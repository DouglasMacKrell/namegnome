"""Rename planner for media files.

This module provides functionality to create a plan for renaming and moving media files
based on platform-specific rules and detect potential conflicts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from namegnome.models.core import PlanStatus, RenamePlan, RenamePlanItem, ScanResult
from namegnome.rules.base import RuleSet

# Logger for this module
logger = logging.getLogger(__name__)


def create_rename_plan(
    scan_result: ScanResult,
    rule_set: RuleSet,
    plan_id: str,
    platform: str,
) -> RenamePlan:
    """Create a rename plan from a scan result.

    Args:
        scan_result: The scan result containing media files to process.
        rule_set: The rule set to use for generating target paths.
        plan_id: Unique identifier for this plan.
        platform: Target platform name (e.g., 'plex', 'jellyfin').

    Returns:
        A RenamePlan object containing the proposed rename operations.

    Raises:
        ValueError: If the rule set doesn't support any of the media types in the scan.
    """
    # Start with an empty plan
    plan = scan_result.as_plan(plan_id=plan_id, platform=platform)

    # Track destinations to detect conflicts
    destinations: dict[Path, RenamePlanItem] = {}

    # Process each media file
    for media_file in scan_result.media_files:
        # Skip if rule set doesn't support this media type
        if not rule_set.supports_media_type(media_file.media_type):
            logger.warning(
                f"Skipping {media_file.path} - media type {media_file.media_type} "
                f"not supported by {rule_set.platform_name} rule set"
            )
            continue

        try:
            # Generate target path
            target_path = rule_set.target_path(media_file)

            # Create plan item
            item = RenamePlanItem(
                source=media_file.path,
                destination=target_path,
                media_file=media_file,
            )

            # Check for conflicts
            if target_path in destinations:
                # Mark both items as conflicting
                item.status = PlanStatus.CONFLICT
                item.reason = f"Destination already used by {destinations[target_path].source}"
                destinations[target_path].status = PlanStatus.CONFLICT
                destinations[target_path].reason = f"Destination already used by {item.source}"
                logger.warning(
                    f"Conflict detected: {item.source} and {destinations[target_path].source} "
                    f"both target {target_path}"
                )

            # Add to plan and track destination
            plan.items.append(item)
            destinations[target_path] = item

        except ValueError as e:
            # Handle errors in path generation
            logger.error(f"Error generating target path for {media_file.path}: {e}")
            item = RenamePlanItem(
                source=media_file.path,
                destination=media_file.path,  # Keep original path
                media_file=media_file,
                status=PlanStatus.FAILED,
                reason=str(e),
            )
            plan.items.append(item)

    return plan


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings.

        Args:
            obj: The object to encode.

        Returns:
            A JSON-serializable object.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def save_plan(plan: RenamePlan, output_dir: Path) -> Path:
    """Save a rename plan to a JSON file.

    Args:
        plan: The rename plan to save.
        output_dir: Directory to save the plan file in.

    Returns:
        Path to the saved plan file.

    Raises:
        OSError: If the output directory cannot be created or the file cannot be written.
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

    logger.info(f"Saved rename plan to {output_file}")
    return output_file
