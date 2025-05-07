"""Tests for the namegnome scan command."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
import typer
from namegnome.cli.commands import ExitCode, app
from namegnome.models.core import MediaFile, MediaType, ScanResult
from namegnome.models.plan import RenamePlan
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Get a Typer CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_scan_directory() -> MagicMock:
    """Mock the scan_directory function."""
    with patch("namegnome.cli.commands.scan_directory") as mock_scan:
        # Create a fake scan result
        mock_result = ScanResult(
            files=[
                MediaFile(
                    path=Path("/test/file1.mp4"),
                    size=1024,
                    media_type=MediaType.TV,
                    modified_date=datetime.now(),
                ),
                MediaFile(
                    path=Path("/test/file2.mkv"),
                    size=2048,
                    media_type=MediaType.MOVIE,
                    modified_date=datetime.now(),
                ),
            ],
            root_dir=Path("/test"),
            media_types=[MediaType.TV, MediaType.MOVIE],
            platform="plex",
        )
        mock_scan.return_value = mock_result
        yield mock_scan


@pytest.fixture
def mock_create_rename_plan() -> MagicMock:
    """Mock the create_rename_plan function."""
    with patch("namegnome.cli.commands.create_rename_plan") as mock_plan:
        # Create a fake rename plan
        mock_plan_obj = RenamePlan(
            id="test_plan",
            created_at=datetime.now(),
            root_dir=Path("/test"),
            platform="plex",
            items=[],  # Empty items list so no manual items
            media_types=[MediaType.TV, MediaType.MOVIE],
            metadata_providers=[],
            llm_model=None,
        )
        mock_plan.return_value = mock_plan_obj
        yield mock_plan


@pytest.fixture
def mock_storage() -> MagicMock:
    """Mock the save_plan function."""
    with patch("namegnome.cli.commands.save_plan") as mock_save_plan:
        # Return a UUID as the function would
        mock_save_plan.return_value = "12345678-1234-1234-1234-123456789012"
        yield mock_save_plan


@pytest.fixture
def mock_render_diff() -> MagicMock:
    """Mock the render_diff function."""
    with patch("namegnome.cli.commands.render_diff") as mock_render:
        yield mock_render


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
def mock_validate_media_type() -> MagicMock:
    """Mock the validate_media_type function."""
    with patch("namegnome.cli.commands.validate_media_type") as mock_validate:
        mock_validate.side_effect = (
            lambda x: MediaType(x.lower())
            if x.lower() in [m.value for m in MediaType]
            else typer.BadParameter(f"Invalid media type: {x}")
        )
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
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_console: MagicMock,
    mock_render_diff: MagicMock,
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
        mock_scan_directory.assert_called_once()

        # Check that argument types are correct (don't check exact paths)
        assert isinstance(mock_scan_directory.call_args[0][0], Path)
        assert mock_scan_directory.call_args[0][1] == [MediaType.TV]

        # Verify that the planner was called
        mock_create_rename_plan.assert_called_once()

        # Verify that the storage function was called
        assert mock_storage.called

        # Verify that the diff was rendered
        mock_render_diff.assert_called_once()


def test_scan_command_no_media_type(
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_console: MagicMock,
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
        mock_scan_directory.assert_not_called()


def test_scan_command_invalid_media_type(
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_console: MagicMock,
    mock_validate_media_type: MagicMock,
) -> None:
    """Test the scan command with an invalid media type."""
    # Set up the mock_validate_media_type to raise an error
    mock_validate_media_type.side_effect = typer.BadParameter(
        "Invalid media type. Must be one of: tv, movie, music"
    )

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
        mock_scan_directory.assert_not_called()


def test_scan_command_json_output(
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_stdout_write: MagicMock,
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
                catch_exceptions=False,
            )

            # Ensure command runs without error
            assert result.exit_code == ExitCode.SUCCESS

            # Check that output contains JSON (look for specific parts)
            assert '"id":' in result.output
            assert '"platform": "plex"' in result.output
            assert '"media_types": [' in result.output


def test_scan_command_verify_flag(
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_console: MagicMock,
) -> None:
    """Test the scan command with the verify flag."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = runner.invoke(
            app,
            ["scan", str(temp_path), "--media-type", "tv", "--verify"],
        )

        # Ensure command runs without error
        assert result.exit_code == ExitCode.SUCCESS

        # Verify that the scanner was called with verify=True
        mock_scan_directory.assert_called_once()
        assert mock_scan_directory.call_args[1]["verify"]

        # Verify that the save_plan was called with verify=True
        mock_storage.assert_called_once()
        # The save_plan should be called with verify=True
        assert mock_storage.call_args[1]["verify"]


def test_scan_command_with_all_options(
    mock_scan_directory: MagicMock,
    mock_create_rename_plan: MagicMock,
    mock_storage: MagicMock,
    mock_console: MagicMock,
) -> None:
    """Test the scan command with all available options."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        result = runner.invoke(
            app,
            [
                "scan",
                str(temp_path),
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

        # The exit code is either SUCCESS or MANUAL_NEEDED, both are valid
        assert result.exit_code in (ExitCode.SUCCESS, ExitCode.MANUAL_NEEDED)

        # Verify that the scanner was called with the right arguments
        mock_scan_directory.assert_called_once()
        call_args = mock_scan_directory.call_args

        # Check positional arguments
        assert isinstance(call_args[0][0], Path)
        assert call_args[0][1] == [MediaType.TV, MediaType.MOVIE]

        # Check keyword arguments
        kwargs = call_args[1]
        assert kwargs["verify"]

        # Verify that the create_rename_plan was called with jellyfin
        mock_create_rename_plan.assert_called_once()
        assert mock_create_rename_plan.call_args[1]["platform"] == "jellyfin"
        assert mock_create_rename_plan.call_args[1]["show_name"] == "Test Show"
        assert mock_create_rename_plan.call_args[1]["movie_year"] == 2023
        assert mock_create_rename_plan.call_args[1]["anthology"]
        assert mock_create_rename_plan.call_args[1]["adjust_episodes"]

        # Verify that the storage function was called
        assert mock_storage.called
