"""Tests for the Plex rule set.

This test suite covers:
- Target path generation for TV and movie files using Plex naming conventions
- Handling of standard, dotted, missing-title, and irregular file formats
- Error handling for unsupported media types
- Ensures robust, cross-platform path generation and error handling (see PLANNING.md)

Rationale:
- Guarantees that renaming logic produces Plex-compatible paths for all supported scenarios
- Validates edge cases, fallback logic, and error handling for user safety and reliability
"""

from datetime import datetime
from pathlib import Path

import pytest

from namegnome.models.core import MediaFile, MediaType
from namegnome.rules.plex import PlexRuleSet


class TestPlexRuleSet:
    """Tests for the PlexRuleSet class.

    Covers TV/movie path generation, edge cases, and error handling for Plex platform logic.
    Ensures all supported and unsupported scenarios are handled as expected.
    """

    @pytest.fixture
    def rule_set(self) -> PlexRuleSet:
        """Create a PlexRuleSet for testing."""
        return PlexRuleSet()

    def test_init(self, rule_set: PlexRuleSet) -> None:
        """Test initialization of the PlexRuleSet.

        Scenario:
        - Ensures platform name and supported media types are set correctly.
        - Validates that music and unknown types are not supported.
        """
        assert rule_set.platform_name == "plex"
        assert MediaType.TV in rule_set.supported_media_types
        assert MediaType.MOVIE in rule_set.supported_media_types
        assert MediaType.MUSIC not in rule_set.supported_media_types

    def test_supports_media_type(self, rule_set: PlexRuleSet) -> None:
        """Test the supports_media_type method.

        Scenario:
        - Checks that TV and movie types are supported, music and unknown are not.
        - Ensures correct filtering for downstream planning logic.
        """
        assert rule_set.supports_media_type(MediaType.TV) is True
        assert rule_set.supports_media_type(MediaType.MOVIE) is True
        assert rule_set.supports_media_type(MediaType.MUSIC) is False
        assert rule_set.supports_media_type(MediaType.UNKNOWN) is False

    def test_tv_show_path_standard_format(
        self, rule_set: PlexRuleSet, tmp_path: Path
    ) -> None:
        """Test target path generation for a standard TV show file format.

        Scenario:
        - TV show file with standard SxxExx and episode title format.
        - Ensures output path matches Plex convention.
        """
        # Create a test media file
        media_file = MediaFile(
            path=tmp_path / "Breaking Bad S01E05 Gray Matter.mp4",
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )
        # Set a base directory for consistent testing
        base_dir = tmp_path
        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)
        # Check that the path follows Plex conventions
        expected = (
            base_dir
            / "TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E05 - Gray Matter.mp4"
        )
        assert target == expected

    def test_tv_show_path_with_dots(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a TV show file with dots instead of spaces.

        Scenario:
        - TV show file with dots in the filename.
        - Ensures output path normalizes to spaces and matches Plex convention.
        """
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/Breaking.Bad.S01E05.Gray.Matter.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)

        # Check that the path follows Plex conventions
        expected = Path(
            "/media/TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E05 - Gray Matter.mp4"
        ).absolute()
        assert target == expected

    def test_tv_show_path_no_episode_title(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a TV show file without an episode title.

        Scenario:
        - TV show file missing an episode title.
        - Ensures fallback to 'Unknown Episode' in output path.
        """
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/Breaking Bad S01E05.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)

        # Check that the path follows Plex conventions
        expected = Path(
            "/media/TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E05 - Unknown Episode.mp4"
        ).absolute()
        assert target == expected

    def test_tv_show_path_irregular_format(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for an irregular TV show file format.

        Scenario:
        - TV show file with an unusual name that doesn't match standard patterns.
        - Ensures fallback to 'Unknown Show' and 'Unknown Episode' in output path.
        """
        # Create a test media file with an unusual name
        media_file = MediaFile(
            path=Path("/test/BreakingBad_105.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path - should use defaults when pattern doesn't match
        target = rule_set.target_path(media_file, base_dir)

        # Check that a default path is created
        expected = Path(
            "/media/TV Shows/Unknown Show/Season 01/Unknown Show - S01E01 - Unknown Episode.mp4"
        ).absolute()
        assert target == expected

    def test_movie_path_with_year(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a movie file with year.

        Scenario:
        - Movie file with year in the filename.
        - Ensures output path includes year and matches Plex convention.
        """
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/Inception (2010).mp4").absolute(),
            size=1024,
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)

        # Check that the path follows Plex conventions
        expected = Path(
            "/media/Movies/Inception (2010)/Inception (2010).mp4"
        ).absolute()
        assert target == expected

    def test_movie_path_no_year(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a movie file without a year.

        Scenario:
        - Movie file without year in the filename.
        - Ensures output path omits year and matches Plex convention.
        """
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/Inception.mp4").absolute(),
            size=1024,
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)

        # Check that the path follows Plex conventions
        expected = Path("/media/Movies/Inception/Inception.mp4").absolute()
        assert target == expected

    def test_movie_path_with_dots(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a movie file with dots instead of spaces.

        Scenario:
        - Movie file with dots in the filename.
        - Ensures output path normalizes to spaces and includes year if present.
        """
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/The.Matrix.1999.mp4").absolute(),
            size=1024,
            media_type=MediaType.MOVIE,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Generate the target path
        target = rule_set.target_path(media_file, base_dir)

        # Expected path should have spaces and follow Plex convention with year
        expected = Path(
            "/media/Movies/The Matrix (1999)/The Matrix (1999).mp4"
        ).absolute()
        assert target == expected

    def test_unsupported_media_type(self, rule_set: PlexRuleSet) -> None:
        """Test error handling for unsupported media types.

        Scenario:
        - Media file with unsupported type (e.g., music).
        - Ensures ValueError is raised for unsupported types.
        """
        # Create a test media file with an unsupported type
        media_file = MediaFile(
            path=Path("/test/song.mp3").absolute(),
            size=1024,
            media_type=MediaType.MUSIC,
            modified_date=datetime.now(),
        )

        # Set a base directory for consistent testing
        base_dir = Path("/media").absolute()

        # Should raise ValueError for unsupported media type
        with pytest.raises(ValueError):
            rule_set.target_path(media_file, base_dir)
