"""Tests for the directory scanner module."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from namegnome.core.scanner import guess_media_type, scan_directory
from namegnome.models.core import MediaType


class TestGuessMediaType:
    """Tests for the guess_media_type function."""

    def test_tv_show_pattern(self) -> None:
        """Test that TV show patterns are detected correctly."""
        # S01E01 pattern
        assert guess_media_type(Path("/tmp/Breaking Bad S01E01.mp4")) == MediaType.TV
        # 1x01 pattern
        assert guess_media_type(Path("/tmp/Breaking Bad 1x01.mkv")) == MediaType.TV
        # season/episode pattern
        assert (
            guess_media_type(Path("/tmp/Breaking Bad Season 1 Episode 1.avi"))
            == MediaType.TV
        )

    def test_directory_hints(self) -> None:
        """Test that directory hints are used to guess media type."""
        # TV show in TV directory
        assert (
            guess_media_type(Path("/media/TV Shows/Breaking Bad/episode.mp4"))
            == MediaType.TV
        )
        # Movie in Movies directory
        assert guess_media_type(Path("/media/Movies/Inception.mp4")) == MediaType.MOVIE
        # Music in Music directory
        assert guess_media_type(Path("/media/Music/song.mp3")) == MediaType.MUSIC

    def test_unknown_type(self) -> None:
        """Test that unknown media types are classified as UNKNOWN."""
        # Unknown extension
        assert guess_media_type(Path("/tmp/somefile.txt")) == MediaType.UNKNOWN
        # No clear hints in the path
        assert guess_media_type(Path("/tmp/random_video.mp4")) == MediaType.UNKNOWN


class TestScanDirectory:
    """Tests for the scan_directory function."""

    @pytest.fixture
    def temp_media_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory with media files for testing."""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())

        # Create TV show files
        tv_dir = temp_dir / "TV Shows"
        tv_dir.mkdir()
        (tv_dir / "Breaking Bad").mkdir()
        (tv_dir / "Breaking Bad" / "Season 01").mkdir()
        (tv_dir / "Breaking Bad" / "Season 01" / "Breaking Bad S01E01.mp4").touch()
        (tv_dir / "Breaking Bad" / "Season 01" / "Breaking Bad S01E02.mp4").touch()
        (
            tv_dir / "Breaking Bad" / "Season 01" / "Breaking Bad S01E01.srt"
        ).touch()  # Subtitle file
        (tv_dir / "The Office").mkdir()
        (tv_dir / "The Office" / "The Office 1x01.mkv").touch()

        # Create movie files
        movie_dir = temp_dir / "Movies"
        movie_dir.mkdir()
        (movie_dir / "Inception (2010)").mkdir()
        (movie_dir / "Inception (2010)" / "Inception (2010).mp4").touch()
        (movie_dir / "The Matrix (1999).mp4").touch()

        # Create music files
        music_dir = temp_dir / "Music"
        music_dir.mkdir()
        (music_dir / "Artist").mkdir()
        (music_dir / "Artist" / "Album").mkdir()
        (music_dir / "Artist" / "Album" / "01 - Track 1.mp3").touch()
        (music_dir / "Artist" / "Album" / "02 - Track 2.mp3").touch()
        (music_dir / "Artist" / "Album" / "cover.jpg").touch()  # Album art

        # Create a hidden directory with media
        hidden_dir = temp_dir / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "hidden_video.mp4").touch()

        # Create a file with non-ASCII name
        (tv_dir / "ユニコード文字.mp4").touch()

        # Create some other files
        (temp_dir / "document.txt").touch()
        (temp_dir / "image.jpg").touch()

        yield temp_dir

        # Clean up after the test
        shutil.rmtree(temp_dir)

    def test_scan_all_media_types(self, temp_media_dir: Path) -> None:
        """Test scanning for all media types."""
        result = scan_directory(temp_media_dir)

        # Check that we found all media files (8 in total: 4 TV, 2 movies, 2 music)
        assert len(result.media_files) == 8

        # Check type counts
        assert result.by_media_type[MediaType.TV] == 4  # Including the Unicode file
        assert result.by_media_type[MediaType.MOVIE] == 2
        assert result.by_media_type[MediaType.MUSIC] == 2

        # Check statistics
        assert result.total_files > 8  # Should include all files
        assert result.skipped_files > 0  # Should have skipped some files
        assert result.scan_duration_seconds > 0
        assert result.root_dir == temp_media_dir.absolute()
        assert not result.errors  # No errors should have occurred

    def test_scan_specific_media_type(self, temp_media_dir: Path) -> None:
        """Test scanning for a specific media type."""
        result = scan_directory(temp_media_dir, media_types=[MediaType.TV])

        # Should find only TV shows
        assert len(result.media_files) == 4
        assert result.by_media_type[MediaType.TV] == 4
        assert MediaType.MOVIE not in result.by_media_type
        assert MediaType.MUSIC not in result.by_media_type

    def test_scan_no_recursive(self, temp_media_dir: Path) -> None:
        """Test scanning without recursion."""
        result = scan_directory(temp_media_dir, recursive=False)

        # Should find no media files (all are in subdirectories)
        assert len(result.media_files) == 0

    def test_scan_include_hidden(self, temp_media_dir: Path) -> None:
        """Test scanning with hidden files and directories included."""
        result = scan_directory(temp_media_dir, include_hidden=True)

        # Should find the hidden video
        assert len(result.media_files) == 9  # 8 regular + 1 hidden

        # Check that the hidden video was found
        hidden_video_found = any(
            media_file.path.name == "hidden_video.mp4"
            for media_file in result.media_files
        )
        assert hidden_video_found

    def test_scan_nonexistent_directory(self) -> None:
        """Test scanning a directory that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            scan_directory(Path("/nonexistent"))

    def test_scan_not_a_directory(self, temp_media_dir: Path) -> None:
        """Test scanning a path that's not a directory."""
        file_path = temp_media_dir / "document.txt"
        with pytest.raises(ValueError):
            scan_directory(file_path)

    def test_non_ascii_filenames(self, temp_media_dir: Path) -> None:
        """Test scanning files with non-ASCII characters in the name."""
        result = scan_directory(temp_media_dir)

        # Check that the Unicode file was found
        unicode_file_found = any(
            "ユニコード文字" in str(media_file.path)
            for media_file in result.media_files
        )
        assert unicode_file_found
