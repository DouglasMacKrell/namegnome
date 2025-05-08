"""Utilities for storing and retrieving rename plans.

This module provides functions for saving, loading, and managing rename plans,
including creating symlinks to the latest plan and storing checksums.
"""

import json
import logging
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel

from namegnome.models.plan import RenamePlan
from namegnome.models.scan import ScanOptions

# Logger for this module
logger = logging.getLogger(__name__)


class RunMetadata(BaseModel):
    """Metadata about a rename plan run."""

    id: str
    timestamp: datetime
    args: Dict[str, Any]
    git_hash: Optional[str] = None


def _ensure_plan_dir() -> Path:
    """Ensure the plan directory exists and return its path."""
    home = Path.home()
    plan_dir = home / ".namegnome" / "plans"
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


def _get_git_hash() -> Optional[str]:
    """Get the current git hash if available."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _update_latest_link(plan_dir: Path, plan_id: str, plan_file: Path) -> None:
    """Update the latest.json symlink or copy to point to the new plan.

    Args:
        plan_dir: Directory where plans are stored
        plan_id: ID of the plan to link to
        plan_file: Path to the plan file
    """
    latest_link = plan_dir / "latest.json"

    # Remove the existing link or file if it exists
    if latest_link.exists() or os.path.islink(str(latest_link)):
        try:
            if os.path.islink(str(latest_link)):
                os.unlink(str(latest_link))
            else:
                latest_link.unlink(missing_ok=True)
        except (OSError, PermissionError) as e:
            # Log the error but continue - not critical
            logger.warning(f"Warning: Could not remove old latest.json reference: {e}")

    # Determine if we're in a CI environment
    is_ci = os.environ.get("CI", "false").lower() in ("true", "1", "yes")

    # Check if we can use symlinks (non-Windows or Windows with symlink capability)
    can_use_symlinks = (
        sys.platform != "win32" or  # Not Windows
        not is_ci  # Not in CI environment on Windows
    )

    if can_use_symlinks:
        try:
            # Use relative path for symlink to work across different mounts
            relative_path = plan_id + "/plan.json"
            os.symlink(relative_path, str(latest_link))
            return
        except (OSError, PermissionError) as e:
            # Log the error but fall back to copying
            logger.warning(
                f"Warning: Could not create symlink, falling back to copy: {e}"
            )

    # Fall back to copying the file
    try:
        shutil.copy2(plan_file, latest_link)
    except (OSError, PermissionError) as e:
        # Log the error but continue - not critical
        logger.warning(f"Warning: Could not create latest.json reference: {e}")


def save_plan(plan: RenamePlan, scan_options: ScanOptions, verify: bool = False) -> str:
    """Save a rename plan to disk and return the ID.

    Args:
        plan: The rename plan to save
        scan_options: The options used to generate the plan
        verify: Whether checksums should be stored for verification

    Returns:
        The ID of the saved plan
    """
    # Generate a unique ID for the plan
    plan_id = str(uuid.uuid4())
    plan_dir = _ensure_plan_dir()

    # Create a directory for this plan
    plan_path = plan_dir / plan_id
    plan_path.mkdir(exist_ok=True)

    # Save the plan as JSON
    plan_file = plan_path / "plan.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))

    # Convert ScanOptions to a serializable dict by converting paths to strings
    args_dict = scan_options.model_dump()
    args_dict["root"] = str(args_dict["root"])

    # Convert other complex types
    if "media_types" in args_dict:
        args_dict["media_types"] = [str(mt) for mt in args_dict["media_types"]]
    if "target_extensions" in args_dict:
        args_dict["target_extensions"] = list(args_dict["target_extensions"])

    # Create run metadata
    metadata = RunMetadata(
        id=plan_id,
        timestamp=datetime.now(),
        args=args_dict,
        git_hash=_get_git_hash(),
    )

    # Save run metadata
    metadata_file = plan_path / "run.yaml"
    with open(metadata_file, "w", encoding="utf-8") as f:
        yaml.dump(metadata.model_dump(), f)

    # If verify is enabled, store checksums for each file
    if verify:
        from namegnome.utils.hash import sha256sum

        checksums = {}
        for item in plan.items:
            try:
                checksums[str(item.source)] = sha256sum(item.source)
            except (FileNotFoundError, PermissionError):
                # Skip files that can't be accessed
                pass

        # Save checksums
        checksum_file = plan_path / "checksums.json"
        with open(checksum_file, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)

    # Create or update latest plan reference
    _update_latest_link(plan_dir, plan_id, plan_file)

    return plan_id


def load_plan(plan_id: Optional[str] = None) -> RenamePlan:
    """Load a rename plan from disk.

    Args:
        plan_id: The ID of the plan to load, or None to load the latest

    Returns:
        The loaded rename plan

    Raises:
        FileNotFoundError: If the plan does not exist
    """
    plan_dir = _ensure_plan_dir()

    if plan_id is None:
        # Load the latest plan
        plan_file = plan_dir / "latest.json"
    else:
        # Load a specific plan
        plan_file = plan_dir / plan_id / "plan.json"

    if not plan_file.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_file}")

    with open(plan_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    return RenamePlan.model_validate(plan_data)


def get_plan_metadata(plan_id: str) -> RunMetadata:
    """Get metadata for a specific plan.

    Args:
        plan_id: The ID of the plan

    Returns:
        The plan metadata

    Raises:
        FileNotFoundError: If the metadata does not exist
    """
    plan_dir = _ensure_plan_dir()
    metadata_file = plan_dir / plan_id / "run.yaml"

    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    return RunMetadata.model_validate(metadata)


def list_plans() -> Dict[str, datetime]:
    """List all available plans with their timestamps.

    Returns:
        A dictionary mapping plan IDs to their timestamps
    """
    plan_dir = _ensure_plan_dir()
    plans = {}

    for path in plan_dir.iterdir():
        if path.is_dir():
            metadata_file = path / "run.yaml"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = yaml.safe_load(f)

                    # Handle timestamp which might be a string or a datetime object
                    timestamp = metadata["timestamp"]
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp)
                    elif not isinstance(timestamp, datetime):
                        # If it's neither string nor datetime, skip this plan
                        continue

                    plans[path.name] = timestamp
                except (KeyError, ValueError, yaml.YAMLError):
                    # Skip invalid metadata files
                    pass

    return plans
