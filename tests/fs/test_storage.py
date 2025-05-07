"""Tests for the filesystem storage module."""

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator
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
def temp_home_dir() -> Iterator[Path]:
    """Create a temporary home directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.dict(os.environ, {"HOME": temp_dir}):
            # Create the plans directory structure
            plans_dir = Path(temp_dir) / ".namegnome" / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            yield Path(temp_dir)


@pytest.fixture
def plan_store_dir(temp_home_dir: Path) -> Path:
    """Create and return the plan store directory."""
    plans_dir = get_plans_dir()
    assert plans_dir.exists()
    return plans_dir


@pytest.fixture
def test_plan() -> RenamePlan:
    """Create a test rename plan."""
    # Used for creating a test plan, even though not directly referenced in the plan
    # (to demonstrate we're creating a valid plan)
    _ = MediaFile(
        path=Path("/test/file.mp4").absolute(),
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )

    return RenamePlan(
        id="20250101_010101",
        created_at=datetime.now(),
        root_dir=Path("/test").absolute(),
        platform="plex",
        media_types=[MediaType.TV],
        items=[],
        metadata_providers=[],
        llm_model=None,
    )


@pytest.fixture
def test_scan_options() -> ScanOptions:
    """Create test scan options."""
    return ScanOptions(
        root=Path("/test").absolute(),
        media_types=[MediaType.TV],
        platform="plex",
    )


def test_get_namegnome_dir(temp_home_dir: Path) -> None:
    """Test that get_namegnome_dir returns the correct path and creates directories."""
    namegnome_dir = get_namegnome_dir()

    # Check that the directory exists
    assert namegnome_dir.exists()
    assert namegnome_dir.is_dir()

    # We now create the plans directory only when needed, not in get_namegnome_dir
    plans_dir = namegnome_dir / "plans"
    assert plans_dir.exists()


def test_get_plans_dir(temp_home_dir: Path) -> None:
    """Test that get_plans_dir returns the correct path."""
    plans_dir = get_plans_dir()

    # Check that the directory exists
    assert plans_dir.exists()
    assert plans_dir.is_dir()

    # Check that it's a subdirectory of the namegnome directory
    assert plans_dir.parent == get_namegnome_dir()


def test_store_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test storing a rename plan."""
    # Store the plan using the new method which now internally creates ScanOptions
    plan_path = store_plan(test_plan)

    # Check that the file exists
    assert plan_path.exists()
    assert plan_path.is_file()

    # UUID format is used now, so check the parent directory follows the pattern
    uuid_pattern = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
    plan_dir = plan_path.parent.name
    assert re.match(uuid_pattern, plan_dir)

    # Read the plan file and verify its contents
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    # The stored plan will have a different ID than the original due to UUID regeneration
    assert "id" in plan_data
    assert plan_data["platform"] == test_plan.platform


def test_store_run_metadata(
    temp_home_dir: Path, test_scan_options: ScanOptions
) -> None:
    """Test storing run metadata."""
    # Generate a UUID-style plan ID
    plan_id = "12345678-1234-1234-1234-123456789012"

    # Create the plan directory
    plan_dir = get_plans_dir() / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)

    # Convert the scan options to args dict
    args = test_scan_options.model_dump()

    # Store metadata
    metadata_path = store_run_metadata(plan_id, args)

    # Check that the file exists
    assert metadata_path.exists()
    assert metadata_path.is_file()

    # Read the metadata file and verify its contents - now using YAML format
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    assert metadata["plan_id"] == plan_id
    assert metadata["args"] is not None
    assert "timestamp" in metadata


def test_list_plans(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test listing plans."""
    # Store a plan
    plan_path = store_plan(test_plan)

    # Extract the generated UUID from the plan path
    uuid_pattern = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
    plan_dir = plan_path.parent.name
    assert re.match(uuid_pattern, plan_dir)

    # List plans
    plans = list_plans()

    # Check that a plan is in the list
    assert len(plans) == 1

    # Get the first plan from the list
    plan_info = plans[0]

    # The first element is the plan ID (UUID)
    assert re.match(uuid_pattern, plan_info[0])

    # The third element is the path
    assert plan_info[2].exists()


def test_get_latest_plan(test_plan: RenamePlan, plan_store_dir: Path) -> None:
    """Test getting the latest plan."""
    # Store a plan
    plan_path = store_plan(test_plan)
    
    # Extract the actual plan ID from the path (UUID directory name)
    actual_plan_id = plan_path.parent.name

    # Get the latest plan
    latest_plan = get_latest_plan()

    # Check that we got a plan back
    assert latest_plan is not None
    
    # Check that the plan ID matches the actual ID after storage (not the original ID)
    plan_id = latest_plan[0] if isinstance(latest_plan, tuple) else latest_plan.id
    assert plan_id == actual_plan_id


def test_get_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test getting a plan by ID."""
    # Store a plan
    plan_path = store_plan(test_plan)

    # Extract the generated UUID from the plan path
    plan_id = plan_path.parent.name

    # Get the plan using the UUID
    plan_data = get_plan(plan_id)

    # Check that we got a plan
    assert plan_data is not None
    assert "id" in plan_data
    assert plan_data["platform"] == test_plan.platform


def test_get_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test getting a nonexistent plan."""
    plan_data = get_plan("nonexistent")
    assert plan_data is None
