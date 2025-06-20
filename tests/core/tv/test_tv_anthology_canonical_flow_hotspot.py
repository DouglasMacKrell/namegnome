"""Failing hotspot tests that define Sprint-0.4 canonical anthology behaviour.

These tests express the *expected* (but not yet implemented) behaviour for the
anthology/double-episode flow outlined in RECOVERY_PLAN.md §0.4. They are
expected to fail until the implementation is completed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


from namegnome.core.tv.anthology import tv_anthology_split as tas
from namegnome.core.tv.tv_plan_context import TVPlanContext
from namegnome.metadata.models import TVEpisode
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan
from namegnome.rules.base import RuleSet, RuleSetConfig


class DummyRuleSet(RuleSet):
    """Simplest RuleSet that echos back the expected canonical filename."""

    def __init__(self):
        super().__init__("dummy")

    # `episode_span` is passed via **kwargs by tv_anthology_split helper.
    def target_path(
        self, media_file, base_dir=None, config=None, metadata=None, **kwargs
    ):  # type: ignore[override]
        span = kwargs.get("episode_span", "E??")
        # Canonical Plex pattern we expect: Show - S01E01-E02 - Title1 & Title2.ext
        titles = kwargs.get("joined_titles", "")
        return base_dir / f"Show - S01{span} - {titles}.mkv"

    def supports_media_type(self, media_type):  # type: ignore[override]
        return True

    @property
    def supported_media_types(self):  # type: ignore[override]
        return [MediaType.TV]


def _ctx(tmp_path: Path):
    plan = RenamePlan(
        id="plan",
        created_at=datetime.now(),
        root_dir=tmp_path,
        platform="plex",
        items=[],
        media_types=[MediaType.TV],
        metadata_providers=[],
        llm_model=None,
    )
    return TVPlanContext(plan=plan, destinations={}, case_insensitive_destinations={})


def test_canonical_span_naming(tmp_path: Path):
    """With --anthology flag, output name should follow S01E01-E02 + ampersand titles."""

    # Fake input file with two title segments in the stem.
    file_path = tmp_path / "Show - S01E01 - SegmentA SegmentB.mkv"
    file_path.touch()

    media_file = MediaFile(
        path=file_path,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    episodes = [
        TVEpisode(
            title="SegmentA", episode_number=1, season_number=1, duration_ms=600000
        ),
        TVEpisode(
            title="SegmentB", episode_number=2, season_number=1, duration_ms=600000
        ),
    ]

    cache = {("Show", 1, None): episodes}

    ctx = _ctx(tmp_path)
    tas._anthology_split_segments(
        media_file,
        DummyRuleSet(),
        RuleSetConfig(anthology=True),
        ctx,
        episode_list_cache=cache,
    )

    assert ctx.plan.items, "No plan item created"
    item = ctx.plan.items[0]
    # Expected canonical span string without season prefix per legacy format
    assert item.episode == "01-E02"
    # Joined titles should use ampersand per spec
    assert " & " in item.episode_title


def test_untrusted_titles_duration_pairing(tmp_path: Path):
    """When --untrusted-titles and --max-duration are set, episodes should be paired by duration."""

    file_path = tmp_path / "Show - UntrustedFile.mkv"
    file_path.touch()

    media_file = MediaFile(
        path=file_path,
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        season=1,
        title="Show",
    )

    episodes = [
        TVEpisode(
            title="EpOne", episode_number=1, season_number=1, duration_ms=900000
        ),  # 15 min
        TVEpisode(
            title="EpTwo", episode_number=2, season_number=1, duration_ms=900000
        ),  # 15 min
    ]
    cache = {("Show", 1, None): episodes}

    ctx = _ctx(tmp_path)
    tas._anthology_split_segments(
        media_file,
        DummyRuleSet(),
        RuleSetConfig(
            anthology=True, untrusted_titles=True, max_duration=30
        ),  # 30 min window
        ctx,
        episode_list_cache=cache,
    )

    assert ctx.plan.items, "Expected paired plan item for untrusted titles mode"
    item = ctx.plan.items[0]
    assert item.episode == "01-E02"
    assert item.episode_title == "EpOne & EpTwo"
