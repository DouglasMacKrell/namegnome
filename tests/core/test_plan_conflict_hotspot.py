"""Tests conflict detection helper in planner.add_plan_item_with_conflict_detection."""

from pathlib import Path
from datetime import datetime

from namegnome.core.planner import (
    add_plan_item_with_conflict_detection as add_conflict,
    PlanContext,
)
from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.models.plan import RenamePlan, RenamePlanItem


def _dummy_plan_context(tmp_path):
    plan = RenamePlan(
        id="p1",
        created_at=datetime.now(),
        root_dir=tmp_path,
        items=[],
        platform="plex",
        media_types=[MediaType.TV],
        metadata_providers=[],
    )
    return PlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


def test_add_plan_item_conflict_marks_both(tmp_path):
    ctx = _dummy_plan_context(tmp_path)

    dest = tmp_path / "Season 01" / "Show - S01E01.mkv"
    dest.parent.mkdir(parents=True, exist_ok=True)

    src1 = tmp_path / "file1.mkv"
    src1.touch()
    item1 = RenamePlanItem(
        source=src1,
        destination=dest,
        media_file=MediaFile(
            path=src1,
            size=1,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        ),
    )
    add_conflict(item1, ctx, dest)

    # Second item with SAME destination triggers conflict
    src2 = tmp_path / "file2.mkv"
    src2.touch()
    item2 = RenamePlanItem(
        source=src2,
        destination=dest,
        media_file=MediaFile(
            path=src2,
            size=1,
            media_type=MediaType.TV,
            modified_date=datetime.now(),
        ),
    )
    add_conflict(item2, ctx, dest)

    assert item1.status == PlanStatus.CONFLICT and item2.status == PlanStatus.CONFLICT 