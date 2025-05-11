"""Utilities for storing and retrieving rename plans.

This module provides functions for saving, loading, and managing rename plans,
including creating symlinks to the latest plan and storing checksums.
"""

import json
import logging
import os
import platform
import shutil
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import yaml
from pydantic import BaseModel

from namegnome.models.core import MediaType
from namegnome.models.plan import RenamePlan
from namegnome.models.scan import ScanOptions

# Logger for this module
logger = logging.getLogger(__name__)

# Constants
MAX_FILENAME_CHECK_ATTEMPTS = 8
WINDOWS_OS = "Windows"
MIN_UUID_LENGTH = 8  # Minimum length to consider a string a UUID


# Register a custom representer for Path objects
def path_representer(dumper: yaml.SafeDumper, data: Path) -> yaml.ScalarNode:
    """Custom YAML representer for Path objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


# Register a custom representer for Enum objects
def enum_representer(dumper: yaml.SafeDumper, data: Enum) -> yaml.ScalarNode:
    """Custom YAML representer for Enum objects."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data.value))


# Add representers to the SafeDumper
yaml.SafeDumper.add_representer(Path, path_representer)
yaml.SafeDumper.add_representer(MediaType, enum_representer)
yaml.SafeDumper.add_multi_representer(Enum, enum_representer)


class RunMetadata(BaseModel):
    """Metadata about a rename plan run."""

    id: str
    timestamp: datetime
    args: Dict[str, Any]
    git_hash: Optional[str] = None

    def model_dump_for_yaml(self) -> Dict[str, Any]:
        """Convert to a YAML-serializable dictionary.

        This converts Path objects and Enums to strings for proper YAML serialization.

        Returns:
            Dict with all values converted to YAML-compatible types.
        """
        data = self.model_dump()

        # Use a recursive function to convert Path objects to strings
        def convert_paths(obj: object) -> object:
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, Enum):
                return str(obj.value)
            else:
                return obj

        # Cast to the expected return type
        return cast(Dict[str, Any], convert_paths(data))


def _ensure_plan_dir() -> Path:
    """Ensure the plans directory exists and return its path.

    Returns:
        Path: The plans directory path.
    """
    # Use a proper cross-platform way to get the user's home directory
    # In CI environments HOME may not be set on Windows
    home_dir = os.environ.get("HOME")
    is_windows_ci = platform.system() == WINDOWS_OS and os.environ.get("CI") == "true"

    if not home_dir or is_windows_ci:
        # On Windows, use USERPROFILE as fallback
        home_dir = os.environ.get("USERPROFILE", str(Path.home()))

    # Convert to Path object for proper handling
    home_path = Path(home_dir)

    # Create .namegnome/plans directory
    plans_dir = home_path / ".namegnome" / "plans"

    # Ensure directory exists
    if not plans_dir.exists():
        plans_dir.parent.mkdir(exist_ok=True)
        plans_dir.mkdir(exist_ok=True)
        logger.info(f"Created plans directory at {plans_dir}")

    return plans_dir


def _get_git_hash() -> Optional[str]:
    """Get the current git hash, if in a git repository.

    Returns:
        Optional[str]: The git hash, or None if not in a git repository.
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def save_plan(
    plan: RenamePlan,
    scan_options: ScanOptions,
    extra_args: Optional[Dict[str, Any]] = None,
) -> str:
    """Save a rename plan to disk.

    Args:
        plan: The rename plan to save.
        scan_options: The scan options used to generate the plan.
        extra_args: Extra arguments to store with the plan.

    Returns:
        str: The ID of the saved plan.
    """
    plans_dir = _ensure_plan_dir()

    run_id = str(uuid.uuid4())
    timestamp = datetime.now()

    # Create metadata
    args = {"scan_options": scan_options.model_dump()}
    if extra_args:
        args.update(extra_args)

    metadata = RunMetadata(
        id=run_id,
        timestamp=timestamp,
        args=args,
        git_hash=_get_git_hash(),
    )

    # Save plan with timestamp and id
    filename = f"{run_id}.json"
    plan_path = plans_dir / filename

    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))

    # Save metadata using the YAML-serializable method
    meta_path = plans_dir / f"{run_id}.meta.yaml"
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata.model_dump_for_yaml(), f)

    # Create or update the latest symlink or file
    latest_link = plans_dir / "latest.json"
    try:
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        # Try to create a symlink
        os.symlink(str(plan_path), str(latest_link))
    except (OSError, NotImplementedError):
        # Fallback: copy the file instead
        shutil.copyfile(str(plan_path), str(latest_link))

    return run_id


def load_plan(plan_id: str) -> Tuple[RenamePlan, RunMetadata]:
    """Load a rename plan and its metadata from disk.

    Args:
        plan_id: The ID of the plan to load.

    Returns:
        tuple[RenamePlan, RunMetadata]: The loaded plan and its metadata.

    Raises:
        FileNotFoundError: If the plan or metadata file does not exist.
    """
    plans_dir = _ensure_plan_dir()
    plan_path = plans_dir / f"{plan_id}.json"
    meta_path = plans_dir / f"{plan_id}.meta.yaml"

    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    # Load plan
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = yaml.safe_load(f)

    plan = RenamePlan.model_validate(plan_data)
    metadata = RunMetadata.model_validate(meta_data)

    return plan, metadata


def get_latest_plan_id() -> Optional[str]:
    """Get the ID of the latest rename plan.

    Returns:
        Optional[str]: The ID of the latest plan, or None if no plans exist.
    """
    plans_dir = _ensure_plan_dir()
    latest_path = plans_dir / "latest.json"

    if not latest_path.exists():
        return None

    # Try different methods to get the latest plan ID
    return _extract_plan_id_from_latest(latest_path, plans_dir)


def _check_symlink_target(latest_path: Path) -> Optional[str]:
    """Check if the latest file is a symlink and get the target's stem.

    Args:
        latest_path: Path to the latest.json file

    Returns:
        str: Plan ID from symlink target, or None if not a symlink
    """
    if latest_path.is_symlink():
        # Extract ID from the target path
        target = latest_path.resolve()
        return target.stem
    return None


def _check_json_plan(latest_path: Path) -> Optional[str]:
    """Try to read the file as a JSON plan file.

    Args:
        latest_path: Path to the file to read

    Returns:
        str: Plan ID if found in JSON, None otherwise
    """
    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict) and "id" in data:
                    return cast(str, data["id"])
            except json.JSONDecodeError:
                # Not a JSON file
                pass
    except Exception:
        pass
    return None


def _check_plain_text_id(latest_path: Path, plans_dir: Path) -> Optional[str]:
    """Try to read the file as a plain text file containing just the plan ID.

    Args:
        latest_path: Path to the file to read
        plans_dir: Plans directory to check if the ID exists

    Returns:
        str: Plan ID if found and valid, None otherwise
    """
    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            # Check if it looks like a UUID
            if len(content) > MIN_UUID_LENGTH and "-" in content:
                # Verify this plan exists to avoid returning a stale reference
                if (plans_dir / f"{content}.json").exists():
                    return content
    except Exception:
        pass
    return None


def _find_latest_plan_file(plans_dir: Path) -> Optional[str]:
    """Find the most recent plan file by modification time.

    Args:
        plans_dir: Directory to search for plan files

    Returns:
        str: Plan ID from the most recent file, or None if no plans exist
    """
    try:
        plan_files = list(plans_dir.glob("*.json"))
        if not plan_files:
            return None

        # Filter out the latest.json file itself
        plan_files = [f for f in plan_files if f.name != "latest.json"]

        # Sort by modification time, newest first
        plan_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Get the first file and extract the UUID part
        if plan_files:
            return plan_files[0].stem
    except Exception:
        pass
    return None


def _extract_plan_id_from_latest(latest_path: Path, plans_dir: Path) -> Optional[str]:
    """Extract the plan ID from the latest.json file or symlink.

    Args:
        latest_path: Path to the latest.json file
        plans_dir: Path to the plans directory

    Returns:
        Optional[str]: The plan ID or None if it can't be determined
    """
    # Try each method in turn until one succeeds
    methods: List[Callable[[], Optional[str]]] = [
        lambda: _check_symlink_target(latest_path),
        lambda: _check_json_plan(latest_path),
        lambda: _check_plain_text_id(latest_path, plans_dir),
        lambda: _find_latest_plan_file(plans_dir),
    ]

    for method in methods:
        result = method()
        if result:
            return result

    # If all methods fail
    return None


def list_plans() -> List[Tuple[str, datetime]]:
    """List all available rename plans.

    Returns:
        list[tuple[str, datetime]]: List of tuples containing (plan_id, creation_date).
    """
    plans_dir = _ensure_plan_dir()
    result = []

    # Get all JSON files (exclude metadata files)
    plan_files = [
        f
        for f in plans_dir.glob("*.json")
        if f.name != "latest.json" and not f.name.endswith(".meta.json")
    ]

    for plan_file in plan_files:
        plan_id = plan_file.stem

        # Try to get timestamp from metadata
        meta_file = plans_dir / f"{plan_id}.meta.yaml"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta_data = yaml.safe_load(f)
                    if isinstance(meta_data, dict) and "timestamp" in meta_data:
                        ts = meta_data["timestamp"]
                        # Handle both datetime objects and ISO-format strings
                        if isinstance(ts, str):
                            timestamp = datetime.fromisoformat(ts)
                        else:
                            timestamp = ts
                        result.append((plan_id, timestamp))
                        continue
            except Exception:
                pass

        # Fallback to file modification time
        timestamp = datetime.fromtimestamp(plan_file.stat().st_mtime)
        result.append((plan_id, timestamp))

    # Sort by timestamp, newest first
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def get_plan_metadata(plan_id: str) -> RunMetadata:
    """Get the metadata for a rename plan.

    Args:
        plan_id: The ID of the plan to get metadata for.

    Returns:
        RunMetadata: The metadata for the plan.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    plans_dir = _ensure_plan_dir()
    meta_path = plans_dir / f"{plan_id}.meta.yaml"

    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    # Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = yaml.safe_load(f)

    return RunMetadata.model_validate(meta_data)
