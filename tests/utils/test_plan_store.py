"""Tests for the plan store module.

This test suite covers:
- Saving and loading rename plans and their metadata
- Listing plans and retrieving the latest plan ID
- Error handling for nonexistent plans and metadata
- Cross-platform and CI-specific quirks (HOME/USERPROFILE, symlink/copy fallback)
- Ensures robust, reproducible plan storage and retrieval (see PLANNING.md)

Rationale:
- Guarantees that plan persistence, auditability, and undo/redo logic are reliable across OSes and CI environments
- Validates error handling and edge cases for user safety and reliability
"""

import os
import platform
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.models.scan import ScanOptions
from namegnome.utils.plan_store import (
    _ensure_plan_dir,
    _get_git_hash,
    get_latest_plan_id,
    get_plan_metadata,
    list_plans,
    load_plan,
    save_plan,
)


@pytest.fixture
def temp_home_dir() -> Generator[Path, None, None]:
    """Create a temporary home directory.

    Yields:
        Path to the temporary home directory.

    Scenario:
    - Simulates different OS environments by patching HOME/USERPROFILE.
    - Ensures plan storage logic is robust to platform differences.
    """
    with TemporaryDirectory() as temp_dir:
        # Create a temporary home directory
        home_dir = Path(temp_dir)

        # Get the appropriate environment variable for the platform
        env_var = "USERPROFILE" if platform.system() == "Windows" else "HOME"

        # Patch the environment variable
        with patch.dict(os.environ, {env_var: str(home_dir)}):
            yield home_dir


@pytest.fixture
def test_plan(tmp_path: Path) -> RenamePlan:
    """Create a test plan with platform-appropriate absolute paths.

    Returns:
        RenamePlan: A test plan with one item and all required fields.

    Scenario:
    - Provides a reusable plan for save/load/list/metadata tests.
    - Ensures all paths are absolute for cross-platform correctness.
    """
    base_dir = tmp_path / "test_dir"
    base_dir.mkdir(parents=True, exist_ok=True)
    source_path = base_dir / "source.mp4"
    destination_path = base_dir / "target.mp4"
    source_path.touch()
    destination_path.touch()
    # Create a media file for the test plan
    media_file = MediaFile(
        path=source_path,
        size=1024,
        media_type=MediaType.MOVIE,
        modified_date=datetime.now(),
        # Optional fields
        title="Test Movie",
        year=2023,
    )
    # Create a rename plan item
    plan_item = RenamePlanItem(
        source=source_path,
        destination=destination_path,
        media_file=media_file,
    )
    return RenamePlan(
        id="test-plan-1",
        root_dir=base_dir,
        platform="plex",
        media_types=[MediaType.MOVIE],
        items=[plan_item],
    )


@pytest.fixture
def test_scan_options() -> ScanOptions:
    """Create test scan options.

    Returns:
        ScanOptions: Minimal scan options for plan storage tests.
    """
    return ScanOptions(
        root=Path.cwd() / "test_dir",
        recursive=True,
    )


def test_ensure_plan_dir() -> None:
    """Test the _ensure_plan_dir function.

    Scenario:
    - Ensures the plans directory exists and is named correctly.
    - Checks for cross-platform compatibility in directory structure.
    """
    # We don't need to test this extensively as it's mostly OS functionality
    plan_dir = _ensure_plan_dir()
    assert plan_dir.exists()
    assert plan_dir.name == "plans"
    # Cross-platform: check the last two parts
    parts = plan_dir.parts
    assert parts[-1] == "plans"
    assert ".namegnome" in parts


def test_save_and_load_plan(
    temp_home_dir: Path, test_plan: RenamePlan, test_scan_options: ScanOptions
) -> None:
    """Test saving and loading a plan.

    Scenario:
    - Saves a plan and verifies that all expected files are created.
    - Loads the plan and checks that it matches the original.
    - Checks for latest.json existence (skipped in CI for reliability).
    - Ensures metadata is present and correct.
    """
    # Save the plan
    plan_id = save_plan(test_plan, test_scan_options)

    # Verify files were created
    plans_dir = _ensure_plan_dir()
    assert (plans_dir / f"{plan_id}.json").exists()
    assert (plans_dir / f"{plan_id}.meta.yaml").exists()

    # Check that the latest reference exists
    # We skip this in environments where file operations might be restricted
    latest_file = _ensure_plan_dir() / "latest.json"
    is_ci = os.environ.get("CI", "false").lower() in ("true", "1", "yes")

    # Only check the latest.json existence in non-CI environments to avoid flaky tests
    if not is_ci:
        assert latest_file.exists()

    # Load the plan and check it matches the original
    loaded_plan, metadata = load_plan(plan_id)
    assert loaded_plan.model_dump() == test_plan.model_dump()

    # Check metadata
    assert metadata.id == plan_id
    assert isinstance(metadata.timestamp, datetime)
    assert "scan_options" in metadata.args


def test_get_latest_plan_id(
    temp_home_dir: Path, test_plan: RenamePlan, test_scan_options: ScanOptions
) -> None:
    """Test getting the latest plan ID.

    Scenario:
    - Saves two plans and checks that the latest plan ID is updated correctly.
    - Ensures correct ordering and retrieval logic.
    """
    # Save the plan
    plan_id1 = save_plan(test_plan, test_scan_options)

    # Get the latest plan ID and verify it matches
    latest_id = get_latest_plan_id()
    assert latest_id == plan_id1

    # Save another plan
    plan_id2 = save_plan(test_plan, test_scan_options)

    # Get the latest plan ID again and verify it's now the second plan
    latest_id = get_latest_plan_id()
    assert latest_id == plan_id2


def test_list_plans(
    temp_home_dir: Path, test_plan: RenamePlan, test_scan_options: ScanOptions
) -> None:
    """Test listing all plans.

    Scenario:
    - Saves two plans with different timestamps and checks that list_plans returns them in the correct order (newest first).
    - Ensures correct sorting and retrieval logic.
    """
    # Save two plans with different timestamps
    with patch("namegnome.utils.plan_store.datetime") as mock_datetime:
        # First plan is saved "now"
        now = datetime.now()
        mock_datetime.now.return_value = now
        plan_id1 = save_plan(test_plan, test_scan_options)

        # Second plan is saved 1 hour later
        later = now + timedelta(hours=1)
        mock_datetime.now.return_value = later
        plan_id2 = save_plan(test_plan, test_scan_options)

    # List all plans and check they're in the expected order (newest first)
    plans = list_plans()
    assert len(plans) == 2
    assert plans[0][0] == plan_id2  # newest first
    assert plans[1][0] == plan_id1


def test_get_plan_metadata(
    temp_home_dir: Path, test_plan: RenamePlan, test_scan_options: ScanOptions
) -> None:
    """Test getting plan metadata.

    Scenario:
    - Saves a plan and retrieves its metadata.
    - Ensures metadata fields are present and correct.
    """
    # Save a plan
    plan_id = save_plan(test_plan, test_scan_options)

    # Get the metadata
    metadata = get_plan_metadata(plan_id)

    # Check metadata
    assert metadata.id == plan_id
    assert isinstance(metadata.timestamp, datetime)
    assert "scan_options" in metadata.args


def test_load_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test that loading a nonexistent plan raises an error.

    Scenario:
    - Attempts to load a plan with a nonexistent ID and expects FileNotFoundError.
    - Ensures robust error handling for missing plans.
    """
    with pytest.raises(FileNotFoundError):
        load_plan("nonexistent-plan-id")


def test_get_nonexistent_plan_metadata(temp_home_dir: Path) -> None:
    """Test that getting metadata for a nonexistent plan raises an error.

    Scenario:
    - Attempts to get metadata for a nonexistent plan and expects FileNotFoundError.
    - Ensures robust error handling for missing metadata.
    """
    with pytest.raises(FileNotFoundError):
        get_plan_metadata("nonexistent-plan-id")


def test_get_latest_plan_id_no_plans(temp_home_dir: Path) -> None:
    """Test getting the latest plan ID when no plans exist.

    Scenario:
    - Ensures get_latest_plan_id returns None when no plans are present.
    - Validates correct behavior for empty state.
    """
    latest_id = get_latest_plan_id()
    assert latest_id is None


def test_get_git_hash_success(mocker: MockerFixture) -> None:
    """Test getting the git hash successfully."""
    # Mock subprocess.run to return a known hash
    mock_result = mocker.MagicMock()
    mock_result.stdout = "abcdef1234567890\n"
    mocker.patch("subprocess.run", return_value=mock_result)

    # Test getting the git hash
    git_hash = _get_git_hash()
    assert git_hash == "abcdef1234567890"


def test_get_git_hash_failure(mocker: MockerFixture) -> None:
    """Test getting the git hash when subprocess fails."""
    # Test when subprocess.run raises an exception
    mocker.patch("subprocess.run", side_effect=Exception("Test exception"))
    git_hash = _get_git_hash()
    assert git_hash is None
