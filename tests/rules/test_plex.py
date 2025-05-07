"""Tests for the Plex rule set."""

from datetime import datetime
from pathlib import Path

import pytest
from namegnome.models.core import MediaFile, MediaType
from namegnome.rules.plex import PlexRuleSet


class TestPlexRuleSet:
    """Tests for the PlexRuleSet class."""

    @pytest.fixture
    def rule_set(self) -> PlexRuleSet:
        """Create a PlexRuleSet for testing."""
        return PlexRuleSet()

    def test_init(self, rule_set: PlexRuleSet) -> None:
        """Test initialization of the PlexRuleSet."""
        assert rule_set.platform_name == "plex"
        assert MediaType.TV in rule_set.supported_media_types
        assert MediaType.MOVIE in rule_set.supported_media_types
        assert MediaType.MUSIC not in rule_set.supported_media_types

    def test_supports_media_type(self, rule_set: PlexRuleSet) -> None:
        """Test the supports_media_type method."""
        assert rule_set.supports_media_type(MediaType.TV) is True
        assert rule_set.supports_media_type(MediaType.MOVIE) is True
        assert rule_set.supports_media_type(MediaType.MUSIC) is False
        assert rule_set.supports_media_type(MediaType.UNKNOWN) is False

    def test_tv_show_path_standard_format(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a standard TV show file format."""
        # Create a test media file
        media_file = MediaFile(
            path=Path("/test/Breaking Bad S01E05 Gray Matter.mp4").absolute(),
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

    def test_tv_show_path_with_dots(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a TV show file with dots instead of spaces."""
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
        """Test target path generation for a TV show file without an episode title."""
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
        """Test target path generation for an irregular TV show file format."""
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
        """Test target path generation for a movie file with year."""
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
        expected = Path("/media/Movies/Inception (2010)/Inception (2010).mp4").absolute()
        assert target == expected

    def test_movie_path_no_year(self, rule_set: PlexRuleSet) -> None:
        """Test target path generation for a movie file without a year."""
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
        """Test target path generation for a movie file with dots instead of spaces."""
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
        expected = Path("/media/Movies/The Matrix (1999)/The Matrix (1999).mp4").absolute()
        assert target == expected

    def test_unsupported_media_type(self, rule_set: PlexRuleSet) -> None:
        """Test error handling for unsupported media types."""
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
