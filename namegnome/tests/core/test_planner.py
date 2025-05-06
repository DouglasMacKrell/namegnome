"""Tests for the rename planner module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from namegnome.core.planner import create_rename_plan, save_plan
from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
from namegnome.rules.plex import PlexRuleSet


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def scan_result(temp_dir: Path) -> ScanResult:
    """Create a sample scan result with test files."""
    # Create some test files
    tv_file = temp_dir / "Breaking Bad S01E01.mp4"
    tv_file.write_bytes(b"dummy content")
    movie_file = temp_dir / "Inception (2010).mp4"
    movie_file.write_bytes(b"dummy content")
    music_file = temp_dir / "song.mp3"
    music_file.write_bytes(b"dummy content")

    # Create media files
    media_files = [
        MediaFile(
            path=tv_file.absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        ),
        MediaFile(
            path=movie_file.absolute(),
            size=1024,
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(),
        ),
        MediaFile(
            path=music_file.absolute(),
            size=1024,
            media_type=MediaType.MUSIC,
            modified_date=datetime.now(),
        ),
    ]

    return ScanResult(
        total_files=3,
        media_files=media_files,
        skipped_files=0,
        by_media_type={
            MediaType.TV: 1,
            MediaType.MOVIE: 1,
            MediaType.MUSIC: 1,
        },
        scan_duration_seconds=0.1,
        root_dir=temp_dir.absolute(),
    )


class TestCreateRenamePlan:
    """Tests for the create_rename_plan function."""

    def test_create_plan_with_plex_rules(self, scan_result: ScanResult) -> None:
        """Test creating a plan with Plex rules."""
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Check plan properties
        assert plan.id == "test-plan"
        assert plan.platform == "plex"
        assert plan.root_dir == scan_result.root_dir
        assert len(plan.items) == 2  # Only TV and Movie, Music is not supported by Plex

        # Check TV show item
        tv_item = next(item for item in plan.items if item.media_file.media_type == MediaType.TV)
        assert tv_item.status == PlanStatus.PENDING
        assert "Breaking Bad" in str(tv_item.destination)
        assert "Season 01" in str(tv_item.destination)
        assert "S01E01" in str(tv_item.destination)

        # Check movie item
        movie_item = next(
            item for item in plan.items if item.media_file.media_type == MediaType.MOVIE
        )
        assert movie_item.status == PlanStatus.PENDING
        assert "Inception" in str(movie_item.destination)
        assert "(2010)" in str(movie_item.destination)

    def test_detect_conflicts(self, temp_dir: Path) -> None:
        """Test that conflicts are detected correctly."""
        # Create two files that would map to the same destination
        file1 = temp_dir / "Show S01E01.mp4"
        file2 = temp_dir / "Show - S01E01.mp4"
        file1.write_bytes(b"dummy content")
        file2.write_bytes(b"dummy content")

        # Create scan result with these files
        media_files = [
            MediaFile(
                path=file1.absolute(),
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            ),
            MediaFile(
                path=file2.absolute(),
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            ),
        ]

        scan_result = ScanResult(
            total_files=2,
            media_files=media_files,
            skipped_files=0,
            by_media_type={MediaType.TV: 2},
            scan_duration_seconds=0.1,
            root_dir=temp_dir.absolute(),
        )

        # Create plan
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Check that both items are marked as conflicting
        assert len(plan.items) == 2
        assert all(item.status == PlanStatus.CONFLICT for item in plan.items)
        assert all(item.reason is not None for item in plan.items)
        assert any("Show S01E01.mp4" in str(item.reason) for item in plan.items)
        assert any("Show - S01E01.mp4" in str(item.reason) for item in plan.items)

    def test_handle_unsupported_media_type(self, scan_result: ScanResult) -> None:
        """Test handling of unsupported media types."""
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Music files should be skipped (not in plan items)
        assert len(plan.items) == 2
        assert not any(item.media_file.media_type == MediaType.MUSIC for item in plan.items)


class TestSavePlan:
    """Tests for the save_plan function."""

    def test_save_plan_to_json(self, scan_result: ScanResult, temp_dir: Path) -> None:
        """Test saving a plan to a JSON file."""
        # Create a plan
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Save the plan
        output_dir = temp_dir / "plans"
        output_file = save_plan(plan, output_dir)

        # Check that the file exists
        assert output_file.exists()
        assert output_file.name == "plan_test-plan.json"

        # Read and parse the JSON
        with output_file.open("r", encoding="utf-8") as f:
            saved_plan = json.load(f)

        # Check the saved data
        assert saved_plan["id"] == "test-plan"
        assert saved_plan["platform"] == "plex"
        assert len(saved_plan["items"]) == 2
        assert all(isinstance(item["source"], str) for item in saved_plan["items"])
        assert all(isinstance(item["destination"], str) for item in saved_plan["items"])

    def test_create_output_directory(self, scan_result: ScanResult, temp_dir: Path) -> None:
        """Test that the output directory is created if it doesn't exist."""
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Try to save to a non-existent directory
        output_dir = temp_dir / "new" / "plans"
        output_file = save_plan(plan, output_dir)

        # Check that the directory was created
        assert output_dir.exists()
        assert output_file.exists()
