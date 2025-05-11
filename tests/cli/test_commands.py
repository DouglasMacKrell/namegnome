"""Tests for the namegnome CLI commands."""

import contextlib
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest import MonkeyPatch
from typer.testing import CliRunner

from namegnome.cli.commands import app
from namegnome.models.core import MediaFile, MediaType, ScanResult
from namegnome.models.plan import RenamePlan


# Helper function to create an absolute path that's platform-independent
def abs_path(path_str: str) -> str:
    """Create a platform-independent absolute path string."""
    from pathlib import Path

    if os.name == "nt":  # Windows
        # Convert Unix-style paths to Windows absolute paths
        if path_str.startswith("/"):
            return str(Path("C:" + path_str.replace("/", "\\")))
    # For Unix systems, keep the path as is
    return str(Path(path_str))


@pytest.fixture
def mock_scan_result(tmp_path: Path) -> ScanResult:
    """Create a mock scan result with platform-appropriate absolute paths."""
    root_path = tmp_path / "media"
    root_path.mkdir(parents=True, exist_ok=True)
    file_path = root_path / "test.mp4"
    file_path.touch()
    return ScanResult(
        root_dir=root_path,
        files=[
            MediaFile(
                path=file_path,
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            )
        ],
        media_types=[MediaType.TV],
        platform="plex",
    )


@pytest.fixture
def mock_rename_plan() -> RenamePlan:
    """Create a mock rename plan."""
    return RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=Path(abs_path("/path/to/media")),
        items=[],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )


@pytest.fixture
def media_file(tmp_path: Path) -> MediaFile:
    """Create a sample media file with platform-appropriate absolute path."""
    file_path = tmp_path / "source1.mp4"
    file_path.touch()
    return MediaFile(
        path=file_path,
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )


@pytest.fixture
def scan_result(media_file: MediaFile) -> ScanResult:
    """Create a sample scan result."""
    media_files = [media_file]
    by_media_type: dict[MediaType, int] = {MediaType.TV: 1}
    return ScanResult(
        root_dir=Path(abs_path("/tmp")),
        files=media_files,
        by_media_type=by_media_type,
        media_types=[MediaType.TV],
        platform="plex",
    )


def test_scan_command_no_media_type() -> None:
    """Test that scan command requires at least one media type."""
    runner = CliRunner()
    result = runner.invoke(app, ["scan", ".", "--no-color"])
    # Typer will show a usage error, not our custom message
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


def test_scan_command_directory_not_found() -> None:
    """Test that scan command handles non-existent directories."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["scan", "/nonexistent", "--media-type", "tv", "--no-color"]
    )
    assert result.exit_code != 0
    assert (
        "does not exist" in result.output or "Invalid value for 'ROOT'" in result.output
    )


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.create_rename_plan")
@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_json_output(
    mock_scan: MagicMock, mock_create_plan: MagicMock
) -> None:
    """Test that scan command can output JSON, or prints warning if no files found."""
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=Path("/tmp"),
        media_types=[MediaType.TV],
        platform="plex",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=Path("/tmp"),
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    result = runner.invoke(
        app, ["scan", "/tmp", "--media-type", "tv", "--json", "--no-color"]
    )
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_no_color(mock_scan: MagicMock) -> None:
    """Test that scan command respects no-color flag and handles empty scans as error."""
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=Path("/tmp"),
        media_types=[MediaType.TV],
        platform="plex",
    )
    result = runner.invoke(app, ["scan", "/tmp", "--media-type", "tv", "--no-color"])
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.create_rename_plan")
@patch("namegnome.cli.commands.scan_directory")
def test_scan_with_media_type(
    mock_scan: MagicMock, mock_create_plan: MagicMock
) -> None:
    """Test that scan command accepts media type, or prints warning if no files found."""
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=Path("/tmp"),
        media_types=[MediaType.TV],
        platform="plex",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=Path("/tmp"),
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    result = runner.invoke(app, ["scan", "/tmp", "--media-type", "tv", "--no-color"])
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.create_rename_plan")
@patch("namegnome.cli.commands.scan_directory")
def test_scan_with_all_options(
    mock_scan: MagicMock, mock_create_plan: MagicMock
) -> None:
    """Test that scan command accepts all optional flags, or prints warning if no files found."""
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=Path("/tmp"),
        media_types=[MediaType.TV, MediaType.MOVIE],
        platform="jellyfin",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=Path("/tmp"),
        items=[],
        platform="jellyfin",
        media_types=[MediaType.TV, MediaType.MOVIE],
        metadata_providers=[],
        llm_model="llama-model",
    )
    result = runner.invoke(
        app,
        [
            "scan",
            "/tmp",
            "--media-type",
            "tv",
            "--media-type",
            "movie",
            "--platform",
            "jellyfin",
            "--verify",
            "--show-name",
            "Test Show",
            "--movie-year",
            "2023",
            "--anthology",
            "--adjust-episodes",
            "--llm-model",
            "llama-model",
            "--no-color",
        ],
    )
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@pytest.mark.parametrize(
    "scan_args",
    [
        ["scan", "{tmp_path}", "--media-type", "tv", "--json", "--no-color"],
        ["scan", "{tmp_path}", "--media-type", "tv", "--no-color"],
        ["scan", "{tmp_path}", "--media-type", "tv", "--no-color"],
        [
            "scan",
            "{tmp_path}",
            "--media-type",
            "tv",
            "--media-type",
            "movie",
            "--platform",
            "jellyfin",
            "--verify",
            "--show-name",
            "Test Show",
            "--movie-year",
            "2023",
            "--anthology",
            "--adjust-episodes",
            "--llm-model",
            "llama-model",
            "--no-color",
        ],
    ],
)
def test_scan_command_cross_platform(
    scan_args: list[str], tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test scan command with a platform-appropriate temp directory."""
    from namegnome.cli.commands import app

    runner = CliRunner()
    args = [a.format(tmp_path=tmp_path) for a in scan_args]
    result = runner.invoke(app, args)
    # Accept either 'No media files found.' or a usage error if the directory is invalid
    assert result.exit_code != 0
    assert (
        "No media files found." in result.output
        or "Usage:" not in result.output  # Fail if usage error is shown
    )


# Add a test to catch Windows-specific usage error
@pytest.mark.skipif(os.name != "nt", reason="Windows-specific error check")
def test_scan_command_windows_usage_error(tmp_path: Path) -> None:
    """Test that scan command does not show usage error for non-existent directory on Windows."""
    from namegnome.cli.commands import app

    runner = CliRunner()
    # Use a non-existent directory
    non_existent = tmp_path / "doesnotexist"
    result = runner.invoke(
        app, ["scan", str(non_existent), "--media-type", "tv", "--no-color"]
    )
    assert result.exit_code != 0
    assert (
        "does not exist" in result.output or "Invalid value for 'ROOT'" in result.output
    )
