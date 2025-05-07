"""Filesystem storage operations for namegnome."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TypedDict, cast

from namegnome.models.core import RenamePlan
from namegnome.utils.json import DateTimeEncoder


class PlanDict(TypedDict):
    """Type definition for a plan dictionary."""

    id: str
    created_at: str
    root_dir: str
    platform: str
    items: list[dict[str, Any]]
    media_types: list[str]
    metadata_providers: list[str]
    llm_model: Optional[str]


def get_namegnome_dir() -> Path:
    """Get the .namegnome directory, creating it if it doesn't exist.

    Returns:
        Path to the .namegnome directory.
    """
    home_dir = Path.home()
    namegnome_dir = home_dir / ".namegnome"
    namegnome_dir.mkdir(exist_ok=True)

    # Create plans directory if it doesn't exist
    plans_dir = namegnome_dir / "plans"
    plans_dir.mkdir(exist_ok=True)

    return namegnome_dir


def get_plans_dir() -> Path:
    """Get the .namegnome/plans directory.

    Returns:
        Path to the plans directory.
    """
    return get_namegnome_dir() / "plans"


def store_plan(plan: RenamePlan) -> Path:
    """Store a rename plan as JSON.

    Args:
        plan: The rename plan to store.

    Returns:
        Path to the stored plan file.
    """
    plans_dir = get_plans_dir()
    plan_file = plans_dir / f"{plan.id}.json"

    # Write plan to file
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, cls=DateTimeEncoder, indent=2)

    # Create a symlink to the latest plan
    latest_path = get_namegnome_dir() / "latest.json"

    # Remove existing symlink if it exists
    if latest_path.exists():
        latest_path.unlink()

    # Create symlink to the latest plan
    try:
        os.symlink(plan_file, latest_path)
    except (OSError, AttributeError):
        # Symlinks might not be supported on all platforms
        # Just copy the file instead
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(), f, cls=DateTimeEncoder, indent=2)

    return plan_file


def store_run_metadata(plan_id: str, args: dict[str, Any]) -> Path:
    """Store metadata about the run that created a plan.

    Args:
        plan_id: ID of the plan.
        args: Command line arguments used for the run.

    Returns:
        Path to the metadata file.
    """
    plans_dir = get_plans_dir()
    metadata_file = plans_dir / f"{plan_id}_meta.json"

    metadata = {
        "plan_id": plan_id,
        "args": args,
        "timestamp": datetime.now().isoformat(),
    }

    # Try to get git hash if available
    try:
        import subprocess
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        ).strip()
        metadata["git_hash"] = git_hash
    except (subprocess.SubprocessError, FileNotFoundError):
        # Git not available or not a git repository
        pass

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata_file


def list_plans() -> list[tuple[str, datetime, Path]]:
    """List all available rename plans.

    Returns:
        List of tuples containing (plan_id, creation_date, file_path).
    """
    plans_dir = get_plans_dir()
    plans = []

    for plan_file in plans_dir.glob("*.json"):
        # Skip metadata files
        if "_meta.json" in plan_file.name:
            continue

        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            plan_id = data.get("id", "unknown")
            created_at_str = data.get("created_at", None)

            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except ValueError:
                    created_at = datetime.now()
            else:
                # Fallback to file modification time
                created_at = datetime.fromtimestamp(plan_file.stat().st_mtime)

            plans.append((plan_id, created_at, plan_file))

        except (json.JSONDecodeError, KeyError):
            # Skip invalid files
            continue

    # Sort by creation date, newest first
    return sorted(plans, key=lambda x: x[1], reverse=True)


def get_latest_plan() -> tuple[str, Path] | None:
    """Get the ID and path of the latest plan.

    Returns:
        Tuple containing (plan_id, file_path) or None if no plans exist.
    """
    latest_path = get_namegnome_dir() / "latest.json"

    if not latest_path.exists():
        plans = list_plans()
        if not plans:
            return None
        return (plans[0][0], plans[0][2])

    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("id", "unknown"), latest_path)
    except (json.JSONDecodeError, KeyError):
        return None


def get_plan(plan_id: str) -> Optional[PlanDict]:
    """Get a plan by ID.

    Args:
        plan_id: ID of the plan to retrieve.

    Returns:
        Plan data as a dictionary, or None if not found.
    """
    plans_dir = get_plans_dir()
    plan_file = plans_dir / f"{plan_id}.json"

    if not plan_file.exists():
        return None

    try:
        with open(plan_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Cast the loaded JSON to our TypedDict
            return cast(PlanDict, data)
    except json.JSONDecodeError:
        return None
