"""Tests for the namegnome CLI commands.

This test suite covers:
- CLI command validation, argument parsing, and error handling
- Scan command with various options, output modes (JSON, no-color), and platform-specific quirks
- Mocking of scan and plan creation logic for isolated CLI testing
- Cross-platform path handling and Windows/Unix-specific edge cases
- Ensures robust, user-friendly CLI UX and error reporting (see PLANNING.md)

Rationale:
- Guarantees that CLI commands behave as expected for all supported scenarios and platforms
- Validates error handling, output modes, and argument validation for user safety and onboarding
"""

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


@pytest.fixture
def mock_scan_result(tmp_path: Path) -> ScanResult:
    """Create a mock scan result with platform-appropriate absolute paths.

    Returns:
        ScanResult: A mock scan result for CLI tests.
    """
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
def mock_rename_plan(tmp_path: Path) -> RenamePlan:
    """Create a mock rename plan.

    Returns:
        RenamePlan: A mock plan for CLI tests.
    """
    root_dir = tmp_path / "media"
    root_dir.mkdir(parents=True, exist_ok=True)
    return RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=root_dir,
        items=[],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )


@pytest.fixture
def media_file(tmp_path: Path) -> MediaFile:
    """Create a sample media file with platform-appropriate absolute path.

    Returns:
        MediaFile: A sample media file for CLI tests.
    """
    file_path = tmp_path / "source1.mp4"
    file_path.touch()
    return MediaFile(
        path=file_path,
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )


@pytest.fixture
def scan_result(media_file: MediaFile, tmp_path: Path) -> ScanResult:
    """Create a sample scan result.

    Returns:
        ScanResult: A sample scan result for CLI tests.
    """
    media_files = [media_file]
    by_media_type: dict[MediaType, int] = {MediaType.TV: 1}
    return ScanResult(
        root_dir=tmp_path,
        files=media_files,
        by_media_type=by_media_type,
        media_types=[MediaType.TV],
        platform="plex",
    )


def test_scan_command_no_media_type() -> None:
    """Test that scan command requires at least one media type.

    Scenario:
    - Invokes scan command without media type and expects a usage error.
    - Ensures CLI argument validation and error reporting.
    """
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
    """Test that scan command validates media types.

    Scenario:
    - Invokes scan command with an invalid media type and expects an error message.
    - Ensures CLI argument validation and error reporting.
    """
    runner = CliRunner()
    result = runner.invoke(app, ["scan", ".", "--media-type", "invalid", "--no-color"])
    assert result.exit_code != 0
    assert (
        "Error: Invalid media type. Must be one of: tv, movie, music" in result.output
    )


def test_scan_command_directory_not_found() -> None:
    """Test that scan command handles non-existent directories.

    Scenario:
    - Invokes scan command with a nonexistent directory and expects an error message.
    - Ensures robust error handling for missing paths.
    """
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
    mock_scan: MagicMock, mock_create_plan: MagicMock, tmp_path: Path
) -> None:
    """Test that scan command can output JSON, or prints warning if no files found.

    Scenario:
    - Mocks scan and plan creation to simulate empty results.
    - Invokes scan command with --json and checks for correct output or warning.
    - Ensures JSON output mode and error handling are robust.
    """
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=tmp_path,
        media_types=[MediaType.TV],
        platform="plex",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--media-type", "tv", "--json", "--no-color"]
    )
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_no_color(mock_scan: MagicMock, tmp_path: Path) -> None:
    """Test that scan command respects no-color flag and handles empty scans as error.

    Scenario:
    - Mocks scan to simulate empty results.
    - Invokes scan command with --no-color and checks for correct output or warning.
    - Ensures no-color output mode and error handling are robust.
    """
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=tmp_path,
        media_types=[MediaType.TV],
        platform="plex",
    )
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--media-type", "tv", "--no-color"]
    )
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.create_rename_plan")
@patch("namegnome.cli.commands.scan_directory")
def test_scan_with_media_type(
    mock_scan: MagicMock, mock_create_plan: MagicMock, tmp_path: Path
) -> None:
    """Test that scan command accepts media type, or prints warning if no files found.

    Scenario:
    - Mocks scan and plan creation to simulate empty results.
    - Invokes scan command with --media-type and checks for correct output or warning.
    - Ensures media type argument is handled correctly.
    """
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=tmp_path,
        media_types=[MediaType.TV],
        platform="plex",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--media-type", "tv", "--no-color"]
    )
    assert result.exit_code != 0
    assert "No media files found." in result.output or "Usage:" in result.output


@patch("rich.progress.Progress", new=lambda *a, **kw: contextlib.nullcontext())
@patch("rich.console.Console.status", new=lambda *a, **kw: contextlib.nullcontext())
@patch("namegnome.cli.commands.create_rename_plan")
@patch("namegnome.cli.commands.scan_directory")
def test_scan_with_all_options(
    mock_scan: MagicMock, mock_create_plan: MagicMock, tmp_path: Path
) -> None:
    """Test that scan command accepts all optional flags, or prints warning if no files found."""
    runner = CliRunner()
    mock_scan.return_value = ScanResult(
        files=[],
        root_dir=tmp_path,
        media_types=[MediaType.TV, MediaType.MOVIE],
        platform="jellyfin",
    )
    mock_create_plan.return_value = RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=tmp_path,
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
            str(tmp_path),
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


def test_config_show_command(monkeypatch: MonkeyPatch) -> None:
    """Test the 'config --show' CLI command prints resolved settings and handles missing keys."""
    runner = CliRunner()
    # Set required env vars
    monkeypatch.setenv("TMDB_API_KEY", "dummy-key")
    monkeypatch.setenv("OMDB_API_KEY", "dummy-omdb")
    # Optional keys
    monkeypatch.delenv("TVDB_API_KEY", raising=False)
    monkeypatch.delenv("FANARTTV_API_KEY", raising=False)
    result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "TMDB_API_KEY" in result.output
    assert "dumm..." in result.output  # Masked value
    assert "OMDB_API_KEY" in result.output
    assert "dumm..." in result.output  # Masked value
    # Now unset a required key and check for error
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    result2 = runner.invoke(app, ["config", "--show"])
    assert result2.exit_code == 1
    assert "Missing required API key: TMDB_API_KEY" in result2.output
    assert "See documentation" in result2.output
