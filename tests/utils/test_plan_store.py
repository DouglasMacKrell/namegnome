"""Tests for the plan store module."""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from unittest.mock import patch

import pytest
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.models.scan import ScanOptions
from namegnome.utils.plan_store import (
    _ensure_plan_dir,
    _get_git_hash,
    get_plan_metadata,
    list_plans,
    load_plan,
    save_plan,
)
from pytest_mock import MockerFixture


@pytest.fixture
def temp_home_dir() -> Generator[Path, None, None]:
    """Create a temporary home directory."""
    with TemporaryDirectory() as temp_dir:
        with patch.dict(os.environ, {"HOME": temp_dir}):
            yield Path(temp_dir)


@pytest.fixture
def sample_media_file(tmp_path: Path) -> MediaFile:
    """Create a sample media file."""
    return MediaFile(
        path=tmp_path / "test.mp4",
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )


@pytest.fixture
def sample_plan(sample_media_file: MediaFile, tmp_path: Path) -> RenamePlan:
    """Create a sample rename plan."""
    return RenamePlan(
        id="test_plan",
        root_dir=tmp_path,
        platform="plex",
        media_types=[MediaType.TV],
        items=[
            RenamePlanItem(
                source=sample_media_file.path,
                destination=tmp_path / "destination" / "test.mp4",
                media_file=sample_media_file,
            )
        ],
    )


@pytest.fixture
def sample_scan_options(tmp_path: Path) -> ScanOptions:
    """Create a sample scan options."""
    return ScanOptions(
        root=tmp_path,
        media_types=[MediaType.TV],
        platform="plex",
    )


def test_ensure_plan_dir(temp_home_dir: Path) -> None:
    """Test that the plan directory is created correctly."""
    plan_dir = _ensure_plan_dir()
    assert plan_dir.exists()
    assert plan_dir.is_dir()
    assert plan_dir == Path.home() / ".namegnome" / "plans"


def test_get_git_hash() -> None:
    """Test that the git hash is retrieved correctly."""
    # This might return None in CI, but should work in a git repo
    git_hash = _get_git_hash()
    if git_hash is not None:
        assert isinstance(git_hash, str)
        assert len(git_hash) == 40  # SHA-1 hash is 40 hex characters


def test_save_and_load_plan(
    sample_plan: RenamePlan, sample_scan_options: ScanOptions, temp_home_dir: Path
) -> None:
    """Test saving and loading a plan."""
    # Save the plan
    plan_id = save_plan(sample_plan, sample_scan_options)

    # Check that the plan directory was created
    plan_dir = _ensure_plan_dir() / plan_id
    assert plan_dir.exists()
    assert plan_dir.is_dir()

    # Check that the plan file was created
    plan_file = plan_dir / "plan.json"
    assert plan_file.exists()

    # Check that the metadata file was created
    metadata_file = plan_dir / "run.yaml"
    assert metadata_file.exists()

    # Check that the latest reference exists (symlink on Unix, copy on Windows)
    latest_file = _ensure_plan_dir() / "latest.json"
    # Skip this assertion if we're on Windows in CI environment
    if not (os.name == 'nt' and os.environ.get('CI')):
        assert latest_file.exists()

    # Load the plan with specific ID
    loaded_plan = load_plan(plan_id)
    # The ID might be different now because we use UUID-based IDs
    assert loaded_plan.platform == sample_plan.platform
    assert str(loaded_plan.root_dir) == str(sample_plan.root_dir)
    assert len(loaded_plan.items) == len(sample_plan.items)


def test_save_plan_with_verify(
    sample_plan: RenamePlan,
    sample_scan_options: ScanOptions,
    temp_home_dir: Path,
    mocker: MockerFixture,
) -> None:
    """Test saving a plan with verify=True."""
    # Mock the sha256sum function
    mock_sha256sum = mocker.patch(
        "namegnome.utils.hash.sha256sum", return_value="fake_hash"
    )

    # Save the plan with verify=True
    plan_id = save_plan(sample_plan, sample_scan_options, verify=True)

    # Check that the checksums file was created
    checksum_file = _ensure_plan_dir() / plan_id / "checksums.json"
    assert checksum_file.exists()

    # Check that the checksum was computed
    mock_sha256sum.assert_called_once()

    # Check the contents of the checksums file
    with open(checksum_file, "r") as f:
        checksums = json.load(f)
    assert str(sample_plan.items[0].source) in checksums
    assert checksums[str(sample_plan.items[0].source)] == "fake_hash"


def test_get_plan_metadata(
    sample_plan: RenamePlan, sample_scan_options: ScanOptions, temp_home_dir: Path
) -> None:
    """Test getting plan metadata."""
    # Save the plan
    plan_id = save_plan(sample_plan, sample_scan_options)

    # Get the metadata
    metadata = get_plan_metadata(plan_id)

    # Check the metadata
    assert metadata.id == plan_id
    assert isinstance(metadata.timestamp, datetime)
    assert metadata.args["root"] == str(sample_scan_options.root)
    assert metadata.args["platform"] == sample_scan_options.platform


def test_list_plans(
    sample_plan: RenamePlan, sample_scan_options: ScanOptions, temp_home_dir: Path
) -> None:
    """Test listing plans."""
    # Save the plan once to ensure the directory is clean
    save_plan(sample_plan, sample_scan_options)

    # Clear the plans directory
    plans_dir = _ensure_plan_dir()
    for item in plans_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        elif item.is_file() and item.name != '.gitkeep':  # Keep any .gitkeep files
            item.unlink()

    # Save multiple plans with different timestamps
    plan_ids = []
    expected_timestamps = []

    for i in range(3):
        # Make each plan have a different timestamp
        with patch("namegnome.utils.plan_store.datetime") as mock_datetime:
            mock_now = datetime.now() - timedelta(days=i)
            mock_datetime.now.return_value = mock_now
            expected_timestamps.append(mock_now)
            plan_id = save_plan(sample_plan, sample_scan_options)
            plan_ids.append(plan_id)

    # List the plans
    plans = list_plans()

    # Check that all plans are listed
    assert len(plans) == 3

    # Check that each plan ID has an associated timestamp
    for plan_id in plan_ids:
        assert plan_id in plans
        assert isinstance(plans[plan_id], datetime)


def test_load_nonexistent_plan(temp_home_dir: Path) -> None:
    """Test loading a nonexistent plan."""
    with pytest.raises(FileNotFoundError):
        load_plan("nonexistent_plan")


def test_get_nonexistent_plan_metadata(temp_home_dir: Path) -> None:
    """Test getting metadata for a nonexistent plan."""
    with pytest.raises(FileNotFoundError):
        get_plan_metadata("nonexistent_plan")


def test_load_latest_plan(
    sample_plan: RenamePlan, sample_scan_options: ScanOptions, temp_home_dir: Path
) -> None:
    """Test loading the latest plan."""
    # Skip on Windows in CI environment since symlinks might not work
    if os.name == 'nt' and os.environ.get('CI'):
        pytest.skip("Skipping test on Windows in CI environment")

    # Save the plan, which gives us a UUID-based plan ID
    plan_id = save_plan(sample_plan, sample_scan_options)

    # Load the latest plan
    loaded_plan = load_plan()

    # Since we're now using UUID-based IDs, the loaded plan's ID won't match the sample plan's
    # original ID, but it should match the returned plan_id from save_plan
    assert loaded_plan.platform == sample_plan.platform
    assert str(loaded_plan.root_dir) == str(sample_plan.root_dir)
    assert len(loaded_plan.items) == len(sample_plan.items)

    # Get a plan with the specific ID to verify it matches the latest
    specific_plan = load_plan(plan_id)
    assert specific_plan.id == loaded_plan.id
