# mypy: disable-error-code=unreachable
# TODO(NGN-XXX): Remove unreachable code and refactor as needed to resolve mypy errors.

# --- REMOVE UNREACHABLE CODE ---
# This file contains unreachable code after return/raise statements. Begin by searching for such code and removing or refactoring as needed.

"""Rename planner for media files.

This module provides functionality to create a plan for renaming and moving media files
based on platform-specific rules and detect potential conflicts.
"""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional
import sys

from namegnome.cli import console
from namegnome.core.episode_parser import _extract_show_season_year
from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext
from namegnome.metadata.episode_fetcher import fetch_episode_list
from namegnome.models.core import MediaFile, PlanStatus, ScanResult
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.rules.base import RuleSet, RuleSetConfig

if TYPE_CHECKING:
    from namegnome.models.core import ScanResult
    from namegnome.models.plan import RenamePlan
    from namegnome.rules.base import RuleSet

# Confidence thresholds as per SCAN_RULES.md
LLM_CONFIDENCE_AUTO_THRESHOLD = 0.75
LLM_CONFIDENCE_MANUAL_THRESHOLD = 0.40

MIN_WORD_LENGTH = 3  # For episode keyword matching


def route_confidence_to_status(confidence: float) -> PlanStatus:
    """Route LLM confidence scores to appropriate plan item status.

    Implements confidence thresholds from SCAN_RULES.md:
    - ≥0.75 → auto (PlanStatus.PENDING)
    - 0.40-0.74 → manual (PlanStatus.MANUAL)
    - <0.40 → unsupported (PlanStatus.FAILED)

    Args:
        confidence: Confidence score between 0.0 and 1.0

    Returns:
        Appropriate PlanStatus for the confidence level
    """
    if confidence >= LLM_CONFIDENCE_AUTO_THRESHOLD:
        return PlanStatus.PENDING  # Auto-processed
    elif confidence >= LLM_CONFIDENCE_MANUAL_THRESHOLD:
        return PlanStatus.MANUAL  # Manual review required
    else:
        return PlanStatus.FAILED  # Unsupported/low confidence


# Use shared TVPlanContext for consistency across modules (imported as alias)
from namegnome.core.tv.tv_plan_context import TVPlanContext as PlanContext  # noqa: E402


@dataclass
class RenamePlanBuildContext:
    """Context for building a rename plan, grouping all required arguments."""

    scan_result: ScanResult
    rule_set: RuleSet
    plan_id: str
    platform: str
    config: Optional[RuleSetConfig] = None
    progress_callback: Optional[Callable[[str], None]] = None


def create_rename_plan(  # noqa: C901, PLR0912
    ctx: RenamePlanBuildContext,
    debug: bool = False,
    episode_list_cache: Optional[
        dict[tuple[str, int | None, int | None], list[Any]]
    ] = None,
) -> RenamePlan:
    """Create a rename plan from a scan result.

    This function now delegates all TV file handling to tv_planner.py, ensuring TV
    logic is fully isolated.
    Movie and Music logic will be isolated in future sprints (see TODOs below).

    Args:
        ctx: RenamePlanBuildContext containing all required arguments.
        debug: Whether to enable debug logging (passed from CLI).
        episode_list_cache: Optional dict for test injection of episode lists.

    Returns:
        A RenamePlan object representing the planned renames.

    Raises:
        ValueError: If the rule set doesn't support any of the media types in the scan.
    """
    scan_result = ctx.scan_result
    rule_set = ctx.rule_set
    plan_id = ctx.plan_id
    platform = ctx.platform
    # Only process supported types
    supported_files = [
        f for f in scan_result.files if rule_set.supports_media_type(f.media_type)
    ]
    unsupported_files = [
        f for f in scan_result.files if not rule_set.supports_media_type(f.media_type)
    ]
    if not supported_files and unsupported_files:
        # All files are unsupported: create FAILED plan items for each
        plan = RenamePlan(
            id=plan_id,
            items=[],
            platform=platform,
            root_dir=scan_result.root_dir,
        )
        for f in unsupported_files:
            plan.items.append(
                RenamePlanItem(
                    source=f.path,
                    destination=f.path,
                    media_file=f,
                    status=PlanStatus.FAILED,
                    reason=(
                        f"Media type {f.media_type} is not supported by "
                        f"{rule_set.__class__.__name__}"
                    ),
                )
            )
        _mark_duplicate_destination_conflicts(plan)
        return plan
    config = ctx.config
    progress_callback = ctx.progress_callback
    # TV delegation: if any TV files, always delegate to create_tv_rename_plan
    from namegnome.models.core import MediaType as _MT

    tv_files = [f for f in scan_result.files if f.media_type == _MT.TV]
    if tv_files:
        # Build a new ScanResult with only TV files
        from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
        from namegnome.models.core import ScanResult

        tv_scan_result = ScanResult(
            files=tv_files,
            root_dir=scan_result.root_dir,
            media_types=[f.media_type for f in tv_files],
            platform=scan_result.platform,
            total_files=len(tv_files),
            skipped_files=scan_result.skipped_files,
            by_media_type=scan_result.by_media_type,
            scan_duration_seconds=scan_result.scan_duration_seconds,
        )
        plan = create_tv_rename_plan(
            TVRenamePlanBuildContext(
                scan_result=tv_scan_result,
                rule_set=rule_set,
                plan_id=plan_id,
                platform=platform,
                config=config,
                progress_callback=progress_callback,
            ),
            episode_list_cache=episode_list_cache,
        )
        # Add FAILED plan items for unsupported files
        for media_file in unsupported_files:
            item = RenamePlanItem(
                source=media_file.path,
                destination=media_file.path,
                media_file=media_file,
                status=PlanStatus.FAILED,
                reason=(
                    f"Media type {media_file.media_type} is not supported by "
                    "Plex rule set"
                ),
            )
            plan.items.append(item)
        _mark_duplicate_destination_conflicts(plan)
        return plan
    files = scan_result.files
    episode_cache: dict[tuple[str, int | None, int | None], list[Any]] = {}
    for media_file in files:
        if media_file.media_type == "tv":
            show, season, year = _extract_show_season_year(
                media_file,
                config or RuleSetConfig(),
            )
            media_file.season = (
                season  # Ensure season is set for correct folder structure
            )
            key = ((show or ""), season, year)
            if key not in episode_cache:
                try:
                    episode_cache[key] = fetch_episode_list(
                        show or "", season, year=year
                    )
                except Exception:
                    episode_cache[key] = []

    plan = RenamePlan(
        id=plan_id,
        items=[],
        platform=platform,
        root_dir=scan_result.root_dir,
    )
    plan_ctx = PlanContext(plan=plan, destinations={}, case_insensitive_destinations={})
    for media_file in files:
        if not rule_set.supports_media_type(media_file.media_type):
            if progress_callback:
                progress_callback(getattr(media_file, "name", str(media_file)))
            continue
        # TODO: Isolate Movie logic into movie_planner.py (Sprint 8.3.2)
        # TODO: Isolate Music logic into music_planner.py (Sprint 8.3.3)
        # Defensive: ensure config is RuleSetConfig
        config_for_call = config or RuleSetConfig()
        _handle_normal_plan_item(media_file, rule_set, config_for_call, plan_ctx)
        if progress_callback:
            progress_callback(getattr(media_file, "name", str(media_file)))
    # At the end of planning, log summary
    from namegnome.cli.console import console

    console.print(
        f"Total planned items: {len(plan_ctx.plan.items)}, unique destinations: "
        f"{len(plan_ctx.destinations)}"
    )

    # ------------------------------------------------------------------
    # Global duplicate-destination safeguard (platform-agnostic)
    # ------------------------------------------------------------------

    _mark_duplicate_destination_conflicts(plan)

    return plan


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects."""

    def default(self, obj: object) -> Any:  # noqa: ANN401
        """Convert datetime and date objects to ISO format strings.

        Args:
            obj: The object to encode.

        Returns:
            A JSON-serializable object.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        # Let the base class default method handle it or raise TypeError
        return super().default(obj)


def save_plan(plan: RenamePlan, output_dir: Path) -> Path:
    """Save a rename plan to a JSON file.

    Args:
        plan: The rename plan to save.
        output_dir: Directory to save the plan file in.

    Returns:
        Path to the saved plan file.

    Raises:
        OSError: If the output directory cannot be created or the file cannot be
            written.
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    output_file = output_dir / f"plan_{plan.id}.json"

    # Convert plan to JSON
    plan_dict = plan.model_dump()
    # Convert Path objects to strings for JSON serialization
    plan_dict["root_dir"] = str(plan_dict["root_dir"])
    for item in plan_dict["items"]:
        item["source"] = str(item["source"])
        item["destination"] = str(item["destination"])
        item["media_file"]["path"] = str(item["media_file"]["path"])

    # Write to file using custom encoder for datetime objects
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(plan_dict, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    return output_file


def _handle_anthology_split_error(
    e: Exception,
    media_file: MediaFile,
    ctx: PlanContext,
) -> None:
    item = RenamePlanItem(
        source=media_file.path,
        destination=media_file.path,
        media_file=media_file,
        status=PlanStatus.FAILED,
        manual=True,
        manual_reason=str(e),
    )
    ctx.plan.items.append(item)
    ctx.destinations[media_file.path] = item


def _extract_unique_verbs_phrases(title: str) -> set[str]:
    """Extract unique verbs/phrases from an episode title for matching."""
    # Simple heuristic: split on spaces, remove stopwords, keep verbs/keywords
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "of",
        "in",
        "on",
        "to",
        "with",
        "for",
        "at",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "as",
        "it",
        "that",
        "this",
        "but",
        "or",
        "so",
        "if",
        "then",
        "than",
        "too",
        "very",
        "just",
        "not",
        "no",
        "yes",
        "do",
        "does",
        "did",
        "has",
        "have",
        "had",
        "can",
        "could",
        "will",
        "would",
        "should",
        "may",
        "might",
        "must",
    }
    words = re.findall(r"\w+", title.lower())
    return set(w for w in words if w not in stopwords and len(w) > MIN_WORD_LENGTH)


def _normalize_title(title: str) -> str:
    """Normalize a title for comparison: lowercase, strip punctuation and spaces."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def normalize_episode_list(raw_list: list[Any]) -> list[dict[str, Any]]:
    """Return a clean ``list[dict]`` from *raw_list*.

    Accepts provider objects, :class:`~namegnome.metadata.models.TVEpisode`
    instances, plain ``dict`` rows, or lightweight attribute-bags from unit
    tests.  The function now enforces **strict validity**:

    * ``season`` and ``episode`` are coerced to ``int`` after stripping leading
      zeros (``"05" -> 5``).
    * Rows with non-numeric values, negatives, or zeros (e.g. *S00E00* /
      specials) are skipped *entirely*.
    * Title strings are preserved verbatim (caller decides further sanitising).

    This stricter filtering guarantees that downstream anthology logic never
    receives sentinel *0* values or unparseable strings, eliminating a raft of
    edge-case branches.
    """
    normalized = []
    for ep in raw_list or []:
        # Support both object and dict
        season = (
            getattr(ep, "season_number", None)
            or getattr(ep, "season", None)
            or ep.get("season_number")
            or ep.get("season")
        )
        episode = (
            getattr(ep, "episode_number", None)
            or getattr(ep, "episode", None)
            or ep.get("episode_number")
            or ep.get("episode")
        )
        title = getattr(ep, "title", None) or ep.get("title")

        # Coerce zero-padded strings ("05" -> 5) and skip invalid rows
        def _coerce(value: object) -> int | None:
            try:
                # Strip leading zeros then int; fall back to 0 if empty
                if isinstance(value, str):
                    value = value.lstrip("0") or "0"
                return int(value)
            except Exception:  # pragma: no cover – non-numeric string
                return None

        season_i = _coerce(season)
        episode_i = _coerce(episode)
        if season_i is None or episode_i is None:
            continue  # non-numeric
        if season_i <= 0 or episode_i <= 0:
            continue  # skip S00E00, negatives, zeros

        title = str(title).strip()

        normalized.append({"season": season_i, "episode": episode_i, "title": title})
    return normalized


def _handle_normal_plan_item(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: PlanContext,
) -> None:  # noqa: PLR0913
    """Handle normal (non-anthology) plan item logic."""
    try:
        # Debug: Log metadata before planning
        console.print(f"[normal] Planning: {media_file.path}")
        console.print(
            f"[normal] MediaFile.title: '{getattr(media_file, 'title', None)}', "
            f"season: '{getattr(media_file, 'season', None)}', episode: "
            f"'{getattr(media_file, 'episode', None)}', episode_title: "
            f"'{getattr(media_file, 'episode_title', None)}'"
        )
        target_path = rule_set.target_path(
            media_file,
            base_dir=ctx.plan.root_dir,
            config=config,
        ).resolve()  # Normalize path

        # Debug: Log planned destination
        console.print(f"[normal] Planned destination: {target_path}")

        item = RenamePlanItem(
            source=media_file.path,
            destination=target_path,
            media_file=media_file,
        )

        # Use unified conflict detection
        add_plan_item_with_conflict_detection(item, ctx, target_path)

        # Log planned move and tracking
        console.print(f"Planned: {item.source} -> {item.destination}")
        console.print(
            f"Tracking destination: {item.destination} (source: {item.source})"
        )

    except ValueError as e:
        item = RenamePlanItem(
            source=media_file.path,
            destination=media_file.path,  # Keep original path
            media_file=media_file,
            status=PlanStatus.FAILED,
            reason=str(e),
        )
        ctx.plan.items.append(item)
        ctx.destinations[media_file.path] = item
        ctx.case_insensitive_destinations[str(media_file.path).lower()] = item


# TODO: NGN-202 - Add support for user-defined conflict resolution strategies
# (e.g., auto-rename, skip, prompt).

# --- Helper: unified conflict detection ------------------------------------


def add_plan_item_with_conflict_detection(
    item: RenamePlanItem,
    ctx: "PlanContext",
    target_path: Path,
) -> None:
    """Add *item* to *ctx.plan* while checking for destination conflicts.

    A conflict is detected when another planned item already targets the same
    *target_path* (case-insensitive).  In that case, both the existing item
    and the new one are marked as `CONFLICT`.
    """

    key = target_path  # Store absolute path for reference tracking

    # Determine the path relative to the scan root directory when possible – this
    # neutralises differences between 8.3 short paths and their long versions on
    # Windows while still producing deterministic keys on POSIX.  Falling back
    # to the absolute path if *target_path* sits outside the root directory.
    root_dir = getattr(ctx.plan, "root_dir", None)
    try:
        relative_path = target_path.relative_to(root_dir) if root_dir else target_path
    except Exception:  # pragma: no cover – different drive or unrelated path
        relative_path = target_path

    if sys.platform.startswith("win"):
        key_norm = relative_path.as_posix().lower()
    else:
        key_norm = str(relative_path)

    if key_norm in ctx.case_insensitive_destinations:
        # Mark conflict on the new item
        item.status = PlanStatus.CONFLICT
        # Mark conflict on the existing item for visibility
        existing = ctx.case_insensitive_destinations.get(key_norm)
        if existing:
            existing.status = PlanStatus.CONFLICT
    # Track destinations
    ctx.plan.items.append(item)
    ctx.destinations[key] = item
    ctx.case_insensitive_destinations[key_norm] = item


# ---------------------------------------------------------------------------
# Helper: mark duplicate destination conflicts (shared across planners)
# ---------------------------------------------------------------------------


def _mark_duplicate_destination_conflicts(plan: RenamePlan) -> None:  # noqa: D401
    """Ensure any items sharing the same destination are flagged as conflicts.

    Runs a deterministic, case-insensitive check over *plan.items* so that
    duplicate destinations never slip through—regardless of which sub-planner
    produced the items or of OS-specific path quirks (8.3 short paths, drive-
    letter casing, etc.).
    """

    seen: dict[str, RenamePlanItem] = {}
    for item in plan.items:
        try:
            rel = item.destination.relative_to(plan.root_dir)
        except Exception:
            rel = item.destination

        key_ci = rel.as_posix().lower()
        alt_key_ci = item.destination.as_posix().lower()
        for k in (key_ci, alt_key_ci):
            if k in seen:
                item.status = PlanStatus.CONFLICT
                if seen[k].status != PlanStatus.CONFLICT:
                    seen[k].status = PlanStatus.CONFLICT
            else:
                seen[k] = item
