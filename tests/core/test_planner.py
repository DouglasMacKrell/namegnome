"""Tests for the planner module.

This test suite covers:
- Creation of rename plans from scan results using rule sets (e.g., Plex)
- Detection of conflicts (e.g., case-insensitive collisions)
- Handling of unsupported media types (e.g., music in Plex)
- Saving plans to JSON files and verifying output
- Output directory creation and file existence checks
- Backward compatibility and cross-platform correctness (see PLANNING.md)

Rationale:
- Ensures robust, cross-platform plan generation and output for all supported platforms and file systems
- Validates handling of edge cases, error conditions, and output artifacts for user safety and reliability
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Never

import pytest
from _pytest.monkeypatch import MonkeyPatch

from namegnome.core.planner import create_rename_plan, save_plan
from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
from namegnome.rules.base import RuleSetConfig
from namegnome.rules.plex import PlexRuleSet


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def scan_result(tmp_path: Path) -> ScanResult:
    """Create a sample scan result with test files using platform-appropriate absolute paths."""
    # Create some test files
    tv_file = tmp_path / "Breaking Bad S01E01.mp4"
    tv_file.write_bytes(b"dummy content")
    movie_file = tmp_path / "Inception (2010).mp4"
    movie_file.write_bytes(b"dummy content")
    music_file = tmp_path / "song.mp3"
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
        files=media_files,
        root_dir=tmp_path.absolute(),
        media_types=[MediaType.TV, MediaType.MOVIE, MediaType.MUSIC],
        platform="plex",
        # Backward compatibility fields
        total_files=3,
        skipped_files=0,
        by_media_type={
            MediaType.TV: 1,
            MediaType.MOVIE: 1,
            MediaType.MUSIC: 1,
        },
        scan_duration_seconds=0.1,
    )


class TestCreateRenamePlan:
    """Tests for the create_rename_plan function.

    Covers plan creation from scan results, conflict detection, and handling of unsupported types.
    Ensures correct plan structure for downstream apply/undo logic.
    """

    def test_create_plan_with_plex_rules(self, scan_result: ScanResult) -> None:
        """Test creating a plan with Plex rules.

        Scenario:
        - Creates a plan from a scan result using the Plex rule set.
        - Asserts that plan properties, item counts, and destination paths are correct.
        - Ensures only supported media types are included in the plan.
        """
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
        tv_item = next(
            item for item in plan.items if item.media_file.media_type == MediaType.TV
        )
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
        """Test that conflicts are detected correctly.

        Scenario:
        - Two files that would map to the same destination (case-insensitive) are included in the scan.
        - Asserts that at least one plan item is marked as a conflict.
        - Ensures conflict detection logic is robust to platform quirks.
        """
        # Create two files that would map to the same destination (same name, just different case)
        file1 = temp_dir / "Show.S01E01.mp4"
        file2 = temp_dir / "show.s01e01.mp4"
        file1.write_bytes(b"dummy content")
        file2.write_bytes(b"dummy content")

        # Create media files
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

        # Create scan result with these files
        scan_result = ScanResult(
            files=media_files,
            root_dir=temp_dir.absolute(),
            media_types=[MediaType.TV],
            platform="plex",
            # Backward compatibility fields
            total_files=2,
            skipped_files=0,
            by_media_type={MediaType.TV: 2},
            scan_duration_seconds=0.1,
        )

        # Create a rename plan
        rule_set = PlexRuleSet()  # Plex rule set
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Check that conflicts were detected
        conflict_statuses = [item.status == PlanStatus.CONFLICT for item in plan.items]
        assert any(conflict_statuses)

    def test_handle_unsupported_media_type(self, scan_result: ScanResult) -> None:
        """Test handling of unsupported media types.

        Scenario:
        - Music files are present in the scan result but not supported by the Plex rule set.
        - Asserts that music files are skipped in the plan.
        - Ensures unsupported types do not cause errors or incorrect plan items.
        """
        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="test-plan",
            platform="plex",
        )

        # Music files should be skipped (not in plan items)
        assert len(plan.items) == 2
        assert not any(
            item.media_file.media_type == MediaType.MUSIC for item in plan.items
        )

    def test_anthology_episode_splitter_e01_dash_e02(
        self, temp_dir: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Test anthology episode splitting for E01-E02 pattern using LLM assistance."""
        import datetime

        from namegnome.core.planner import create_rename_plan
        from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
        from namegnome.rules.plex import PlexRuleSet

        anthology_file = temp_dir / "Show - E01-E02.mkv"
        anthology_file.write_bytes(b"dummy content")
        media_file = MediaFile(
            path=anthology_file.absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.datetime.now(),
        )
        scan_result = ScanResult(
            files=[media_file],
            root_dir=temp_dir.absolute(),
            media_types=[MediaType.TV],
            platform="plex",
            total_files=1,
            skipped_files=0,
            by_media_type={MediaType.TV: 1},
            scan_duration_seconds=0.1,
        )

        def mock_split_anthology(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
            return [
                {"episode": "E01", "title": "Episode One"},
                {"episode": "E02", "title": "Episode Two"},
            ]

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology", mock_split_anthology
        )

        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-e01e02",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )

        episodes = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(episodes) == 2
        assert {str(item.media_file.episode) for item in episodes} == {"E01", "E02"}
        assert {item.media_file.title for item in episodes} == {
            "Episode One",
            "Episode Two",
        }
        for item in episodes:
            assert item.status == PlanStatus.PENDING

        # Malformed LLM response triggers MANUAL flag
        def mock_split_anthology_malformed(*args: Any, **kwargs: Any) -> Never:
            raise ValueError("Malformed LLM JSON")

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology",
            mock_split_anthology_malformed,
        )
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-e01e02-malformed",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )
        manual_items = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(manual_items) == 1
        assert manual_items[0].status == PlanStatus.MANUAL
        assert "Malformed LLM JSON" in (manual_items[0].manual_reason or "")

    def test_anthology_episode_splitter_1x01_dash_1x02(
        self, temp_dir: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Test anthology episode splitting for 1x01-1x02 pattern using LLM assistance."""
        import datetime

        from namegnome.core.planner import create_rename_plan
        from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
        from namegnome.rules.plex import PlexRuleSet

        anthology_file = temp_dir / "Show 1x01-1x02.mkv"
        anthology_file.write_bytes(b"dummy content")
        media_file = MediaFile(
            path=anthology_file.absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.datetime.now(),
        )
        scan_result = ScanResult(
            files=[media_file],
            root_dir=temp_dir.absolute(),
            media_types=[MediaType.TV],
            platform="plex",
            total_files=1,
            skipped_files=0,
            by_media_type={MediaType.TV: 1},
            scan_duration_seconds=0.1,
        )

        def mock_split_anthology(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
            return [
                {"episode": "1x01", "title": "Episode One"},
                {"episode": "1x02", "title": "Episode Two"},
            ]

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology", mock_split_anthology
        )

        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-1x01-1x02",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )

        episodes = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(episodes) == 2
        assert {str(item.media_file.episode) for item in episodes} == {"1x01", "1x02"}
        assert {item.media_file.title for item in episodes} == {
            "Episode One",
            "Episode Two",
        }
        for item in episodes:
            assert item.status == PlanStatus.PENDING

        # Malformed LLM response triggers MANUAL flag
        def mock_split_anthology_malformed(*args: Any, **kwargs: Any) -> Never:
            raise ValueError("Malformed LLM JSON")

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology",
            mock_split_anthology_malformed,
        )
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-1x01-1x02-malformed",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )
        manual_items = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(manual_items) == 1
        assert manual_items[0].status == PlanStatus.MANUAL
        assert "Malformed LLM JSON" in (manual_items[0].manual_reason or "")

    def test_anthology_splitter_paw_patrol_real_filename(
        self, temp_dir: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Test anthology splitting for a real Paw Patrol anthology filename."""
        import datetime

        from namegnome.core.planner import create_rename_plan
        from namegnome.models.core import MediaFile, MediaType, PlanStatus, ScanResult
        from namegnome.rules.plex import PlexRuleSet

        filename = (
            "Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4"
        )
        anthology_file = temp_dir / filename
        anthology_file.write_bytes(b"dummy content")
        media_file = MediaFile(
            path=anthology_file.absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.datetime.now(),
        )
        scan_result = ScanResult(
            files=[media_file],
            root_dir=temp_dir.absolute(),
            media_types=[MediaType.TV],
            platform="plex",
            total_files=1,
            skipped_files=0,
            by_media_type={MediaType.TV: 1},
            scan_duration_seconds=0.1,
        )

        def mock_split_anthology(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
            return [
                {"episode": "S01E01", "title": "Pups And The Kitty Tastrophe"},
                {"episode": "S01E02", "title": "Pups Save A Train"},
            ]

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology", mock_split_anthology
        )

        rule_set = PlexRuleSet()
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-pawpatrol",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )

        episodes = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(episodes) == 2
        assert {str(item.media_file.episode) for item in episodes} == {
            "S01E01",
            "S01E02",
        }
        assert {item.media_file.title for item in episodes} == {
            "Pups And The Kitty Tastrophe",
            "Pups Save A Train",
        }
        for item in episodes:
            assert item.status == PlanStatus.PENDING

        # Malformed LLM response triggers MANUAL flag
        def mock_split_anthology_malformed(*args: Any, **kwargs: Any) -> Never:
            raise ValueError("Malformed LLM JSON")

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology",
            mock_split_anthology_malformed,
        )
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=rule_set,
            plan_id="anthology-test-plan-pawpatrol-malformed",
            platform="plex",
            config=RuleSetConfig(anthology=True),
        )
        manual_items = [
            item
            for item in plan.items
            if item.media_file.path == anthology_file.absolute()
        ]
        assert len(manual_items) == 1
        assert manual_items[0].status == PlanStatus.MANUAL
        assert "Malformed LLM JSON" in (manual_items[0].manual_reason or "")

    def test_llm_confidence_manual_flag(
        self, temp_dir: Path, monkeypatch: MonkeyPatch
    ) -> None:
        """Test that LLM confidence below threshold sets manual flag and reason."""
        # Simulate a TV file that would trigger LLM logic
        tv_file = temp_dir / "Show.S01E01.mp4"
        tv_file.write_bytes(b"dummy content")
        media_file = MediaFile(
            path=tv_file.absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        scan_result = ScanResult(
            files=[media_file],
            root_dir=temp_dir.absolute(),
            media_types=[MediaType.TV],
            platform="plex",
            total_files=1,
            skipped_files=0,
            by_media_type={MediaType.TV: 1},
            scan_duration_seconds=0.1,
        )

        # Patch split_anthology to return a segment with low confidence
        def mock_split_anthology_low_conf(
            *args: Any, **kwargs: Any
        ) -> list[dict[str, Any]]:
            return [{"episode": "S01E01", "title": "Test Title", "confidence": 0.5}]

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology",
            mock_split_anthology_low_conf,
        )
        from namegnome.rules.base import RuleSetConfig
        from namegnome.rules.plex import PlexRuleSet

        config = RuleSetConfig(anthology=True)
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=PlexRuleSet(),
            plan_id="test-plan",
            platform="plex",
            config=config,
        )
        assert len(plan.items) == 1
        item = plan.items[0]
        assert item.manual is True
        assert item.manual_reason is not None
        assert "confidence" in item.manual_reason

        # Now patch split_anthology to return high confidence
        def mock_split_anthology_high_conf(
            *args: Any, **kwargs: Any
        ) -> list[dict[str, Any]]:
            return [{"episode": "S01E01", "title": "Test Title", "confidence": 0.95}]

        monkeypatch.setattr(
            "namegnome.llm.prompt_orchestrator.split_anthology",
            mock_split_anthology_high_conf,
        )
        plan = create_rename_plan(
            scan_result=scan_result,
            rule_set=PlexRuleSet(),
            plan_id="test-plan",
            platform="plex",
            config=config,
        )
        assert len(plan.items) == 1
        item = plan.items[0]
        assert item.manual is False
        assert item.manual_reason is None


class TestSavePlan:
    """Tests for the save_plan function.

    Covers saving plans to JSON files, output directory creation, and file existence checks.
    Ensures output artifacts are correct and compatible with downstream tools.
    """

    def test_save_plan_to_json(self, scan_result: ScanResult, temp_dir: Path) -> None:
        """Test saving a plan to a JSON file.

        Scenario:
        - Creates a plan and saves it to a JSON file in a specified output directory.
        - Asserts that the file exists, has the correct name, and contains valid JSON.
        - Ensures output is compatible with downstream tools and manual inspection.
        """
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

    def test_create_output_directory(
        self, scan_result: ScanResult, temp_dir: Path
    ) -> None:
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
