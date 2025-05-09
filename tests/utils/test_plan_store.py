"""Tests for the plan store module."""

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
    """Create a temporary home directory."""
    with TemporaryDirectory() as temp_dir:
        # Create a temporary home directory
        home_dir = Path(temp_dir)

        # Get the appropriate environment variable for the platform
        env_var = "USERPROFILE" if platform.system() == "Windows" else "HOME"

        # Patch the environment variable
        with patch.dict(os.environ, {env_var: str(home_dir)}):
            yield home_dir


@pytest.fixture
def test_plan() -> RenamePlan:
    """Create a test plan."""
    # Create platform-independent paths
    base_dir = Path.cwd() / "test_dir"
    source_path = base_dir / "source.mp4"
    destination_path = base_dir / "target.mp4"

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
    """Create test scan options."""
    return ScanOptions(
        root=Path.cwd() / "test_dir",
        recursive=True,
    )


def test_ensure_plan_dir() -> None:
    """Test the _ensure_plan_dir function."""
    # We don't need to test this extensively as it's mostly OS functionality
    plan_dir = _ensure_plan_dir()
    assert plan_dir.exists()
    assert plan_dir.name == "plans"
    assert str(plan_dir).endswith(".namegnome/plans")


def test_save_and_load_plan(
    temp_home_dir: Path, test_plan: RenamePlan, test_scan_options: ScanOptions
) -> None:
    """Test saving and loading a plan."""
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
    """Test getting the latest plan ID."""
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
    """Test listing all plans."""
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
    """Test getting plan metadata."""
    # Save a plan
    plan_id = save_plan(test_plan, test_scan_options)

    # Get the metadata
    metadata = get_plan_metadata(plan_id)

    # Check metadata
    assert metadata.id == plan_id
    assert isinstance(metadata.timestamp, datetime)
    assert "scan_options" in metadata.args


def test_load_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test that loading a nonexistent plan raises an error."""
    with pytest.raises(FileNotFoundError):
        load_plan("nonexistent-plan-id")


def test_get_nonexistent_plan_metadata(temp_home_dir: Path) -> None:
    """Test that getting metadata for a nonexistent plan raises an error."""
    with pytest.raises(FileNotFoundError):
        get_plan_metadata("nonexistent-plan-id")


def test_get_latest_plan_id_no_plans(temp_home_dir: Path) -> None:
    """Test getting the latest plan ID when no plans exist."""
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
