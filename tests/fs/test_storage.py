"""Tests for the namegnome.fs.storage module."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import pytest
from namegnome.fs.storage import (
    get_latest_plan,
    get_namegnome_dir,
    get_plan,
    get_plans_dir,
    list_plans,
    store_plan,
    store_run_metadata,
)
from namegnome.models.core import MediaFile, MediaType, RenamePlan


@pytest.fixture
def temp_home_dir() -> Iterator[Path]:
    """Create a temporary home directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.dict(os.environ, {"HOME": temp_dir}):
            yield Path(temp_dir)


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
    )


def test_get_namegnome_dir(temp_home_dir: Path) -> None:
    """Test that get_namegnome_dir returns the correct path and creates directories."""
    namegnome_dir = get_namegnome_dir()

    # Check that the directory exists
    assert namegnome_dir.exists()
    assert namegnome_dir.is_dir()

    # Check that the plans directory exists
    plans_dir = namegnome_dir / "plans"
    assert plans_dir.exists()
    assert plans_dir.is_dir()


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
    plan_path = store_plan(test_plan)

    # Check that the file exists
    assert plan_path.exists()
    assert plan_path.is_file()

    # Check that the latest.json symlink exists
    latest_path = get_namegnome_dir() / "latest.json"
    assert latest_path.exists()

    # Read the plan file and verify its contents
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    assert plan_data["id"] == test_plan.id
    assert plan_data["platform"] == test_plan.platform


def test_store_run_metadata(temp_home_dir: Path) -> None:
    """Test storing run metadata."""
    plan_id = "20250101_010101"
    args = {
        "root": "/test",
        "media_type": ["tv"],
        "platform": "plex",
    }

    metadata_path = store_run_metadata(plan_id, args)

    # Check that the file exists
    assert metadata_path.exists()
    assert metadata_path.is_file()

    # Read the metadata file and verify its contents
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    assert metadata["plan_id"] == plan_id
    assert metadata["args"] == args
    assert "timestamp" in metadata


def test_list_plans(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test listing plans."""
    # Store a plan
    plan_path = store_plan(test_plan)

    # List plans
    plans = list_plans()

    # Check that the plan is in the list
    assert len(plans) == 1
    assert plans[0][0] == test_plan.id
    assert plans[0][2] == plan_path


def test_get_latest_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test getting the latest plan."""
    # Store a plan
    # We don't need the plan_path variable after storing, but we're storing for test setup
    _ = store_plan(test_plan)

    # Get the latest plan
    latest = get_latest_plan()

    # Check that the latest plan is the one we stored
    assert latest is not None
    assert latest[0] == test_plan.id


def test_get_plan(temp_home_dir: Path, test_plan: RenamePlan) -> None:
    """Test getting a plan by ID."""
    # Store a plan
    store_plan(test_plan)

    # Get the plan
    plan_data = get_plan(test_plan.id)

    # Check that we got the correct plan
    assert plan_data is not None
    assert plan_data["id"] == test_plan.id
    assert plan_data["platform"] == test_plan.platform


def test_get_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test getting a nonexistent plan."""
    plan_data = get_plan("nonexistent")
    assert plan_data is None
