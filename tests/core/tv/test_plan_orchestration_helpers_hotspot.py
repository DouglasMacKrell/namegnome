"""Hotspot tests for lightweight helper utilities inside
*namegnome.core.tv.plan_orchestration*.

These tests focus on internal helpers that previously had no direct coverage:
• `_ensure_plan_container`
• `_add_plan_item_and_callback`
• `_handle_explicit_span`
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from namegnome.core.tv import plan_orchestration as po
from namegnome.models.core import MediaFile, MediaType, PlanStatus
from namegnome.models.plan import RenamePlanItem


def _dummy_media(tmp_path: Path) -> MediaFile:  # noqa: D401
    return MediaFile(
        path=tmp_path / "dummy.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
    )


def test_ensure_plan_container_stubs_items_list():
    ctx = SimpleNamespace()  # no `plan` attribute yet
    items = po._ensure_plan_container(ctx)

    # The function should attach a stub plan with an items list.
    assert hasattr(ctx, "plan") and hasattr(ctx.plan, "items")
    assert items is ctx.plan.items  # same list object


def test_add_plan_item_and_callback_appends(tmp_path: Path):
    plan_ctx = SimpleNamespace()  # intentionally missing plan/items
    media = _dummy_media(tmp_path)
    item = RenamePlanItem(source=media.path, destination=media.path, media_file=media)

    # Should attach plan container and append item
    po._add_plan_item_and_callback(item, plan_ctx, None, media)

    assert hasattr(plan_ctx, "plan")
    assert item in plan_ctx.plan.items


def test_handle_explicit_span_flag():
    span_ctx = SimpleNamespace(found_match=True)
    assert po._handle_explicit_span(span_ctx) is True

    span_ctx2 = SimpleNamespace(found_match=False)
    assert po._handle_explicit_span(span_ctx2) is False 