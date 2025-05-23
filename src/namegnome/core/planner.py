# mypy: disable-error-code=unreachable
"""Rename planner for media files.

This module provides functionality to create a plan for renaming and moving media files
based on platform-specific rules and detect potential conflicts.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from namegnome.llm import prompt_orchestrator
from namegnome.models.core import MediaFile, PlanStatus, ScanResult
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.rules.base import RuleSet, RuleSetConfig

if TYPE_CHECKING:
    from namegnome.models.core import ScanResult
    from namegnome.models.plan import RenamePlan
    from namegnome.rules.base import RuleSet


@dataclass
class PlanContext:
    """Context object holding plan and destination tracking for rename planning."""

    plan: RenamePlan
    destinations: dict[Path, RenamePlanItem]
    case_insensitive_destinations: dict[str, RenamePlanItem]


def create_rename_plan(
    scan_result: ScanResult,
    rule_set: RuleSet,
    plan_id: str,
    platform: str,
    *,  # Force keyword arguments for better clarity
    config: Optional[RuleSetConfig] = None,
) -> RenamePlan:
    """Create a rename plan from a scan result.

    Args:
        scan_result: The scan result containing media files to process.
        rule_set: The rule set to use for generating target paths.
        plan_id: Unique identifier for this plan.
        platform: Target platform name (e.g., 'plex', 'jellyfin').
        config: Optional configuration for the rule set.

    Returns:
        A RenamePlan object containing the proposed rename operations.

    Raises:
        ValueError: If the rule set doesn't support any of the media types in the scan.
    """
    # Start with an empty plan
    plan = scan_result.as_plan(plan_id=plan_id, platform=platform)

    # Create default config if none provided
    if config is None:
        config = RuleSetConfig()

    # Track destinations to detect conflicts
    destinations: dict[Path, RenamePlanItem] = {}
    # Track paths on case-insensitive filesystems
    # Reason: On Windows and macOS, file systems are often case-insensitive,
    # so we must detect conflicts like 'Show.mkv' vs 'show.mkv'.
    # See PLANNING.md for cross-platform requirements.
    case_insensitive_destinations: dict[str, RenamePlanItem] = {}

    ctx = PlanContext(plan, destinations, case_insensitive_destinations)

    # Process each media file
    for media_file in scan_result.files:
        # Skip if rule set doesn't support this media type
        if not rule_set.supports_media_type(media_file.media_type):
            continue

        # Anthology/multi-episode detection (triggered by config.anthology)
        if _handle_anthology_split(
            media_file,
            rule_set,
            config,
            ctx,
        ):
            continue

        _handle_normal_plan_item(
            media_file,
            rule_set,
            config,
            ctx,
        )

    return plan


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, obj: object) -> Any:  # noqa: ANN401
        """Convert datetime objects to ISO format strings.

        Args:
            obj: The object to encode.

        Returns:
            A JSON-serializable object.
        """
        if isinstance(obj, datetime):
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
        status=PlanStatus.MANUAL,
        manual=True,
        manual_reason=str(e),
    )
    ctx.plan.items.append(item)


def _anthology_split_segments(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: PlanContext,
) -> None:
    segments = prompt_orchestrator.split_anthology(media_file)
    try:
        threshold = float(os.environ.get("NGN_LLM_THRESHOLD", "0.7"))
    except Exception:
        threshold = 0.7
    for seg in segments:
        seg_media_file = media_file.model_copy()
        seg_media_file.episode = seg.get("episode")
        seg_media_file.title = seg.get("title")
        confidence = seg.get("confidence")
        manual = False
        manual_reason = None
        if confidence is not None:
            try:
                conf_val = float(confidence)
                if conf_val < threshold:
                    manual = True
                    manual_reason = (
                        f"LLM confidence {conf_val:.2f} below threshold {threshold:.2f}"
                    )
            except Exception:
                pass
        target_path = rule_set.target_path(seg_media_file, config=config)
        item = RenamePlanItem(
            source=media_file.path,
            destination=target_path,
            media_file=seg_media_file,
            manual=manual,
            manual_reason=manual_reason,
        )
        ctx.plan.items.append(item)
        ctx.destinations[target_path] = item
        ctx.case_insensitive_destinations[str(target_path).lower()] = item


def _handle_anthology_split(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: PlanContext,
) -> bool:
    """Handle anthology splitting for a media file. Returns True if handled."""
    if media_file.media_type.name.lower() == "tv" and getattr(
        config, "anthology", False
    ):
        try:
            _anthology_split_segments(media_file, rule_set, config, ctx)
        except Exception as e:
            _handle_anthology_split_error(e, media_file, ctx)
        return True
    return False


def _append_failed_plan_item(
    media_file: MediaFile, ctx: PlanContext, error: Exception
) -> None:
    """Append a failed RenamePlanItem to the plan for user review."""
    item = RenamePlanItem(
        source=media_file.path,
        destination=media_file.path,  # Keep original path
        media_file=media_file,
        status=PlanStatus.FAILED,
        reason=str(error),
    )
    ctx.plan.items.append(item)


def _try_generate_plan_item(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: PlanContext,
) -> None:
    """Try to generate and append a plan item, handling ValueError as failed."""
    try:
        # Generate target path using the config object
        target_path = rule_set.target_path(
            media_file,
            config=config,
        )

        # Create plan item
        item = RenamePlanItem(
            source=media_file.path,
            destination=target_path,
            media_file=media_file,
        )

        # Check for conflicts
        if target_path in ctx.destinations:
            # Mark both items as conflicting
            item.status = PlanStatus.CONFLICT
            item.reason = (
                f"Destination already used by {ctx.destinations[target_path].source}"
            )
            ctx.destinations[target_path].status = PlanStatus.CONFLICT
            conflict_src = item.source
            ctx.destinations[
                target_path
            ].reason = f"Destination already used by {conflict_src}"
        elif str(target_path).lower() in ctx.case_insensitive_destinations:
            conflicting_item = ctx.case_insensitive_destinations[
                str(target_path).lower()
            ]
            item.status = PlanStatus.CONFLICT
            item.reason = (
                f"Destination conflicts with {conflicting_item.source} "
                "(case-insensitive filesystem)"
            )
            conflicting_item.status = PlanStatus.CONFLICT
            conflicting_item.reason = (
                f"Destination conflicts with {item.source} "
                "(case-insensitive filesystem)"
            )

        # Add to plan and track destination
        ctx.plan.items.append(item)
        ctx.destinations[target_path] = item
        ctx.case_insensitive_destinations[str(target_path).lower()] = item

    except ValueError as e:
        _append_failed_plan_item(media_file, ctx, e)


def _handle_normal_plan_item(
    media_file: MediaFile,
    rule_set: RuleSet,
    config: RuleSetConfig,
    ctx: PlanContext,
) -> None:  # noqa: PLR0913
    """Handle normal (non-anthology) plan item logic."""
    try:
        # Generate target path using the config object
        target_path = rule_set.target_path(
            media_file,
            config=config,
        )

        # Create plan item
        item = RenamePlanItem(
            source=media_file.path,
            destination=target_path,
            media_file=media_file,
        )

        # Check for conflicts
        if target_path in ctx.destinations:
            # Mark both items as conflicting
            item.status = PlanStatus.CONFLICT
            item.reason = (
                f"Destination already used by {ctx.destinations[target_path].source}"
            )
            ctx.destinations[target_path].status = PlanStatus.CONFLICT
            conflict_src = item.source
            ctx.destinations[
                target_path
            ].reason = f"Destination already used by {conflict_src}"
        elif str(target_path).lower() in ctx.case_insensitive_destinations:
            conflicting_item = ctx.case_insensitive_destinations[
                str(target_path).lower()
            ]
            item.status = PlanStatus.CONFLICT
            item.reason = (
                f"Destination conflicts with {conflicting_item.source} "
                "(case-insensitive filesystem)"
            )
            conflicting_item.status = PlanStatus.CONFLICT
            conflicting_item.reason = (
                f"Destination conflicts with {item.source} "
                "(case-insensitive filesystem)"
            )

        # Add to plan and track destination
        ctx.plan.items.append(item)
        ctx.destinations[target_path] = item
        ctx.case_insensitive_destinations[str(target_path).lower()] = item

    except ValueError as e:
        item = RenamePlanItem(
            source=media_file.path,
            destination=media_file.path,  # Keep original path
            media_file=media_file,
            status=PlanStatus.FAILED,
            reason=str(e),
        )
        ctx.plan.items.append(item)


# TODO: NGN-202 - Add support for user-defined conflict resolution strategies
# (e.g., auto-rename, skip, prompt).
