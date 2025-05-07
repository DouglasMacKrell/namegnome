"""Tests for the CLI renderer."""

import datetime
from pathlib import Path

import pytest
from namegnome.cli.renderer import render_diff
from namegnome.models.core import MediaFile, MediaType, PlanStatus, RenamePlan, RenamePlanItem
from rich.console import Console


@pytest.fixture
def media_file() -> MediaFile:
    """Create a sample media file."""
    return MediaFile(
        path=Path("/tmp/source1.mp4"),
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.datetime.now(),
    )


@pytest.fixture
def sample_plan(media_file: MediaFile) -> RenamePlan:
    """Create a sample rename plan."""
    return RenamePlan(
        id="test-plan",
        created_at=datetime.datetime(2025, 5, 6, 16, 22, 7),
        root_dir=Path("/tmp"),
        items=[
            RenamePlanItem(
                source=Path("/tmp/source1.mp4"),
                destination=Path("/tmp/target1.mp4"),
                media_file=media_file,
                status=PlanStatus.PENDING,
            ),
            RenamePlanItem(
                source=Path("/tmp/source2.mp4"),
                destination=Path("/tmp/target2.mp4"),
                media_file=media_file,
                status=PlanStatus.CONFLICT,
            ),
            RenamePlanItem(
                source=Path("/tmp/source3.mp4"),
                destination=Path("/tmp/target3.mp4"),
                media_file=media_file,
                status=PlanStatus.MANUAL,
            ),
        ],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )


def test_render_diff_with_color(
    capsys: pytest.CaptureFixture[str], sample_plan: RenamePlan
) -> None:
    """Test that the diff renderer outputs colored text."""
    console = Console(force_terminal=True)
    render_diff(sample_plan, console=console)
    captured = capsys.readouterr()

    # Check for ANSI color codes
    assert "\033[" in captured.out
    # Check for table structure
    assert "Rename Plan" in captured.out
    assert "Status" in captured.out
    assert "Source" in captured.out
    assert "Destination" in captured.out
    assert "Reason" in captured.out
    # Check for test data
    assert "/tmp/source1.mp4" in captured.out
    assert "/tmp/target1.mp4" in captured.out


def test_render_diff_no_color(capsys: pytest.CaptureFixture[str], sample_plan: RenamePlan) -> None:
    """Test that the diff renderer respects no-color flag."""
    console = Console(force_terminal=True, no_color=True)
    render_diff(sample_plan, console=console)
    captured = capsys.readouterr()

    # Check that no ANSI color codes are present
    assert "\033[" not in captured.out
    # Check for table structure
    assert "Rename Plan" in captured.out
    assert "Status" in captured.out
    assert "Source" in captured.out
    assert "Destination" in captured.out
    assert "Reason" in captured.out


def test_render_diff_empty_plan(capsys: pytest.CaptureFixture[str]) -> None:
    """Test rendering an empty plan."""
    plan = RenamePlan(
        id="empty-plan",
        created_at=datetime.datetime.now(),
        root_dir=Path("/tmp"),
        items=[],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )
    console = Console(force_terminal=True)
    render_diff(plan, console=console)
    captured = capsys.readouterr()

    assert "Total: 0 | Conflicts: 0" in captured.out


def test_render_diff_status_colors(
    capsys: pytest.CaptureFixture[str], sample_plan: RenamePlan
) -> None:
    """Test that different statuses get different colors."""
    console = Console(force_terminal=True)
    render_diff(sample_plan, console=console)
    captured = capsys.readouterr()

    # Check for color codes for different statuses
    assert "\033[1;33m" in captured.out  # Yellow for PENDING
    assert "\033[1;31m" in captured.out  # Red for CONFLICT
    assert "\033[1;91m" in captured.out  # Bright red for MANUAL
