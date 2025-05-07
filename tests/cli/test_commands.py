"""Tests for the CLI commands."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from namegnome.cli.commands import scan_command
from namegnome.models.core import MediaFile, MediaType, RenamePlan, ScanResult


@pytest.fixture
def mock_scan_result() -> ScanResult:
    """Create a mock scan result."""
    return ScanResult(
        root_dir=Path("/path/to/media"),
        media_files=[
            MediaFile(
                path=Path("/path/to/media/test.mp4"),
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            )
        ],
    )


@pytest.fixture
def mock_rename_plan() -> RenamePlan:
    """Create a mock rename plan."""
    return RenamePlan(
        id="test-plan",
        created_at=datetime.now(),
        root_dir=Path("/path/to/media"),
        items=[],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )


@pytest.fixture
def media_file() -> MediaFile:
    """Create a sample media file."""
    return MediaFile(
        path=Path("/tmp/source1.mp4"),
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
        root_dir=Path("/tmp"),
        media_files=media_files,
        by_media_type=by_media_type,
    )


@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_no_media_type(mock_scan: Any) -> None:
    """Test that scan command requires at least one media type."""
    result = scan_command(root=Path("/tmp"))
    assert result == 1


@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_invalid_media_type(mock_scan: Any) -> None:
    """Test that scan command validates media types."""
    result = scan_command(root=Path("/tmp"), media_type=["invalid"])
    assert result == 1


@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_directory_not_found(mock_scan: Any) -> None:
    """Test that scan command handles non-existent directories."""
    mock_scan.side_effect = FileNotFoundError("Directory not found")
    result = scan_command(root=Path("/nonexistent"), media_type=["tv"])
    assert result == 1


@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_json_output(
    mock_scan: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that scan command can output JSON."""
    # Create a real ScanResult object for the mock to return
    scan_result = ScanResult(
        root_dir=Path("/tmp"),
        media_files=[
            MediaFile(
                path=Path("/tmp/test.mp4"),
                size=1024,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
            )
        ],
    )
    mock_scan.return_value = scan_result

    result = scan_command(
        root=Path("/tmp"),
        media_type=["tv"],
        json_output=True,
    )
    assert result == 0
    captured = capsys.readouterr()
    assert "items" in captured.out


@patch("namegnome.cli.commands.scan_directory")
def test_scan_command_no_color(mock_scan: Any) -> None:
    """Test that scan command respects no-color flag."""
    result = scan_command(
        root=Path("/tmp"),
        media_type=["tv"],
        no_color=True,
    )
    assert result == 0


@patch("namegnome.cli.commands.scan_directory")
@patch("namegnome.cli.commands.create_rename_plan")
def test_scan_with_media_type(
    mock_create_plan: Any, mock_scan: Any, mock_scan_result: Any, mock_rename_plan: Any
) -> None:
    """Test that scan command accepts media type."""
    mock_scan.return_value = mock_scan_result
    mock_create_plan.return_value = mock_rename_plan

    result = scan_command(Path("/path/to/media"), media_type=["tv"])
    assert result == 0


@patch("namegnome.cli.commands.scan_directory")
@patch("namegnome.cli.commands.create_rename_plan")
def test_scan_json_output(
    mock_create_plan: Any, mock_scan: Any, mock_scan_result: Any, mock_rename_plan: Any
) -> None:
    """Test that scan command can output JSON."""
    mock_scan.return_value = mock_scan_result
    mock_create_plan.return_value = mock_rename_plan

    result = scan_command(Path("/path/to/media"), media_type=["tv"], json_output=True)
    assert result == 0


@patch("namegnome.cli.commands.scan_directory")
@patch("namegnome.cli.commands.create_rename_plan")
def test_scan_no_color(
    mock_create_plan: Any, mock_scan: Any, mock_scan_result: Any, mock_rename_plan: Any
) -> None:
    """Test that scan command respects no-color flag."""
    mock_scan.return_value = mock_scan_result
    mock_create_plan.return_value = mock_rename_plan

    result = scan_command(Path("/path/to/media"), media_type=["tv"], no_color=True)
    assert result == 0


@patch("namegnome.cli.commands.scan_directory")
@patch("namegnome.cli.commands.create_rename_plan")
def test_scan_with_all_options(
    mock_create_plan: Any, mock_scan: Any, mock_scan_result: Any, mock_rename_plan: Any
) -> None:
    """Test that scan command accepts all optional flags."""
    mock_scan.return_value = mock_scan_result
    mock_create_plan.return_value = mock_rename_plan

    result = scan_command(
        Path("/path/to/media"),
        media_type=["tv"],
        platform="plex",
        show_name="Test Show",
        movie_year=2024,
        anthology=True,
        adjust_episodes=True,
        verify=True,
        llm_model="deepseek-coder",
        strict_directory_structure=False,
    )
    assert result == 0
