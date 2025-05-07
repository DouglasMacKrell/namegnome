"""Filesystem storage operations for namegnome.

This module is a wrapper around utils.plan_store to maintain backward compatibility.
All new code should use utils.plan_store directly.
"""

import enum
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from namegnome.models.plan import RenamePlan
from namegnome.models.scan import ScanOptions
from namegnome.utils.plan_store import (
    _ensure_plan_dir,
    save_plan,
)
from namegnome.utils.plan_store import (
    list_plans as _list_plans,
)


def get_namegnome_dir() -> Path:
    """Get the .namegnome directory, creating it if it doesn't exist.

    Returns:
        Path to the .namegnome directory.
    """
    namegnome_dir = Path.home() / ".namegnome"
    namegnome_dir.mkdir(exist_ok=True)

    # Create plans directory for backward compatibility
    plans_dir = namegnome_dir / "plans"
    plans_dir.mkdir(exist_ok=True)

    return namegnome_dir


def get_plans_dir() -> Path:
    """Get the .namegnome/plans directory.

    Returns:
        Path to the plans directory.
    """
    return _ensure_plan_dir()


def store_plan(plan: RenamePlan) -> Path:
    """Store a rename plan as JSON.

    Args:
        plan: The rename plan to store.

    Returns:
        Path to the stored plan file.
    """
    # Create minimal ScanOptions for backward compatibility
    scan_options = ScanOptions(
        root=Path(plan.root_dir),
        media_types=[],  # This will be populated from plan if available
        platform=plan.platform,
    )

    # Try to extract media types from the plan
    if hasattr(plan, "media_types") and plan.media_types:
        scan_options.media_types = plan.media_types

    # Save the plan
    plan_id = save_plan(plan, scan_options)

    # Return the path for backward compatibility
    return get_plans_dir() / plan_id / "plan.json"


def _convert_value_for_yaml(value: object) -> object:
    """Convert a value to be YAML-serializable.

    Args:
        value: The value to convert.

    Returns:
        A YAML-serializable value.
    """
    if isinstance(value, Path):
        return str(value)
    elif isinstance(value, enum.Enum):
        return value.value
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: _convert_value_for_yaml(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_convert_value_for_yaml(item) for item in value]
    else:
        return value


def store_run_metadata(plan_id: str, args: Dict[str, Any]) -> Path:
    """Store metadata about the run that created a plan.

    Args:
        plan_id: ID of the plan.
        args: Command line arguments used for the run.

    Returns:
        Path to the metadata file.
    """
    # Ensure the plan directory exists
    plan_dir = get_plans_dir() / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata file path
    metadata_path = plan_dir / "run.yaml"

    # Convert complex types to simple types that can be serialized to YAML
    serializable_args = _convert_value_for_yaml(args)

    # Create metadata dictionary
    metadata = {
        "plan_id": plan_id,
        "args": serializable_args,
        "timestamp": datetime.now().isoformat(),
    }

    # Write metadata to file
    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, default_flow_style=False)

    return metadata_path


def list_plans() -> List[Tuple[str, Any, Path]]:
    """List all available rename plans.

    Returns:
        List of tuples containing (plan_id, creation_date, file_path).
    """
    plans_dict = _list_plans()
    result = []

    for plan_id, timestamp in plans_dict.items():
        plan_path = get_plans_dir() / plan_id / "plan.json"
        result.append((plan_id, timestamp, plan_path))

    # Sort by creation date, newest first
    return sorted(result, key=lambda x: x[1], reverse=True)


def get_latest_plan() -> Optional[Tuple[str, Path]]:
    """Get the ID and path of the latest plan.

    Returns:
        Tuple containing (plan_id, file_path) or None if no plans exist.
    """
    plans = list_plans()
    if not plans:
        return None

    # Return the most recent plan
    return (plans[0][0], plans[0][2])


def get_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get a plan by ID.

    Args:
        plan_id: The ID of the plan to get.

    Returns:
        The plan data as a dictionary, or None if not found.
    """
    plans_dir = get_plans_dir()

    # Check for a UUID directory first
    plan_dir = plans_dir / plan_id
    if plan_dir.exists() and plan_dir.is_dir():
        plan_file = plan_dir / "plan.json"
        if plan_file.exists():
            with open(plan_file, "r", encoding="utf-8") as f:
                return json.load(f)

    # Fall back to the old-style timestamp-based plan files
    plan_file = plans_dir / f"plan_{plan_id}.json"
    if plan_file.exists():
        with open(plan_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return None
