"""TV-specific scan and rename planning logic.

for anthology, episode matching, and fallback.

"""

import logging
import re
from typing import Any

from namegnome.core.tv.anthology.tv_anthology_helpers import (
    _extract_show_season_year,
)
from namegnome.core.tv.anthology.tv_anthology_log import (
    _log_anthology_single_segment_fallback,
    _log_anthology_single_segment_skip,
)
from namegnome.core.tv.anthology.tv_anthology_split import (
    _anthology_split_segments,
)
from namegnome.core.tv.fallbacks import (
    _fallback_to_filename_span,
)
from namegnome.core.tv.matching import (
    _find_best_episode_match,
)
from namegnome.core.tv.plan_conflicts import add_plan_item_with_conflict_detection
from namegnome.core.tv.tv_plan_context import (
    AnthologyContext,
    AnthologyPlanItemContext,
    PlanContext,
    PlanItemContext,
    TVRenamePlanBuildContext,
)
from namegnome.core.tv.utils import (
    _strip_preamble,
    sanitize_title_tv,
)
from namegnome.metadata.episode_fetcher import fetch_episode_list
from namegnome.models.core import MediaFile, PlanStatus
from namegnome.models.plan import RenamePlanItem
from namegnome.rules.base import RuleSet, RuleSetConfig

# Import any other dependencies as needed

# --- Constants for magic values (PLR2004) ---
MIN_WORD_LENGTH = 3  # For episode keyword matching
ADJACENT_EPISODE_DIFF = 1  # For checking episode adjacency
TWO_SEGMENT_SPLIT = 2  # For candidate_splits length
FUZZY_MATCH_THRESHOLD = 50  # For best_score threshold

# --- Additional constants for magic values ---
FUZZY_MATCH_STRONG_THRESHOLD = 75  # For strong fuzzy match
CANDIDATE_SPLIT_SEGMENTS = 2  # For candidate_splits length

# --- TV-specific helpers and logic (moved from planner.py) ---


def _extract_show_name(media_file: MediaFile, config: RuleSetConfig) -> str | None:
    """Extract the show name from a MediaFile or RuleSetConfig.

    Tries the media file's title, then the config's show_name, then parsing
    the filename, then the parent folder name.
    """
    show_name = getattr(media_file, "title", None)
    if not show_name:
        show_name = getattr(config, "show_name", None)
    if not show_name:
        # Try to parse show name from filename before falling back to parent directory
        parsed_show, _ = _parse_show_season_from_filename(media_file.path.name)
        if parsed_show:
            show_name = parsed_show
    if not show_name:
        show_name = media_file.path.parent.name
    return show_name


def _extract_season(media_file: MediaFile, config: RuleSetConfig) -> int | None:
    """Extract the season number from a MediaFile or RuleSetConfig.

    Tries the media file's season, then the config's season, then parsing
    the filename.
    """
    season = getattr(media_file, "season", None)
    if not season:
        season = getattr(config, "season", None)
    if not season:
        # Try to parse season from filename
        _, parsed_season = _parse_show_season_from_filename(media_file.path.name)
        if parsed_season:
            season = parsed_season
    return season


def _extract_show_name_and_year(show_name: str) -> tuple[str, int | None]:
    """Extract a trailing year from the show name and return (name, year).

    This function parses the show name for a trailing year and returns the name
    and year as a tuple.
    """
    match = re.match(r"(.+?)[ (._-]*([12][09][0-9]{2})[ )_.-]*$", show_name)
    if match:
        name = match.group(1).strip()
        try:
            year = int(match.group(2))
        except Exception:
            year = None
        return name, year
    return show_name, None


def _extract_year_from_filename(fname: str) -> int | None:
    """Extract a year from the filename if present.

    Returns the year as an int if found, otherwise None.
    """
    match = re.match(r".*([12][09][0-9]{2})", fname)
    if match:
        try:
            return int(match.group(1))
        except Exception:
            return None
    return None


def _parse_show_season_from_filename(fname: str) -> tuple[str | None, int | None]:
    """Parse show name and season from filename using known patterns.

    This function uses regex to extract the show name and season number from a filename.
    Returns a tuple of (show_name, season) or (None, None) if not found.
    """
    match = re.search(
        r"^(?P<show>.+)-S(?P<season>\d{1,2})E(?P<episode>\d{2})",
        fname,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"^(?P<show>.+)[ ._-]+S(?P<season>\d{1,2})E(?P<episode>\d{2})",
            fname,
            re.IGNORECASE,
        )
    if match:
        show_name = match.group("show").rstrip(" .-_")
        season = int(match.group("season"))
        return show_name, season
    return None, None


def _anthology_single_segment_fallback(
    seg: str,
    episode_titles: list[str],
    sanitized_episode_titles: list[str],
    episode_list: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fallback for anthology single-segment matching.

    Attempts to match a segment to a single episode using fuzzy matching.
    Returns matched episodes and titles if a confident match is found.
    """
    norm_seg = sanitize_title_tv(seg)
    norm_titles = [sanitize_title_tv(t) for t in episode_titles]
    found_titles = [t for t in norm_titles if t in norm_seg]
    if len(found_titles) == 1:
        best = None
        best_score = 0.0
        best_ep = None
        from rapidfuzz import fuzz

        for idx, ep_title in enumerate(sanitized_episode_titles):
            score = fuzz.ratio(sanitize_title_tv(seg), ep_title)
            if score > best_score:
                best_score = score
                best = episode_titles[idx]
                best_ep = episode_list[idx]
        if best_score >= FUZZY_MATCH_THRESHOLD:
            matched_episodes = [best_ep] if best_ep is not None else []
            matched_titles = [best] if best is not None else []
            _log_anthology_single_segment_fallback(seg, best, best_score)
            return matched_episodes, matched_titles
    else:
        _log_anthology_single_segment_skip(found_titles)
    return [], []


def _anthology_filename_span_fallback(context: AnthologyPlanItemContext) -> bool:
    """Fallback for anthology filename span matching.

    Wraps the context in a PlanItemContext and delegates to _fallback_to_filename_span.
    Returns True if a fallback match is found.
    """
    plan_item_context = PlanItemContext(
        media_file=context.media_file,
        rule_set=context.rule_set,
        config=context.config,
        ctx=context.ctx,
        unique_episodes=[],
        unique_titles=[],
        season=context.season,
        episode_list=context.episode_list,
        orig_stem=context.orig_stem,
    )
    return _fallback_to_filename_span(plan_item_context)


def contains_multiple_episode_keywords(segment: str, episode_titles: list[str]) -> bool:
    """Return True if the segment contains keywords from more than one episode.

    Title (normalized).

    This function checks if the normalized segment contains keywords from
    multiple episode titles.
    """
    matches = 0
    seg_norm = sanitize_title_tv(segment)
    for title in episode_titles:
        title_norm = sanitize_title_tv(title)
        for word in title_norm.split():
            if len(word) > MIN_WORD_LENGTH and word in seg_norm:
                matches += 1
                break
        if matches > 1:
            return True
    return False


def _create_manual_plan_item(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: "PlanContext",
) -> None:
    """Create a manual plan item when no confident match is found.

    This function creates a RenamePlanItem with manual status and reason, and
    adds it to the plan.
    """
    target_path = rule_set.target_path(
        media_file,
        base_dir=ctx.plan.root_dir,
        config=config,
    ).resolve()
    item = RenamePlanItem(
        source=media_file.path,
        destination=target_path,
        media_file=media_file,
        manual=True,
        manual_reason=(
            "No confident match for filename; missing episode number or title."
        ),
        status=PlanStatus.MANUAL,
    )
    add_plan_item_with_conflict_detection(item, ctx, media_file.path)


def _handle_normal_matching(
    media_file: MediaFile,
    ctx: "TVRenamePlanBuildContext",
    plan_ctx: "PlanContext",
    episode_list: list[dict[str, Any]],
    found_match: bool,
) -> bool:
    """Attempt to match a media file to an episode using fuzzy matching.

    Updates the media file's episode and episode_title if a confident match is found.
    Returns True if a match is found, otherwise False.
    """
    orig_stem = media_file.path.stem
    stripped_stem = _strip_preamble(orig_stem)
    best_match, best_score, best_ep = _find_best_episode_match(
        stripped_stem, episode_list
    )
    if best_match and best_score > FUZZY_MATCH_THRESHOLD and best_ep is not None:
        found_match = True
        media_file.episode = getattr(
            best_ep,
            "episode",
            best_ep.get("episode") if isinstance(best_ep, dict) else None,
        )
        media_file.episode_title = str(
            getattr(
                best_ep,
                "title",
                best_ep.get("title") if isinstance(best_ep, dict) else None,
            )
        )
    return found_match


def _handle_anthology_mode(context: "AnthologyContext") -> bool:
    """Handle anthology mode for TV planning.

    Attempts to fetch episode lists from fallback providers if not present, then
    splits segments.
    Returns True when complete.
    """
    if not context.episode_list or len(context.episode_list) == 0:
        fallback_providers = ["tmdb", "omdb"]
        for provider in fallback_providers:
            logging.debug(
                f"[DEBUG] fetch_episode_list: show='{context.show}', "
                f"season={context.season}, year={context.year}, provider={provider}"
            )
            fallback_episode_list = fetch_episode_list(
                context.show, context.season, year=context.year, provider=str(provider)
            )
            if fallback_episode_list:
                context.episode_list_cache[context.key] = fallback_episode_list
                context.episode_list = fallback_episode_list
                break
    _anthology_split_segments(
        context.media_file,
        context.ctx.rule_set,
        context.ctx.config if context.ctx.config is not None else RuleSetConfig(),
        context.plan_ctx,
        context.episode_list_cache,
    )
    if context.ctx.progress_callback:
        context.ctx.progress_callback(
            getattr(context.media_file, "name", str(context.media_file))
        )
    return True


def _handle_normal_plan_item(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: "PlanContext",
    found_match: bool = False,
) -> None:  # noqa: PLR0913
    """Handle normal (non-anthology) plan item logic for TV."""
    show_name, season, _ = _extract_show_season_year(media_file, config)
    media_file.title = show_name
    media_file.season = season
    # --- PATCH: Set episode and episode_title for non-anthology ---
    # Try to extract episode number and title from filename or metadata
    fname = media_file.path.stem
    import re

    match = re.search(r"S(\d{1,2})E(\d{2,3})", fname, re.IGNORECASE)
    if match:
        media_file.episode = int(match.group(2))
        # Try to extract title after episode pattern
        title_part = fname[match.end() :].strip(" -._")
        if title_part:
            media_file.episode_title = sanitize_title_tv(title_part)
    # TEMP LOG: Print values before path generation
    logging.debug(
        f"[DEBUG][TEMP] Path gen: title='{media_file.title}', "
        f"season='{media_file.season}', "
        f"episode='{getattr(media_file, 'episode', None)}', "
        f"episode_title='{getattr(media_file, 'episode_title', None)}', "
        f"file='{media_file.path}'"
    )

    target_path = rule_set.target_path(
        media_file,
        base_dir=ctx.plan.root_dir,
        config=config,
    ).resolve()
    # Always create a plan item and check for conflicts, regardless of found_match
    item = RenamePlanItem(
        source=media_file.path,
        destination=target_path,
        media_file=media_file,
        manual=not found_match,
        manual_reason=(
            None
            if found_match
            else ("No confident match for filename; missing episode number or title.")
        ),
    )
    add_plan_item_with_conflict_detection(item, ctx, target_path)


# --- Anthology moniker extraction and advanced splitting ---
def _extract_shared_moniker(title: str) -> str | None:
    """Extract a shared moniker (e.g., 'Mighty Pups, Charged Up') from a double-length.

    Episode title.

    Look for a prefix before a colon or before the first story.
    e.g., 'Mighty Pups, Charged Up: Pups Stop a Humdinger Horde' =>
    'Mighty Pups, Charged Up'.
    """
    # Look for a prefix before a colon or before the first story
    # e.g., 'Mighty Pups, Charged Up: Pups Stop a Humdinger Horde' =>
    # 'Mighty Pups, Charged Up'.
    match = re.match(r"^([\w\s,'-]+):", title)
    if match:
        return match.group(1).strip()
    # Try before first 'Pups' or similar
    match = re.match(r"^([\w\s,'-]+)Pups ", title)
    if match:
        return match.group(1).strip()
    return None
