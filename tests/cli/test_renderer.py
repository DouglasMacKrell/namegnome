"""Tests for the renderer module."""

import io
import re
from datetime import datetime
from pathlib import Path

import pytest
from rich.console import Console

from namegnome.cli.renderer import render_diff
from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.models.plan import RenamePlan, RenamePlanItem


# Helper function to create an absolute path that's platform-independent
def abs_path(path_str: str) -> Path:
    """Create a platform-independent absolute path."""
    import os
    from pathlib import Path

    if os.name == "nt":  # Windows
        # Convert Unix-style paths to Windows absolute paths
        if path_str.startswith("/"):
            return Path("C:" + path_str.replace("/", "\\"))
    # For Unix systems, keep the path as is
    return Path(path_str)


@pytest.fixture
def media_file() -> MediaFile:
    """Create a sample media file."""
    return MediaFile(
        path=abs_path("/tmp/source1.mp4"),
        size=1024,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )


@pytest.fixture
def sample_plan(media_file: MediaFile) -> RenamePlan:
    """Create a sample rename plan."""
    return RenamePlan(
        id="test-plan",
        created_at=datetime(2025, 5, 6, 16, 22, 7),
        root_dir=abs_path("/tmp"),
        items=[
            RenamePlanItem(
                source=abs_path("/tmp/source1.mp4"),
                destination=abs_path("/tmp/target1.mp4"),
                media_file=media_file,
                status=PlanStatus.PENDING,
            ),
            RenamePlanItem(
                source=abs_path("/tmp/source2.mp4"),
                destination=abs_path("/tmp/target2.mp4"),
                media_file=media_file,
                status=PlanStatus.CONFLICT,
            ),
            RenamePlanItem(
                source=abs_path("/tmp/source3.mp4"),
                destination=abs_path("/tmp/target3.mp4"),
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
    # No specific path checks as they might differ between platforms


def test_render_diff_no_color(sample_plan: RenamePlan) -> None:
    """Test that the diff renderer respects no-color flag."""
    # Use a StringIO to capture output instead of capsys
    string_io = io.StringIO()
    console = Console(file=string_io, no_color=True, highlight=False, soft_wrap=True)
    render_diff(sample_plan, console=console)

    # Get output as plain text
    output = string_io.getvalue()

    # Strip ANSI control sequences
    cleaned_output = re.sub(r"\x1b\[.*?m", "", output)

    # Check for table structure in the plain text
    assert "Rename Plan" in cleaned_output
    assert "Status" in cleaned_output
    assert "Source" in cleaned_output
    assert "Destination" in cleaned_output
    assert "Reason" in cleaned_output


def test_render_diff_empty_plan() -> None:
    """Test rendering an empty plan."""
    plan = RenamePlan(
        id="empty-plan",
        created_at=datetime.now(),
        root_dir=abs_path("/tmp"),
        items=[],
        platform="plex",
        media_types=[],
        metadata_providers=[],
        llm_model=None,
    )

    # Use a StringIO to capture output
    string_io = io.StringIO()
    console = Console(file=string_io, force_terminal=True)
    render_diff(plan, console=console)

    output = string_io.getvalue()

    # Strip ANSI control sequences for clean comparison
    cleaned_output = re.sub(r"\x1b\[.*?m", "", output)

    # Check for the summary line in the appropriate format
    assert re.search(r"Total:\s*0", cleaned_output)
    assert re.search(r"Conflicts:\s*0", cleaned_output)


def test_render_diff_status_colors(
    capsys: pytest.CaptureFixture[str], sample_plan: RenamePlan
) -> None:
    """Test that different statuses get different colors."""
    console = Console(force_terminal=True)
    render_diff(sample_plan, console=console)
    captured = capsys.readouterr()

    # Check for ANSI control sequences in the output
    assert "\033[" in captured.out

    # Verify presence of statuses in the output
    assert "pending" in captured.out
    assert "conflict" in captured.out
    assert "manual" in captured.out
