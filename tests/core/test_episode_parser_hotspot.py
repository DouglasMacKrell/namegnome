"""Test episode parser functionality for standard TV filename patterns.

This test file specifically tests the core issue discovered in Sprint 1.6-m volume testing:
Files like "Paw Patrol-S01E01-Title.mp4" were returning season: null, episode: null.
"""

from pathlib import Path
from datetime import datetime

from namegnome.models.core import MediaFile, MediaType
from namegnome.core.tv_planner import _parse_show_season_from_filename
from namegnome.core.episode_parser import _extract_show_season_year
from namegnome.rules.base import RuleSetConfig


class TestStandardTVFilenamePatterns:
    """Test parsing of standard TV filename patterns from our test fixtures."""

    def test_parse_show_season_from_filename_paw_patrol(self):
        """Test parsing Paw Patrol filename pattern."""
        show, season = _parse_show_season_from_filename(
            "Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4"
        )
        assert show == "Paw Patrol"
        assert season == 1

    def test_parse_show_season_from_filename_danger_mouse(self):
        """Test parsing Danger Mouse filename pattern."""
        show, season = _parse_show_season_from_filename(
            "Danger Mouse 2015-S01E01-Danger Mouse Begins Again.mp4"
        )
        assert show == "Danger Mouse 2015"
        assert season == 1

    def test_parse_show_season_from_filename_firebuds(self):
        """Test parsing Firebuds filename pattern."""
        show, season = _parse_show_season_from_filename(
            "Firebuds-S01E01-Car In A Tree Dalmatian Day.mp4"
        )
        assert show == "Firebuds"
        assert season == 1

    def test_parse_show_season_from_filename_harvey_girls_special_chars(self):
        """Test parsing Harvey Girls Forever filename with special characters."""
        show, season = _parse_show_season_from_filename(
            "Harvey Girls Forever! - S01E01 - War and Trees WEBDL-1080p.mkv"
        )
        assert show is not None  # Should extract some show name
        assert season == 1

    def test_parse_show_season_from_filename_martha_speaks(self):
        """Test parsing Martha Speaks filename pattern."""
        show, season = _parse_show_season_from_filename(
            "Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4"
        )
        assert show == "Martha Speaks"
        assert season == 1

    def test_parse_show_season_from_filename_octonauts(self):
        """Test parsing The Octonauts filename pattern."""
        show, season = _parse_show_season_from_filename(
            "The Octonauts-S01E01-The Whale Shark.mp4"
        )
        assert show == "The Octonauts"
        assert season == 1

    def test_parse_show_season_from_filename_high_episode_numbers(self):
        """Test parsing filenames with high episode numbers (2+ digits)."""
        show, season = _parse_show_season_from_filename(
            "Danger Mouse 2015-S01E50-Mouse Rise.mp4"
        )
        assert show == "Danger Mouse 2015"
        assert season == 1

    def test_parse_show_season_from_filename_high_season_numbers(self):
        """Test parsing filenames with high season numbers (2+ digits)."""
        show, season = _parse_show_season_from_filename(
            "Paw Patrol-S11E01-Rescue Wheels Pups Save The Teetering Tower.mp4"
        )
        assert show == "Paw Patrol"
        assert season == 11

    def test_parse_show_season_from_filename_edge_cases(self):
        """Test parsing edge cases that should return None."""
        # Missing season
        show, season = _parse_show_season_from_filename("Show-E01-Title.mp4")
        assert show is None
        assert season is None

        # Missing episode
        show, season = _parse_show_season_from_filename("Show-S01-Title.mp4")
        assert show is None
        assert season is None

        # No pattern at all
        show, season = _parse_show_season_from_filename("Random_File_Name.mp4")
        assert show is None
        assert season is None

    def test_extract_show_season_year_with_media_file(self, tmp_path):
        """Test _extract_show_season_year function with MediaFile objects."""
        # Create a mock media file
        media_file = MediaFile(
            path=tmp_path / "Paw Patrol-S01E01-Title.mp4",
            size=1234,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        config = RuleSetConfig()

        show, season, year = _extract_show_season_year(media_file, config)
        assert show == "Paw Patrol"
        assert season == 1
        assert year is None  # No year in this filename

    def test_extract_show_season_year_with_year(self, tmp_path):
        """Test _extract_show_season_year function with year in show name."""
        media_file = MediaFile(
            path=tmp_path / "Danger Mouse 2015-S01E01-Title.mp4",
            size=1234,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        config = RuleSetConfig()

        show, season, year = _extract_show_season_year(media_file, config)
        assert show == "Danger Mouse"  # Year should be extracted
        assert season == 1
        assert year == 2015

    def test_parse_show_season_from_filename_all_fixture_patterns(self):
        """Test all the 6 hand-selected show filename patterns from our fixtures."""
        test_cases = [
            # Paw Patrol
            (
                "Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4",
                "Paw Patrol",
                1,
            ),
            # Danger Mouse 2015
            (
                "Danger Mouse 2015-S01E01-Danger Mouse Begins Again.mp4",
                "Danger Mouse 2015",
                1,
            ),
            # Firebuds
            ("Firebuds-S01E01-Car In A Tree Dalmatian Day.mp4", "Firebuds", 1),
            # Martha Speaks
            (
                "Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4",
                "Martha Speaks",
                1,
            ),
            # The Octonauts
            ("The Octonauts-S01E01-The Whale Shark.mp4", "The Octonauts", 1),
            # High episode numbers
            (
                "Paw Patrol-S11E26-Pups Save The Space Kitty Pups Save The Sea Sponges.mp4",
                "Paw Patrol",
                11,
            ),
        ]

        for filename, expected_show, expected_season in test_cases:
            show, season = _parse_show_season_from_filename(filename)
            assert show == expected_show, (
                f"Failed to parse show from {filename}: got {show}, expected {expected_show}"
            )
            assert season == expected_season, (
                f"Failed to parse season from {filename}: got {season}, expected {expected_season}"
            )

    def test_harvey_girls_special_format_parsing(self):
        """Test Harvey Girls Forever special format with spaces and exclamation marks."""
        # This is a more challenging pattern: "Harvey Girls Forever! - S01E01 - War and Trees WEBDL-1080p.mkv"
        show, season = _parse_show_season_from_filename(
            "Harvey Girls Forever! - S01E01 - War and Trees WEBDL-1080p.mkv"
        )
        # The current regex should handle this with the second pattern that allows spaces
        assert show is not None  # Should extract some show name
        assert season == 1


class TestMediaFilePopulationDuringScanning:
    """Test that MediaFile objects are properly populated during scanning, not just planning."""

    def test_mediafile_season_episode_populated_during_scan(self):
        """Test that scanning TV files populates season/episode fields in MediaFile objects.

        This test reproduces the issue found in Sprint 1.6-m volume testing:
        MediaFile objects had season: null, episode: null even for parseable filenames.
        """
        from namegnome.core.scanner import _create_media_file
        import tempfile
        import os

        # Create a temporary file to test with realistic TV filename pattern
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Rename to match Paw Patrol pattern from volume test failures
            test_path = (
                temp_path.parent
                / "Paw Patrol-S04E26-Sea Patrol Pups Save Puplantis.mp4"
            )
            temp_path.rename(test_path)

            # Create MediaFile object using scanner's method
            errors = []
            media_file, media_type = _create_media_file(
                test_path, verify_hash=False, errors=errors
            )

            # These assertions should pass but currently fail due to Sprint 1.7.1 issue
            assert media_file.season == 4, f"Expected season 4, got {media_file.season}"
            assert media_file.episode == 26, (
                f"Expected episode 26, got {media_file.episode}"
            )
            assert media_file.title == "Paw Patrol", (
                f"Expected 'Paw Patrol', got {media_file.title}"
            )
            assert media_file.episode_title == "Sea Patrol Pups Save Puplantis", (
                f"Expected episode title, got {media_file.episode_title}"
            )

        finally:
            # Clean up
            if test_path.exists():
                os.unlink(test_path)

    def test_mediafile_various_tv_patterns_populated_during_scan(self):
        """Test various TV filename patterns get properly parsed during scanning."""
        from namegnome.core.scanner import _create_media_file
        import tempfile
        import os

        test_cases = [
            (
                "Danger Mouse 2015-S01E01-Danger Mouse Begins Again.mp4",
                1,
                1,
                "Danger Mouse 2015",
                "Danger Mouse Begins Again",
            ),
            (
                "Harvey Girls Forever-S02E12-Too Cool For School Sheriff For A Day.mp4",
                2,
                12,
                "Harvey Girls Forever",
                "Too Cool For School Sheriff For A Day",
            ),
            (
                "Martha Speaks-S03E05-Martha'S Dirty Habit.mp4",
                3,
                5,
                "Martha Speaks",
                "Martha'S Dirty Habit",
            ),
        ]

        for (
            filename,
            expected_season,
            expected_episode,
            expected_title,
            expected_episode_title,
        ) in test_cases:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            try:
                # Rename to match test pattern
                test_path = temp_path.parent / filename
                temp_path.rename(test_path)

                # Create MediaFile object using scanner's method
                errors = []
                media_file, media_type = _create_media_file(
                    test_path, verify_hash=False, errors=errors
                )

                # These should all be populated during scanning
                assert media_file.season == expected_season, (
                    f"File {filename}: Expected season {expected_season}, got {media_file.season}"
                )
                assert media_file.episode == expected_episode, (
                    f"File {filename}: Expected episode {expected_episode}, got {media_file.episode}"
                )
                assert media_file.title == expected_title, (
                    f"File {filename}: Expected title '{expected_title}', got '{media_file.title}'"
                )
                assert media_file.episode_title == expected_episode_title, (
                    f"File {filename}: Expected episode title '{expected_episode_title}', got '{media_file.episode_title}'"
                )

            finally:
                # Clean up
                if test_path.exists():
                    os.unlink(test_path)
