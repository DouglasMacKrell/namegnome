"""Hot-spot tests for conflict detection and unsupported media handling in
`namegnome.core.tv.plan_orchestration`.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

import pytest

from namegnome.core.tv.plan_orchestration import (
    add_plan_item_with_conflict_detection,
    _handle_unsupported_media_type,
    TVPlanContext,
)
from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.models.plan import RenamePlan, RenamePlanItem


def _ctx(tmp_path: Path) -> TVPlanContext:  # noqa: D401
    plan = RenamePlan(
        id="p",
        platform="plex",
        root_dir=tmp_path,
    )
    return TVPlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


def test_case_insensitive_conflict_detection(tmp_path: Path):
    ctx = _ctx(tmp_path)
    src1 = tmp_path / "Video.mkv"
    src2 = tmp_path / "video.mkv"  # differs only by case
    dest1 = tmp_path / "dest.mkv"

    dummy_media = MediaFile(
        path=src1,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )

    item1 = RenamePlanItem(source=src1, destination=dest1, media_file=dummy_media)
    item2 = RenamePlanItem(source=src2, destination=dest1, media_file=dummy_media)

    # First insert should succeed without conflict
    add_plan_item_with_conflict_detection(item1, ctx, dest1)
    assert item1.status != PlanStatus.CONFLICT

    # Second insert triggers case-insensitive conflict
    add_plan_item_with_conflict_detection(item2, ctx, dest1)
    assert item2.status == PlanStatus.CONFLICT
    assert item1.status == PlanStatus.CONFLICT, "Existing item should also be marked as conflict"


def test_handle_unsupported_media_type(tmp_path: Path):
    ctx = _ctx(tmp_path)
    media_file = MediaFile(
        path=tmp_path / "audio.mp3",
        size=1,
        media_type=MediaType.MUSIC,  # unsupported by TV planner
        modified_date=datetime.now(),
    )

    _handle_unsupported_media_type(media_file, ctx, None)

    assert ctx.plan.items, "An item should have been added"
    item = ctx.plan.items[0]
    assert item.manual and item.manual_reason == "Unsupported media type" 