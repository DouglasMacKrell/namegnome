"""Tests for the namegnome scan command."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import typer
from pydantic import HttpUrl
from typer.testing import CliRunner
from typing_extensions import Literal

from namegnome.cli.commands import app
from namegnome.metadata.models import ArtworkImage
from namegnome.models.core import MediaFile, MediaType, ScanResult
from namegnome.models.plan import RenamePlan


@pytest.fixture
def runner() -> CliRunner:
    """Get a Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def app_fixture() -> typer.Typer:
    """Create a patched version of the app with the mock fixtures."""
    return app


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_scan_result(tmp_path: Path) -> ScanResult:
    """Create a mock scan result with platform-appropriate absolute paths."""
    base_dir = tmp_path / "test"
    base_dir.mkdir(parents=True, exist_ok=True)
    test_file1 = base_dir / "file1.mp4"
    test_file2 = base_dir / "file2.mkv"
    test_file1.touch()
    test_file2.touch()
    return ScanResult(
        files=[
            MediaFile(
                path=test_file1,
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            ),
            MediaFile(
                path=test_file2,
                size=2048,
                media_type=MediaType.MOVIE,
                modified_date=datetime.now(),
            ),
        ],
        root_dir=base_dir,
        media_types=[MediaType.TV, MediaType.MOVIE],
        platform="plex",
    )


@pytest.fixture(autouse=True)
def mock_scan_directory(
    mock_scan_result: ScanResult,
) -> Generator[MagicMock, None, None]:
    """Mock the scan_directory function.

    This fixture uses the autouse=True parameter to ensure it's automatically applied
    to all tests in this module, and it patches both the direct import and module import.
    """
    # First patch the direct import in namegnome.cli.commands
    with patch("namegnome.cli.commands.scan_directory") as mock_cli_scan:
        # Then patch the actual function in its module
        with patch("namegnome.core.scanner.scan_directory") as mock_core_scan:
            # Set up both mocks to return the same result
            mock_cli_scan.return_value = mock_scan_result
            mock_core_scan.return_value = mock_scan_result

            # Yield the CLI version which is what our tests will use
            yield mock_cli_scan


@pytest.fixture
def mock_create_rename_plan() -> Generator[MagicMock, None, None]:
    """Mock the create_rename_plan function."""
    with patch("namegnome.cli.commands.create_rename_plan") as mock_plan:
        # Use platform-agnostic absolute path
        base_dir = Path.cwd() / "test"

        # Create a fake rename plan
        mock_plan_obj = RenamePlan(
            id="test_plan",
            created_at=datetime.now(),
            root_dir=base_dir,
            platform="plex",
            items=[],  # Empty items list so no manual items
            media_types=[MediaType.TV, MediaType.MOVIE],
            metadata_providers=[],
            llm_model=None,
        )
        mock_plan.return_value = mock_plan_obj
        yield mock_plan


@pytest.fixture
def mock_storage() -> Generator[MagicMock, None, None]:
    """Mock the save_plan function."""
    with patch("namegnome.cli.commands.save_plan") as mock_save_plan:
        # Return a UUID as the function would
        mock_save_plan.return_value = "12345678-1234-1234-1234-123456789012"
        yield mock_save_plan


@pytest.fixture
def mock_render_diff() -> Generator[MagicMock, None, None]:
    """Mock the render_diff function."""
    with patch("namegnome.cli.commands.render_diff") as mock_render:
        yield mock_render


@pytest.fixture
def mock_console_log() -> Generator[MagicMock, None, None]:
    """Mock the console.log method."""
    with patch("namegnome.cli.commands.console.log") as mock_log:
        yield mock_log


@pytest.fixture
def mock_console() -> Generator[MagicMock, None, None]:
    """Mock the entire console creation."""
    with patch("namegnome.cli.commands.Console") as mock_console_class:
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        yield mock_console


@pytest.fixture
def mock_stdout_write() -> Generator[MagicMock, None, None]:
    """Mock sys.stdout.write method."""
    with patch("sys.stdout.write") as mock_write:
        yield mock_write


@pytest.fixture
def mock_validate_media_type() -> Generator[MagicMock, None, None]:
    """Mock the validate_media_type function."""
    with patch("namegnome.cli.commands.validate_media_type") as mock_validate:
        mock_validate.side_effect = (
            lambda x: MediaType(x.lower())
            if x.lower() in [m.value for m in MediaType]
            else typer.BadParameter(f"Invalid media type: {x}")
        )
        yield mock_validate


@pytest.fixture
def temp_dir_with_media() -> Generator[Path, None, None]:
    """Create a temporary directory with a fake media file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a fake media file
        media_path = Path(temp_dir) / "test.mp4"
        with open(media_path, "wb") as f:
            f.write(b"FAKE MP4 DATA")

        yield Path(temp_dir)


def test_scan_command_no_media_type() -> None:
    """Test that scan command requires at least one media type."""
    runner = CliRunner()
    result = runner.invoke(app, ["scan", ".", "--no-color"])
    assert result.exit_code != 0
    assert (
        "At least one media type must be specified" in result.output
        or "Missing option" in result.output
        or "Usage:" in result.output
    )


def test_scan_command_invalid_media_type() -> None:
    """Test that scan command validates media types."""
    runner = CliRunner()
    result = runner.invoke(app, ["scan", ".", "--media-type", "invalid", "--no-color"])
    assert result.exit_code != 0
    assert (
        "Error: Invalid media type. Must be one of: tv, movie, music" in result.output
    )


class DummyContext:
    """Dummy context manager for patching rich status/progress in tests."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize DummyContext."""
        pass

    def __enter__(self) -> "DummyContext":
        """Enter the context manager."""
        return self

    def __exit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> Literal[False]:
        """Exit the context manager."""
        return False


def test_scan_command_with_artwork_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test scan command with --artwork flag triggers artwork download and file creation."""
    monkeypatch.setenv("FANARTTV_API_KEY", "dummykey")
    runner = CliRunner()
    with runner.isolated_filesystem():
        movie_file = Path("movie.mp4")
        movie_file.touch()
        tmdbid = "12345"
        artwork_dir = Path(".namegnome") / "artwork" / tmdbid
        poster_path = artwork_dir / "poster.jpg"

        async def fake_fetch_fanart_poster(meta: object, dir: Path) -> ArtworkImage:
            dir.mkdir(parents=True, exist_ok=True)
            (dir / "poster.jpg").write_bytes(b"FAKEIMAGE")
            from namegnome.metadata.models import ArtworkImage

            return ArtworkImage(
                url=HttpUrl("http://img2.jpg/"),
                width=1000,
                height=1500,
                type="poster",
                provider="fanart",
            )

        scan_result = ScanResult(
            files=[
                MediaFile(
                    path=movie_file.resolve(),
                    size=1234,
                    media_type=MediaType.MOVIE,
                    modified_date=datetime.now(),
                )
            ],
            root_dir=Path("."),
            media_types=[MediaType.MOVIE],
            platform="plex",
        )
        with (
            patch(
                "namegnome.cli.commands.fetch_fanart_poster", fake_fetch_fanart_poster
            ),
            patch("namegnome.cli.commands.scan_directory", return_value=scan_result),
            patch("rich.console.Console.status", DummyContext),
            patch("rich.progress.Progress", DummyContext),
        ):
            from namegnome.cli.commands import app

            result = runner.invoke(
                app,
                ["scan", ".", "--media-type", "movie", "--artwork"],
            )
        assert result.exit_code == 0
        assert poster_path.exists()
        assert poster_path.read_bytes() == b"FAKEIMAGE"
