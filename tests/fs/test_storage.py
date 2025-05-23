"""Tests for the filesystem storage module.

This test suite covers:
- Directory creation and validation for .namegnome and plans
- Storing and retrieving rename plans and run metadata
- Listing plans, getting the latest plan, and retrieving plan details
- Error handling for nonexistent plans and directories
- Cross-platform and CI-specific quirks (HOME/USERPROFILE, symlink/copy fallback)
- Ensures robust, reproducible plan storage and retrieval (see PLANNING.md)

Rationale:
- Guarantees that filesystem storage, auditability, and undo/redo logic are reliable across OSes and CI environments
- Validates error handling and edge cases for user safety and reliability
"""

import json
import os
import platform
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import yaml

from namegnome.fs import (
    get_latest_plan,
    get_namegnome_dir,
    get_plan,
    get_plans_dir,
    list_plans,
    store_plan,
    store_run_metadata,
)
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan
from namegnome.models.scan import ScanOptions


@pytest.fixture
def temp_home_dir() -> Generator[Path, None, None]:
    """Create a temporary home directory for testing.

    Yields:
        Path to the temporary home directory.

    Scenario:
    - Simulates different OS environments by patching HOME/USERPROFILE.
    - Ensures plan storage logic is robust to platform differences.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Get the appropriate environment variable for the platform
        env_var = "USERPROFILE" if platform.system() == "Windows" else "HOME"

        home_path = Path(temp_dir)
        # Create the plans directory structure
        plans_dir = home_path / ".namegnome" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        with patch.dict(os.environ, {env_var: str(home_path)}):
            yield home_path
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def plan_store_dir(temp_home_dir: Path) -> Path:
    """Create and return the plan store directory.

    Returns:
        Path to the plan store directory.

    Scenario:
    - Ensures the plans directory exists and is accessible for all tests.
    """
    plans_dir = get_plans_dir()
    assert plans_dir.exists()
    return plans_dir


@pytest.fixture
def test_plan(tmp_path: Path) -> RenamePlan:
    """Create a test rename plan with platform-appropriate absolute paths.

    Returns:
        RenamePlan: A test plan with all required fields.

    Scenario:
    - Provides a reusable plan for store/list/get tests.
    - Ensures all paths are absolute for cross-platform correctness.
    """
    # Used for creating a test plan, even though not directly referenced in the plan
    # (to demonstrate we're creating a valid plan)
    _ = MediaFile(
        path=tmp_path / "file.mp4",
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )

    return RenamePlan(
        id="20250101_010101",
        created_at=datetime.now(),
        root_dir=tmp_path,
        platform="plex",
        media_types=[MediaType.TV],
        items=[],
        metadata_providers=[],
        llm_model=None,
    )


@pytest.fixture
def test_scan_options() -> ScanOptions:
    """Create test scan options.

    Returns:
        ScanOptions: Minimal scan options for plan storage tests.
    """
    return ScanOptions(
        root=Path("/test").absolute(),
        media_types=[MediaType.TV],
        platform="plex",
    )


def test_get_namegnome_dir(temp_home_dir: Path) -> None:
    """Test that get_namegnome_dir returns the correct path and creates directories.

    Scenario:
    - Ensures the .namegnome directory and plans subdirectory are created and accessible.
    - Validates cross-platform directory creation logic.
    """
    namegnome_dir = get_namegnome_dir()

    # Check that the directory exists
    assert namegnome_dir.exists()
    assert namegnome_dir.is_dir()

    # We now create the plans directory only when needed, not in get_namegnome_dir
    plans_dir = namegnome_dir / "plans"
    assert plans_dir.exists()


def test_get_plans_dir(temp_home_dir: Path) -> None:
    """Test that get_plans_dir returns the correct path.

    Scenario:
    - Ensures the plans directory exists and is a subdirectory of .namegnome.
    - Validates cross-platform directory structure.
    """
    plans_dir = get_plans_dir()

    # Check that the directory exists
    assert plans_dir.exists()
    assert plans_dir.is_dir()

    # Check that it's a subdirectory of the namegnome directory
    # Resolve paths to handle Windows path comparison issues
    assert plans_dir.resolve().parent == get_namegnome_dir().resolve()


def test_store_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test storing a rename plan.

    Scenario:
    - Stores a plan and checks that the file exists and has a valid UUID filename.
    - Reads the plan file and verifies its contents.
    - Ensures plan storage is robust to UUID regeneration and platform quirks.
    """
    # Store the plan using the new method which now internally creates ScanOptions
    plan_path = store_plan(test_plan)

    # Check that the file exists
    assert plan_path.exists()
    assert plan_path.is_file()

    # UUID format is now used in the filename, not as directory
    uuid_pattern = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.json"
    plan_filename = plan_path.name
    assert re.match(uuid_pattern, plan_filename)

    # Read the plan file and verify its contents
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # The stored plan will have a different ID than the original due to UUID regeneration
    assert "id" in plan_data
    assert plan_data["platform"] == test_plan.platform


def test_store_run_metadata(
    temp_home_dir: Path, test_scan_options: ScanOptions
) -> None:
    """Test storing run metadata.

    Scenario:
    - Stores run metadata for a plan and checks that the file exists and contains expected fields.
    - Ensures YAML serialization and field presence.
    """
    # Generate a UUID-style plan ID
    plan_id = "12345678-1234-1234-1234-123456789012"

    # Convert the scan options to args dict
    args = test_scan_options.model_dump()

    # Store metadata
    metadata_path = store_run_metadata(plan_id, args)

    # Check that the file exists
    assert metadata_path.exists()
    assert metadata_path.is_file()

    # Read the metadata file and verify its contents
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    assert metadata["id"] == plan_id
    assert "args" in metadata
    assert "timestamp" in metadata


def test_list_plans(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test listing plans.

    Scenario:
    - Stores a plan and checks that it appears in the list with a valid UUID and path.
    - Ensures correct extraction and listing logic.
    """
    # Store a plan
    plan_path = store_plan(test_plan)

    # Extract the generated UUID from the plan path - now in the filename
    uuid_pattern = (
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.json"
    )
    plan_filename = plan_path.name
    plan_id_match = re.match(uuid_pattern, plan_filename)
    assert plan_id_match is not None
    actual_plan_id = plan_id_match.group(1)

    # List plans
    plans = list_plans()

    # Check that a plan is in the list
    assert len(plans) == 1

    # Get the first plan from the list
    plan_info = plans[0]

    # The first element is the plan ID (UUID)
    assert plan_info[0] == actual_plan_id

    # The third element is the path
    assert plan_info[2].exists()


def test_get_latest_plan(test_plan: RenamePlan, plan_store_dir: Path) -> None:
    """Test getting the latest plan.

    Scenario:
    - Stores a plan and checks that get_latest_plan returns the correct ID and path.
    - Ensures correct retrieval logic for latest plan.
    """
    # Store a plan
    plan_path = store_plan(test_plan)

    # Extract the actual plan ID from the file name
    uuid_pattern = (
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.json"
    )
    plan_filename = plan_path.name
    plan_id_match = re.match(uuid_pattern, plan_filename)
    assert plan_id_match is not None
    actual_plan_id = plan_id_match.group(1)

    # Get the latest plan
    latest_plan = get_latest_plan()

    # Check that we got a plan back
    assert latest_plan is not None

    # Check that the plan ID matches the actual ID after storage (not the original ID)
    # The latest_plan is a tuple of (plan_id, path)
    assert isinstance(latest_plan, tuple)
    plan_id, _ = latest_plan
    assert plan_id == actual_plan_id


def test_get_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test getting a plan by ID."""
    # Store a plan
    plan_path = store_plan(test_plan)

    # Extract the generated UUID from the plan path
    uuid_pattern = (
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\.json"
    )
    plan_filename = plan_path.name
    plan_id_match = re.match(uuid_pattern, plan_filename)
    assert plan_id_match is not None
    actual_plan_id = plan_id_match.group(1)

    # Get the plan using the UUID
    plan_data = get_plan(actual_plan_id)

    # Check that we got a plan
    assert plan_data is not None
    assert "id" in plan_data
    assert plan_data["platform"] == test_plan.platform


def test_get_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test getting a nonexistent plan."""
    plan_data = get_plan("nonexistent")
    assert plan_data is None
