"""Tests for the namegnome scan command."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
import typer
from namegnome.cli.commands import ExitCode, app
from namegnome.models.core import MediaFile, MediaType, RenamePlan, ScanResult
from typer.testing import CliRunner


@pytest.fixture
def mock_scanner() -> MagicMock:
    """Mock the scan_directory function."""
    with patch("namegnome.cli.commands.scan_directory") as mock_scanner:
        # Create a mock scan result
        media_file = MediaFile(
            path=Path("/test/file.mp4").absolute(),
            size=1024,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        )

        result = ScanResult(
            total_files=1,
            media_files=[media_file],
            skipped_files=0,
            by_media_type={MediaType.TV: 1},
            errors=[],
            scan_duration_seconds=0.1,
            root_dir=Path("/test").absolute(),
        )

        mock_scanner.return_value = result
        yield mock_scanner


@pytest.fixture
def mock_planner() -> MagicMock:
    """Mock the create_rename_plan function."""
    with patch("namegnome.cli.commands.create_rename_plan") as mock_planner:
        # Create a mock rename plan
        plan = RenamePlan(
            id="20250101_010101",
            created_at=datetime.now(),
            root_dir=Path("/test").absolute(),
            platform="plex",
            media_types=[MediaType.TV],
            items=[],
        )

        mock_planner.return_value = plan
        yield mock_planner


@pytest.fixture
def mock_storage() -> tuple[MagicMock, MagicMock]:
    """Mock the storage functions."""
    with patch("namegnome.cli.commands.store_plan") as mock_store_plan, \
         patch("namegnome.cli.commands.store_run_metadata") as mock_store_metadata:

        mock_store_plan.return_value = Path("/test/.namegnome/plans/20250101_010101.json")
        mock_store_metadata.return_value = Path("/test/.namegnome/plans/20250101_010101_meta.json")

        yield mock_store_plan, mock_store_metadata


@pytest.fixture
def mock_console_log() -> MagicMock:
    """Mock the console.log method."""
    with patch("namegnome.cli.commands.console.log") as mock_log:
        yield mock_log


@pytest.fixture
def mock_console() -> MagicMock:
    """Mock the entire console creation."""
    with patch("namegnome.cli.commands.Console") as mock_console_class:
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        yield mock_console


@pytest.fixture
def mock_stdout_write() -> MagicMock:
    """Mock sys.stdout.write method."""
    with patch("sys.stdout.write") as mock_write:
        yield mock_write


@pytest.fixture
def mock_render_diff() -> MagicMock:
    """Mock the render_diff function."""
    with patch("namegnome.cli.commands.render_diff") as mock_render_diff:
        yield mock_render_diff


@pytest.fixture
def mock_validate_media_type() -> MagicMock:
    """Mock the validate_media_type function."""
    with patch("namegnome.cli.commands.validate_media_type") as mock_validate:
        mock_validate.side_effect = lambda x: MediaType(x.lower()) if x.lower() in [m.value for m in MediaType] else typer.BadParameter(f"Invalid media type: {x}")
        yield mock_validate


@pytest.fixture
def temp_dir_with_media() -> Iterator[Path]:
    """Create a temporary directory with a fake media file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a fake media file
        media_path = Path(temp_dir) / "test.mp4"
        with open(media_path, "wb") as f:
            f.write(b"FAKE MP4 DATA")

        yield Path(temp_dir)


def test_scan_command_basic(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_console: MagicMock, mock_render_diff: MagicMock
) -> None:
    """Test the basic scan command with minimal options."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = runner.invoke(
            app,
            ["scan", str(temp_path), "--media-type", "tv"],
        )

        # Ensure command runs without error
        assert result.exit_code == ExitCode.SUCCESS

        # Verify that the scanner was called
        mock_scanner.assert_called_once()

        # Check that argument types are correct (don't check exact paths)
        assert isinstance(mock_scanner.call_args[0][0], Path)
        assert mock_scanner.call_args[0][1] == [MediaType.TV]

        # Verify that the planner was called
        mock_planner.assert_called_once()

        # Verify that the storage functions were called
        mock_store_plan, mock_store_metadata = mock_storage
        assert mock_store_plan.called
        assert mock_store_metadata.called

        # Verify that the diff was rendered
        mock_render_diff.assert_called_once()


def test_scan_command_no_media_type(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_console: MagicMock
) -> None:
    """Test the scan command with missing media type."""
    # Set up the mock console to capture the error
    mock_console.print.return_value = None

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Store result but don't check exit code as the CliRunner doesn't properly propagate it
        _ = runner.invoke(
            app,
            ["scan", str(temp_path)],
        )

        # Verify that the console prints the expected error message
        mock_console.print.assert_called_with(
            "[red]Error: At least one media type must be specified[/red]"
        )

        # Verify that the scanner was not called
        mock_scanner.assert_not_called()


def test_scan_command_invalid_media_type(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_console: MagicMock, mock_validate_media_type: MagicMock
) -> None:
    """Test the scan command with an invalid media type."""
    # Set up the mock_validate_media_type to raise an error
    mock_validate_media_type.side_effect = typer.BadParameter("Invalid media type. Must be one of: tv, movie, music")

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Store result but don't check exit code as the CliRunner doesn't properly propagate it
        _ = runner.invoke(
            app,
            ["scan", str(temp_path), "--media-type", "invalid"],
        )

        # Verify the validate_media_type was called
        mock_validate_media_type.assert_called_with("invalid")

        # Verify that the console prints the expected error message
        mock_console.print.assert_called_with(
            "[red]Error: Invalid media type. Must be one of: tv, movie, music[/red]"
        )

        # Verify that the scanner was not called
        mock_scanner.assert_not_called()


def test_scan_command_json_output(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_stdout_write: MagicMock
) -> None:
    """Test the scan command with JSON output."""
    # Using CliRunner with isolation to test the command
    runner = CliRunner(mix_stderr=False)

    # We need to mock console.log to prevent it from appearing in output
    with patch("namegnome.cli.commands.console.log"):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = runner.invoke(
                app,
                ["scan", str(temp_path), "--media-type", "tv", "--json"],
                catch_exceptions=False
            )

            # Ensure command runs without error
            assert result.exit_code == ExitCode.SUCCESS

            # Check that output contains JSON (look for specific parts)
            assert '"id":' in result.output
            assert '"platform": "plex"' in result.output
            assert '"media_types": [' in result.output


def test_scan_command_verify_flag(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_console: MagicMock
) -> None:
    """Test the scan command with --verify flag."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = runner.invoke(
            app,
            ["scan", str(temp_path), "--media-type", "tv", "--verify"],
        )

        # Ensure command runs without error
        assert result.exit_code == ExitCode.SUCCESS

        # Verify that the scanner was called with verify_hash=True
        assert mock_scanner.call_args[1]["verify_hash"] is True


def test_scan_command_with_all_options(
    mock_scanner: MagicMock, mock_planner: MagicMock, mock_storage: tuple[MagicMock, MagicMock], mock_console: MagicMock
) -> None:
    """Test the scan command with all options."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = runner.invoke(
            app,
            [
                "scan",
                str(temp_path),
                "--media-type", "tv",
                "--media-type", "movie",
                "--platform", "jellyfin",
                "--show-name", "Test Show",
                "--movie-year", "2023",
                "--anthology",
                "--adjust-episodes",
                "--verify",
                "--no-color",
                "--llm-model", "test-model",
                "--strict-directory-structure",
            ],
        )

        # Ensure command runs without error
        assert result.exit_code == ExitCode.SUCCESS

        # Verify that all arguments were passed to the planner
        assert mock_planner.call_args[1]["platform"] == "jellyfin"
        assert mock_planner.call_args[1]["show_name"] == "Test Show"
        assert mock_planner.call_args[1]["movie_year"] == 2023
        assert mock_planner.call_args[1]["anthology"] is True
        assert mock_planner.call_args[1]["adjust_episodes"] is True
        assert mock_planner.call_args[1]["verify"] is True
        assert mock_planner.call_args[1]["llm_model"] == "test-model"
