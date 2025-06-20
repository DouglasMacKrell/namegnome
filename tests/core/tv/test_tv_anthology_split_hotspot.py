"""Tests for namegnome.core.tv.anthology.tv_anthology_split hot paths."""

from datetime import datetime
from pathlib import Path

from namegnome.core.tv.anthology import tv_anthology_split as tas
from namegnome.core.tv.tv_plan_context import TVPlanContext
from namegnome.metadata.models import TVEpisode
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan
from namegnome.rules.base import RuleSet, RuleSetConfig


class DummyRuleSet(RuleSet):
    """Minimal RuleSet implementation sufficient for tests."""

    def __init__(self):
        super().__init__("dummy")

    def target_path(
        self, media_file, base_dir=None, config=None, metadata=None, **kwargs
    ):  # type: ignore[override]
        # For unit-tests we don't care about the real path – just echo source.
        return media_file.path

    def supports_media_type(self, media_type):
        return True

    @property
    def supported_media_types(self):
        return [MediaType.TV]


def _make_ctx(tmp_path: Path):
    plan = RenamePlan(
        id="test_plan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        platform="plex",
        items=[],
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    return TVPlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


def test_anthology_split_early_match(tmp_path: Path):
    file_path = tmp_path / "Show-S01E01-SegmentA and SegmentB.mkv"
    file_path.touch()

    media_file = MediaFile(
        path=file_path,
        size=123,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    rule_set = DummyRuleSet()
    ctx = _make_ctx(tmp_path)

    episodes = [
        TVEpisode(title="SegmentA", episode_number=1, season_number=1),
        TVEpisode(title="SegmentB", episode_number=2, season_number=1),
    ]
    cache = {("Show", 1, None): episodes}

    tas._anthology_split_segments(
        media_file,
        rule_set,
        RuleSetConfig(anthology=True),
        ctx,
        episode_list_cache=cache,
    )

    assert len(ctx.plan.items) == 1
    item = ctx.plan.items[0]
    assert item.episode == "01-E02"
    assert "SegmentA" in item.episode_title and "SegmentB" in item.episode_title
    assert item.manual is False


def test_token_set_match_cases():
    assert tas._token_set_match("Pups Save Train", "Pups Save A Train") is True
    # Very short word should need full overlap
    assert tas._token_set_match("Go", "Going Gone") is False
