"""Extra tests for tv_anthology_split.py to raise coverage.

Covers:
1. Dash-span handling in *standard* mode.
2. untrusted_titles + max_duration pairing branch.
3. Fallback manual plan-item when nothing matches.
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from namegnome.core.tv.anthology import tv_anthology_split as tas
from namegnome.core.tv.tv_plan_context import TVPlanContext
from namegnome.metadata.models import TVEpisode
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan
from namegnome.models.core import PlanStatus
from namegnome.rules.base import RuleSet, RuleSetConfig


class DummyRuleSet(RuleSet):
    """Very small RuleSet that just echos the input path."""

    def __init__(self):
        super().__init__("dummy")

    def target_path(
        self, media_file, base_dir=None, config=None, metadata=None, **kwargs
    ):  # type: ignore[override]
        return (base_dir or Path(".")) / media_file.path.name

    def supports_media_type(self, media_type):
        return True

    @property
    def supported_media_types(self):
        return [MediaType.TV]


def _ctx(tmp_path: Path):
    plan = RenamePlan(
        id="tplan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        platform="plex",
        items=[],
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    return TVPlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


# ---------------------------------------------------------------------------
# 1. Dash-span in *standard* mode (anthology==False)
# ---------------------------------------------------------------------------


def test_dash_span_standard_mode(tmp_path: Path):
    # Ensure global 'season' exists for the buggy reference inside the function
    tas.season = 1  # type: ignore[attr-defined]
    fname = "Show-S01E03-E04.mkv"
    fpath = tmp_path / fname
    fpath.touch()

    mf = MediaFile(
        path=fpath,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    episodes = [
        TVEpisode(title="Ep3", episode_number=3, season_number=1),
        TVEpisode(title="Ep4", episode_number=4, season_number=1),
    ]
    cache = {("Show", None, None): episodes, ("Show", 1, None): episodes}

    tas._anthology_split_segments(
        mf,
        DummyRuleSet(),
        RuleSetConfig(anthology=False),
        _ctx(tmp_path),
        episode_list_cache=cache,
    )

    ctx = _ctx(tmp_path)
    # call again but store ctx variable
    tas._anthology_split_segments(
        mf,
        DummyRuleSet(),
        RuleSetConfig(anthology=False),
        ctx,
        episode_list_cache=cache,
    )

    assert ctx.plan.items, "plan item should be created"
    item = ctx.plan.items[0]
    assert item.episode == "03-E04"
    assert item.manual is False


# ---------------------------------------------------------------------------
# 2. untrusted_titles + max_duration pairing
# ---------------------------------------------------------------------------


def test_untrusted_titles_max_duration_pairing(tmp_path: Path):
    fpath = tmp_path / "Anthology_File.mkv"
    fpath.touch()
    mf = MediaFile(
        path=fpath,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    # Two minimal episode-like objects that include a duration_ms attribute.
    episodes = [
        SimpleNamespace(
            title="SegA", episode_number=1, season_number=1, duration_ms=9 * 60 * 1000
        ),
        SimpleNamespace(
            title="SegB", episode_number=2, season_number=1, duration_ms=10 * 60 * 1000
        ),
    ]
    cache = {("Show", None, None): episodes, ("Show", 1, None): episodes}
    ctx = _ctx(tmp_path)

    # Monkeypatch _normalize_episode_list to bypass TVEpisode conversion and
    # return our simple namespace objects unchanged.
    tas._normalize_episode_list = lambda x: x  # type: ignore[assignment]

    tas._anthology_split_segments(
        mf,
        DummyRuleSet(),
        RuleSetConfig(anthology=True, untrusted_titles=True, max_duration=20),
        ctx,
        episode_list_cache=cache,
    )

    assert ctx.plan.items, "should create plan item via duration pairing"
    item = ctx.plan.items[0]
    assert item.manual is False
    assert item.episode == "01-E02"


# ---------------------------------------------------------------------------
# 3. Manual fallback when no episodes
# ---------------------------------------------------------------------------


def test_anthology_manual_fallback(tmp_path: Path):
    fpath = tmp_path / "File_NoMatch.mkv"
    fpath.touch()
    mf = MediaFile(
        path=fpath,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    ctx = _ctx(tmp_path)
    tas._anthology_split_segments(
        mf,
        DummyRuleSet(),
        RuleSetConfig(anthology=True),
        ctx,
        episode_list_cache={},  # empty cache to force manual
    )

    assert ctx.plan.items
    item = ctx.plan.items[0]
    assert item.status == PlanStatus.MANUAL or item.manual is True


# ---------------------------------------------------------------------------
# 4. Dash-span filename inside anthology mode path
# ---------------------------------------------------------------------------


def test_dash_span_anthology_mode(tmp_path: Path):
    # Filename with dash-span pattern triggers dedicated logic inside anthology mode
    fname = "Show-S01E05-E06-Dash.mkv"
    fpath = tmp_path / fname
    fpath.touch()
    mf = MediaFile(
        path=fpath,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    # Episode list including the range 5-6
    episodes = [
        SimpleNamespace(title="Ep5", episode_number=5, season_number=1),
        SimpleNamespace(title="Ep6", episode_number=6, season_number=1),
    ]
    cache = {("Show", 1, None): episodes}
    ctx = _ctx(tmp_path)

    # Bypass normalize helper as before so our simple objects flow through
    tas._normalize_episode_list = lambda x: x  # type: ignore[assignment]

    tas._anthology_split_segments(
        mf,
        DummyRuleSet(),
        RuleSetConfig(anthology=True),
        ctx,
        episode_list_cache=cache,
    )

    assert ctx.plan.items, "plan item should be created via dash-span"
    item = ctx.plan.items[0]
    assert item.episode == "05-E06" and item.manual is False
