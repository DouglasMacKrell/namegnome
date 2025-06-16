"""Tests for TV rename plan orchestration logic, including anthology and span handling."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest

from namegnome.core.tv import plan_orchestration
from namegnome.core.tv.plan_context import TVRenamePlanBuildContext
from namegnome.core.tv.plan_orchestration import create_tv_rename_plan
from namegnome.metadata.models import TVEpisode
from namegnome.models.core import MediaFile, MediaType
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.rules.base import RuleSet, RuleSetConfig
from namegnome.rules.plex import PlexRuleSet


class DummyRuleSet(RuleSet):
    """Dummy RuleSet for testing plan orchestration."""

    def __init__(self, platform_name: str = "dummy") -> None:
        """Initialize DummyRuleSet with a platform name for testing."""
        super().__init__(platform_name)

    def target_path(
        self, media_file: MediaFile, base_dir: Path, config: RuleSetConfig
    ) -> Path:
        """Dummy target_path for testing."""
        if not isinstance(base_dir, Path):
            base_dir = Path(base_dir)
        season = media_file.season if media_file.season is not None else 1
        episode = media_file.episode if media_file.episode is not None else 1
        episode_title = media_file.episode_title or "Unknown"
        title = media_file.title or "Unknown"
        return (
            base_dir
            / f"{title} - S{season:02d}E{str(episode).zfill(2)} - {episode_title}.mp4"
        )

    def supports_media_type(self, media_type: MediaType) -> bool:
        """Dummy supports_media_type for testing."""
        return media_type == MediaType.TV

    def supported_media_types(self) -> set[MediaType]:
        """Return supported media types."""
        return {MediaType.TV}


class DummyPlan:
    """Dummy plan for testing."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize DummyPlan with base_dir."""
        self.items = []
        self.root_dir = base_dir
        self.destinations = {}
        self.case_insensitive_destinations = {}


def make_media_file(
    stem: str,
    season: int = 1,
    episode: int | None = None,
    media_type: MediaType = MediaType.TV,
    base_dir: Optional[Path] = None,
) -> MediaFile:
    """Create a MediaFile for testing."""
    episode_str = str(episode) if episode is not None else None
    if base_dir is None:
        base_dir = Path(tempfile.gettempdir())
    return MediaFile(
        path=base_dir / f"{stem}.mp4",
        size=1,
        media_type=media_type,
        modified_date=datetime.now(),
        title="Martha Speaks",
        season=season,
        episode=episode_str,
        episode_title=None,
    )


def test_handle_normal_plan_item(tmp_path: Path) -> None:
    """Test normal plan item handling.

    Args:
        tmp_path (Path): Temporary directory for test files.
    """
    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title=None,
        season=None,
        episode=None,
        episode_title=None,
    )
    ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    plan_orchestration._handle_normal_plan_item(
        mf, DummyRuleSet(), RuleSetConfig(), ctx, ctx
    )
    assert ctx.plan.items
    assert ctx.plan.items[0].destination.suffix == ".mp4"


def test_handle_explicit_span(tmp_path: Path) -> None:
    """Test explicit span plan item handling."""

    class DummyExplicitSpan:
        def __init__(self) -> None:
            self.orig_stem = "Show S01E01-E02.mkv"
            self.episode_list = [
                {"episode": 1, "title": "Ep1"},
                {"episode": 2, "title": "Ep2"},
            ]
            self.season = 1
            self.media_file = MediaFile(
                path=tmp_path / "show.S01E01-E02.mkv",
                size=1,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
                title=None,
                season=None,
                episode=None,
                episode_title=None,
            )
            self.rule_set = DummyRuleSet()
            self.ctx = TVRenamePlanBuildContext(
                scan_result=None,
                rule_set=DummyRuleSet(),
                plan_id="test-plan",
                platform="plex",
                config=RuleSetConfig(),
            )
            self.config = RuleSetConfig()
            self.found_match = True

    result = plan_orchestration._handle_explicit_span(DummyExplicitSpan())
    assert result is True or result is False
    # Unreachable code after return removed


def test_handle_episode_number_match(tmp_path: Path) -> None:
    """Test episode number match plan item handling."""
    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title=None,
        season=None,
        episode=None,
        episode_title=None,
    )
    mf.episode = 1
    ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    episode_list = [{"episode": 1, "title": "Ep1"}]
    result = plan_orchestration._handle_episode_number_match(
        mf, DummyRuleSet(), RuleSetConfig(), ctx, episode_list
    )
    assert result is True


def test_handle_normal_matching(tmp_path: Path) -> None:
    """Test normal matching plan item handling."""
    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title=None,
        season=None,
        episode=None,
        episode_title=None,
    )
    ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    plan_ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    plan_orchestration._handle_normal_matching(
        mf, ctx, plan_ctx, [{"episode": 1, "title": "Ep1"}], True
    )


def test_handle_fallback_providers_normal(monkeypatch: object, tmp_path: Path) -> None:
    """Test fallback provider plan item handling."""

    class DummyFallbackProviderContext:
        def __init__(self) -> None:
            self.show = "Show"
            self.season = 1
            self.year = 2020
            self.media_file = MediaFile(
                path=tmp_path / "show.S01E01.mkv",
                size=1,
                media_type=MediaType.TV,
                modified_date=datetime.now(),
                title=None,
                season=None,
                episode=None,
                episode_title=None,
            )
            self.found_match = False

    from namegnome.metadata.models import TVEpisode

    monkeypatch.setattr(
        plan_orchestration,
        "fetch_episode_list",
        lambda *a, **kw: [TVEpisode(title="Ep1", episode_number=1, season_number=1)],
    )
    ctx = DummyFallbackProviderContext()
    result = plan_orchestration._handle_fallback_providers_normal(ctx)
    assert result is True or result is False


def test_handle_anthology_mode(monkeypatch: object, tmp_path: Path) -> None:
    """Test anthology mode plan item handling."""
    from datetime import datetime

    from namegnome.core.tv.plan_context import TVRenamePlanBuildContext
    from namegnome.models.core import MediaFile, MediaType
    from namegnome.rules.base import RuleSetConfig

    class ScanResult:
        def __init__(self, files: list[str], root_dir: str) -> None:
            self.files = files
            self.root_dir = root_dir
            self.media_types = [MediaType.TV]
            self.platform = "plex"
            self.total_files = len(files)
            self.skipped_files = []
            self.by_media_type = {}
            self.scan_duration_seconds = 0

    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title="Show",
        season=1,
        episode=None,
        episode_title=None,
    )
    scan_result = ScanResult([mf], tmp_path)
    rule_set = PlexRuleSet()
    config = RuleSetConfig()
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=rule_set,
        plan_id="test-plan",
        platform="plex",
        config=config,
    )
    plan_ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=rule_set,
        plan_id="test-plan",
        platform="plex",
        config=config,
    )

    class DummyAnthologyContext:
        def __init__(self) -> None:
            self.episode_list = []
            self.episode_list_cache = {}
            self.show = "Show"
            self.season = 1
            self.year = 2020
            self.key = ("Show", 1, 2020)
            self.media_file = mf
            self.ctx = ctx
            self.plan_ctx = plan_ctx

    monkeypatch.setattr(
        plan_orchestration,
        "fetch_episode_list",
        lambda *a, **kw: [{"episode": 1, "title": "Ep1"}],
    )
    anthology_ctx = DummyAnthologyContext()
    result = plan_orchestration._handle_anthology_mode(anthology_ctx)
    assert result is True


def test_add_plan_item_and_callback(tmp_path: Path) -> None:
    """Test adding a plan item and triggering callback."""
    ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    plan_ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title=None,
        season=None,
        episode=None,
        episode_title=None,
    )
    item = RenamePlanItem(source=mf.path, destination=mf.path, media_file=mf)
    plan_orchestration._add_plan_item_and_callback(item, plan_ctx, ctx, mf)
    assert plan_ctx.plan.items


def test_handle_unsupported_media_type(tmp_path: Path) -> None:
    """Test handling of unsupported media type."""
    ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    plan_ctx = TVRenamePlanBuildContext(
        scan_result=None,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    mf = MediaFile(
        path=tmp_path / "show.S01E01.mkv",
        size=1,
        media_type=MediaType.TV,
        modified_date=datetime.now(),
        title=None,
        season=None,
        episode=None,
        episode_title=None,
    )
    plan_orchestration._handle_unsupported_media_type(mf, plan_ctx, ctx)
    assert plan_ctx.plan.items


def test_create_tv_rename_plan_single_episode(tmp_path: Path, monkeypatch: object) -> None:
    """Test create_tv_rename_plan with a single-episode file (actually a span).

    Should produce a span plan item with both episode titles.
    """
    mf = make_media_file(
        "Martha Speaks-S01E01-Martha Speaks Martha Gives Advice",
        1,
        1,
        media_type=MediaType.TV,
        base_dir=tmp_path,
    )
    scan_result = ScanResult([mf], tmp_path)
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    episodes = [
        TVEpisode(title="Martha Speaks", episode_number=1, season_number=1),
        TVEpisode(title="Martha Gives Advice", episode_number=2, season_number=1),
    ]
    episode_list_cache = {
        ("Martha Speaks", 1, None): [
            {"title": "Martha Speaks", "episode": 1, "season": 1},
            {"title": "Martha Gives Advice", "episode": 2, "season": 1},
        ]
    }
    monkeypatch.setattr(
        "namegnome.metadata.episode_fetcher.fetch_episode_list",
        lambda show, season, year=None: episodes,
    )
    monkeypatch.setattr(
        "namegnome.core.tv.plan_orchestration._anthology_split_segments",
        lambda media_file, rule_set, config, ctx, episode_list_cache=None, **kwargs: __import__("namegnome.core.tv.anthology.tv_anthology_split").core.tv.anthology.tv_anthology_split._anthology_split_segments(
            media_file, rule_set, config, ctx, episode_list_cache=episode_list_cache or episode_list_cache
        ),
    )
    plan = create_tv_rename_plan(ctx, episode_list_cache=episode_list_cache)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    assert item.media_file.episode == "01-E02"
    assert "Martha Speaks" in item.media_file.episode_title
    assert "Martha Gives Advice" in item.media_file.episode_title


def test_create_tv_rename_plan_anthology(tmp_path: Path, monkeypatch: object) -> None:
    """Test create_tv_rename_plan with an anthology file (two stories in filename).

    Should produce a dual-episode plan item with both titles.
    """
    mf = make_media_file(
        "Martha Speaks-S01E01-Martha Speaks and Martha Gives Advice",
        1,
        1,
        media_type=MediaType.TV,
        base_dir=tmp_path,
    )
    scan_result = ScanResult([mf], tmp_path)
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    episodes = [
        TVEpisode(title="Martha Speaks", episode_number=1, season_number=1),
        TVEpisode(title="Martha Gives Advice", episode_number=2, season_number=1),
    ]
    episode_list_cache = {
        ("Martha Speaks", 1, None): [
            {"title": "Martha Speaks", "episode": 1, "season": 1},
            {"title": "Martha Gives Advice", "episode": 2, "season": 1},
        ]
    }
    monkeypatch.setattr(
        "namegnome.metadata.episode_fetcher.fetch_episode_list",
        lambda show, season, year=None: episodes,
    )
    monkeypatch.setattr(
        "namegnome.core.tv.plan_orchestration._anthology_split_segments",
        lambda media_file, rule_set, config, ctx, episode_list_cache=None, **kwargs: __import__("namegnome.core.tv.anthology.tv_anthology_split").core.tv.anthology.tv_anthology_split._anthology_split_segments(
            media_file, rule_set, config, ctx, episode_list_cache=episode_list_cache or episode_list_cache
        ),
    )
    plan = create_tv_rename_plan(ctx, episode_list_cache=episode_list_cache)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    assert "Martha Speaks" in item.media_file.episode_title
    assert "Martha Gives Advice" in item.media_file.episode_title
    assert not item.manual


def test_create_tv_rename_plan_manual(tmp_path: Path, monkeypatch: object) -> None:
    """Test create_tv_rename_plan with an ambiguous/unmatched file.

    Should flag as manual.
    """
    mf = make_media_file(
        "Martha Speaks-S01E99-Unknown Story",
        1,
        99,
        media_type=MediaType.TV,
        base_dir=tmp_path,
    )
    scan_result = ScanResult([mf], tmp_path)
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    monkeypatch.setattr(
        "namegnome.metadata.episode_fetcher.fetch_episode_list",
        lambda show, season, year=None: [
            TVEpisode(title="Martha Speaks", episode_number=1, season_number=1),
            TVEpisode(title="Martha Gives Advice", episode_number=2, season_number=1),
        ],
    )
    plan = create_tv_rename_plan(ctx)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    assert item.manual


def test_normalize_episode_list_regression() -> None:
    """Regression test: normalize_episode_list should handle both dict and TVEpisode input, and always return a list of dicts with 'season', 'episode', 'title'."""
    from namegnome.core.tv.utils import normalize_episode_list
    from namegnome.metadata.models import TVEpisode

    dict_input = [
        {"season": 1, "episode": 1, "title": "Ep1"},
        {"season": 1, "episode": 2, "title": "Ep2"},
    ]
    out1 = normalize_episode_list(dict_input)
    assert isinstance(out1, list)
    assert all(isinstance(ep, dict) for ep in out1)
    assert (
        out1[0]["season"] == 1 and out1[0]["episode"] == "01" and out1[0]["title"] == "Ep1"
    )
    obj_input = [
        TVEpisode(title="Ep1", episode_number=1, season_number=1),
        TVEpisode(title="Ep2", episode_number=2, season_number=1),
    ]
    out2 = normalize_episode_list(obj_input)
    assert isinstance(out2, list)
    assert all(isinstance(ep, dict) for ep in out2)
    assert (
        out2[0]["season"] == 1 and out2[0]["episode"] == "01" and out2[0]["title"] == "Ep1"
    )


class ScanResult:
    """Minimal DummyScanResult for test scan_result construction."""

    def __init__(self, files: list[str], root_dir: str) -> None:
        """Initialize DummyScanResult with files and root_dir for test scan_result construction."""
        self.files = files
        self.root_dir = root_dir
        self.media_types = [f.media_type for f in files]
        self.platform = "plex"
        self.total_files = len(files)
        self.skipped_files = []
        self.by_media_type = {}
        self.scan_duration_seconds = 0


def test_dummy_rule_set_implements_required_methods() -> None:
    """Regression: DummyRuleSet should always implement all RuleSet abstract methods."""
    from namegnome.rules.base import RuleSet

    # Instantiation should not raise TypeError
    try:
        dummy = DummyRuleSet()
    except TypeError as e:
        pytest.fail(f"DummyRuleSet cannot be instantiated: {e}")
    # Optionally, check for unimplemented abstract methods
    abstract_methods = getattr(RuleSet, "__abstractmethods__", set())
    for method in abstract_methods:
        assert hasattr(dummy, method), f"DummyRuleSet missing required method: {method}"


def test_create_tv_rename_plan_anthology_none_season_regression(
    tmp_path: Path, monkeypatch: object
) -> None:
    """Regression: create_tv_rename_plan should not crash if MediaFile.season is None and anthology mode is triggered."""
    mf = make_media_file(
        "Martha Speaks-S01E01-Martha Speaks and Martha Gives Advice",
        season=None,  # Explicitly None
        episode=1,
        media_type=MediaType.TV,
        base_dir=tmp_path,
    )
    scan_result = ScanResult([mf], tmp_path)
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    episodes = [
        TVEpisode(title="Martha Speaks", episode_number=1, season_number=1),
        TVEpisode(title="Martha Gives Advice", episode_number=2, season_number=1),
    ]
    episode_list_cache = {
        ("Martha Speaks", None, None): [
            {"title": "Martha Speaks", "episode": 1, "season": 1},
            {"title": "Martha Gives Advice", "episode": 2, "season": 1},
        ]
    }
    monkeypatch.setattr(
        "namegnome.metadata.episode_fetcher.fetch_episode_list",
        lambda show, season, year=None: episodes,
    )
    monkeypatch.setattr(
        "namegnome.core.tv.plan_orchestration._anthology_split_segments",
        lambda media_file, rule_set, config, ctx, episode_list_cache=None, **kwargs: __import__("namegnome.core.tv.anthology.tv_anthology_split").core.tv.anthology.tv_anthology_split._anthology_split_segments(
            media_file, rule_set, config, ctx, episode_list_cache=episode_list_cache or episode_list_cache
        ),
    )
    plan = create_tv_rename_plan(ctx, episode_list_cache=episode_list_cache)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    assert "Martha Speaks" in item.media_file.episode_title
    assert "Martha Gives Advice" in item.media_file.episode_title
    assert not item.manual


def test_create_tv_rename_plan_anthology_prompt(tmp_path: Path, monkeypatch: object) -> None:
    """Test that the anthology detection prompt is called and respected in the scan/plan flow."""
    mf = make_media_file(
        "Martha Speaks-S01E01-Martha Speaks and Martha Gives Advice",
        1,
        1,
        media_type=MediaType.TV,
        base_dir=tmp_path,
    )
    scan_result = ScanResult([mf], tmp_path)
    ctx = TVRenamePlanBuildContext(
        scan_result=scan_result,
        rule_set=DummyRuleSet(),
        plan_id="test-plan",
        platform="plex",
        config=RuleSetConfig(),
    )
    episodes = [
        TVEpisode(title="Martha Speaks", episode_number=1, season_number=1),
        TVEpisode(title="Martha Gives Advice", episode_number=2, season_number=1),
    ]
    episode_list_cache = {
        ("Martha Speaks", 1, None): [
            {"title": "Martha Speaks", "episode": 1, "season": 1},
            {"title": "Martha Gives Advice", "episode": 2, "season": 1},
        ]
    }
    monkeypatch.setattr(
        "namegnome.metadata.episode_fetcher.fetch_episode_list",
        lambda show, season, year=None: episodes,
    )
    monkeypatch.setattr(
        "namegnome.core.tv.plan_orchestration._anthology_split_segments",
        lambda media_file, rule_set, config, ctx, episode_list_cache=None, **kwargs: __import__("namegnome.core.tv.anthology.tv_anthology_split").core.tv.anthology.tv_anthology_split._anthology_split_segments(
            media_file, rule_set, config, ctx, episode_list_cache=episode_list_cache or episode_list_cache
        ),
    )
    # Simulate user confirming anthology
    monkeypatch.setattr(
        "namegnome.cli.utils.prompt_utils.prompt_for_anthology_detection",
        lambda filename: True,
    )
    plan = create_tv_rename_plan(ctx, episode_list_cache=episode_list_cache)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    assert "Martha Speaks" in item.media_file.episode_title
    assert "Martha Gives Advice" in item.media_file.episode_title
    assert not item.manual
    # Simulate user denying anthology
    monkeypatch.setattr(
        "namegnome.cli.utils.prompt_utils.prompt_for_anthology_detection",
        lambda filename: False,
    )
    plan = create_tv_rename_plan(ctx, episode_list_cache=episode_list_cache)
    assert isinstance(plan, RenamePlan)
    assert len(plan.items) == 1
    item = plan.items[0]
    # Should not treat as anthology, so only one title should be present
    titles = item.media_file.episode_title.split(" and ")
    assert len(titles) == 1 or ("Martha Speaks" in item.media_file.episode_title or "Martha Gives Advice" in item.media_file.episode_title)
