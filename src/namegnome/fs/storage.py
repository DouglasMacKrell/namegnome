"""Filesystem storage operations for namegnome.

This module provides plan and metadata storage for rename operations,
maintaining backward compatibility with legacy plan formats.
- All new code should use utils.plan_store directly; this module wraps it for
  compatibility with older CLI/tests.
- Handles plan storage, metadata, and listing, with custom YAML serialization for
  Path and Enum types.

Design:
- Custom YAML representers ensure that Path and Enum objects are serialized in a
  human-readable way for metadata files.
- All plan storage is routed through utils.plan_store, but legacy CLI/tests may
  still use this module's API.
- Directory structure and file naming conventions are derived from PLANNING.md
  and TASK.md.
- This module is retained for legacy support; new features and bugfixes should
  target utils.plan_store.

See README.md, PLANNING.md, and TASK.md for rationale and usage examples.
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
    get_latest_plan_id,
    load_plan,
    save_plan,
)
from namegnome.utils.plan_store import (
    list_plans as plan_store_list_plans,
)


# Reason: Custom YAML representers ensure Path and Enum objects are serialized as
# strings for human readability and compatibility.
def _path_representer(dumper: yaml.SafeDumper, data: Path) -> yaml.ScalarNode:
    """Custom YAML representer for Path objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def _enum_representer(dumper: yaml.SafeDumper, data: enum.Enum) -> yaml.ScalarNode:
    """Custom YAML representer for Enum objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data.value))


# Add the representers to the dumper
yaml.SafeDumper.add_representer(Path, _path_representer)
yaml.SafeDumper.add_multi_representer(enum.Enum, _enum_representer)


# Reason: get_namegnome_dir and get_plans_dir maintain legacy directory structure for
# backward compatibility with older CLI/tests.
def get_namegnome_dir() -> Path:
    """Get the .namegnome directory, creating it if it doesn't exist.

    Returns:
        Path to the .namegnome directory.

    Reason:
        Maintains legacy directory structure for backward compatibility with older
        CLI/tests.
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

    Reason:
        Maintains legacy directory structure for backward compatibility with older
        CLI/tests.
    """
    return _ensure_plan_dir()


def store_plan(plan: RenamePlan) -> Path:
    """Store a rename plan as JSON.

    Args:
        plan: The rename plan to store.

    Returns:
        Path to the stored plan file.

    Reason:
        Provides a legacy-compatible API for storing plans; new code should use
        utils.plan_store.save_plan directly.
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
    return get_plans_dir() / f"{plan_id}.json"


def _convert_value_for_yaml(value: object) -> object:
    """Convert a value to be YAML-serializable.

    Args:
        value: The value to convert.

    Returns:
        A YAML-serializable value.

    Reason:
        Ensures compatibility with legacy YAML metadata files and human readability.
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

    Reason:
        Maintains legacy metadata format for backward compatibility; new code should
        use utils.plan_store.
    """
    # Ensure the plan directory exists
    plans_dir = get_plans_dir()

    # Create metadata file path
    metadata_path = plans_dir / f"{plan_id}.meta.yaml"

    # Convert complex types to simple types that can be serialized to YAML
    serializable_args = _convert_value_for_yaml(args)

    # Create metadata dictionary
    metadata = {
        "id": plan_id,
        "args": serializable_args,
        "timestamp": datetime.now().isoformat(),
    }

    # Write metadata to file
    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, default_flow_style=False)

    return metadata_path


def list_plans() -> List[Tuple[str, Any, Path]]:
    """List all available rename plans.

    Returns:
        List of tuples containing (plan_id, creation_date, file_path).

    Reason:
        Provides a legacy-compatible API for listing plans; new code should use
        utils.plan_store.list_plans.
    """
    plans_list = plan_store_list_plans()
    result = []

    for plan_id, timestamp in plans_list:
        # Handle both string timestamps and datetime objects
        plan_path = get_plans_dir() / f"{plan_id}.json"
        result.append((plan_id, timestamp, plan_path))

    # Already sorted by creation date, newest first
    return result


def get_latest_plan() -> Optional[Tuple[str, Path]]:
    """Get the ID and path of the latest plan.

    Returns:
        Tuple containing (plan_id, file_path) or None if no plans exist.

    Reason:
        Provides a legacy-compatible API for retrieving the latest plan; new code
        should use utils.plan_store.get_latest_plan_id.
    """
    plan_id = get_latest_plan_id()
    if not plan_id:
        return None

    plan_path = get_plans_dir() / f"{plan_id}.json"
    return (plan_id, plan_path)


def get_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get a plan by ID.

    Args:
        plan_id: The ID of the plan to get.

    Returns:
        The plan data as a dictionary, or None if not found.

    Reason:
        Provides a legacy-compatible API for retrieving plans; new code should use
        utils.plan_store.load_plan.
    """
    plans_dir = get_plans_dir()

    # Try to load using the new format
    try:
        plan, _ = load_plan(plan_id)
        return plan.model_dump()
    except FileNotFoundError:
        pass

    # Check for the new file format directly
    plan_file = plans_dir / f"{plan_id}.json"
    if plan_file.exists():
        with open(plan_file, "r", encoding="utf-8") as f:
            plan_data: Dict[str, Any] = json.load(f)
            return plan_data

    # Fall back to the old-style timestamp-based plan files
    plan_file = plans_dir / f"plan_{plan_id}.json"
    if plan_file.exists():
        with open(plan_file, "r", encoding="utf-8") as f:
            old_data: Dict[str, Any] = json.load(f)
            return old_data

    # Check for old-style UUID directory structure
    old_plan_dir = plans_dir / plan_id
    if old_plan_dir.exists() and old_plan_dir.is_dir():
        old_plan_file = old_plan_dir / "plan.json"
        if old_plan_file.exists():
            with open(old_plan_file, "r", encoding="utf-8") as f:
                old_plan_data: Dict[str, Any] = json.load(f)
                return old_plan_data

    return None


# TODO: NGN-207 - Remove this wrapper module once all CLI/tests are migrated to use
# utils.plan_store directly.
