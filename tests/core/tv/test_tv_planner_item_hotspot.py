"""Tests some branches of namegnome.core.tv_planner._handle_normal_plan_item."""

from datetime import datetime
from pathlib import Path

from namegnome.core import tv_planner as tvp
from namegnome.core.tv.tv_plan_context import TVPlanContext
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan
from namegnome.rules.base import RuleSet, RuleSetConfig


class DummyRuleSet(RuleSet):
    def __init__(self):
        super().__init__("dummy")

    def target_path(
        self, media_file, base_dir=None, config=None, metadata=None, **kwargs
    ):  # type: ignore[override]
        # Return a predictable dummy path that does not rely on metadata fields.
        return (base_dir or Path(".")) / "dummy.mkv"

    def supports_media_type(self, media_type):
        return True

    @property
    def supported_media_types(self):
        return [MediaType.TV]


def _make_ctx(tmp_path: Path):
    plan = RenamePlan(
        id="tvplanner",
        created_at=datetime.now(),
        root_dir=tmp_path,
        platform="plex",
        items=[],
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    return TVPlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


def test_handle_normal_plan_item_found_match(tmp_path: Path):
    file_path = tmp_path / "Show - S01E01.mkv"
    file_path.touch()
    mfile = MediaFile(
        path=file_path,
        size=42,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title="Show",
        season=1,
    )
    rule_set = DummyRuleSet()
    ctx = _make_ctx(tmp_path)

    # Monkeypatch conflict helper so that it actually appends to the plan for unit-testing purposes
    import namegnome.core.tv.plan_conflicts as pc  # noqa: WPS433

    pc.add_plan_item_with_conflict_detection = (
        lambda item, ctx_arg, _path: ctx_arg.plan.items.append(item)
    )
    tvp.add_plan_item_with_conflict_detection = pc.add_plan_item_with_conflict_detection

    # Call with found_match=True to mark item as automatic (not manual)
    tvp._handle_normal_plan_item(
        mfile,
        rule_set,
        RuleSetConfig(),
        ctx,
        found_match=True,
    )

    assert len(ctx.plan.items) == 1
    item = ctx.plan.items[0]
    assert item.manual is False
    # Destination path produced by dummy rule set contains Season 01 folder
    assert item.destination.name == "dummy.mkv"
