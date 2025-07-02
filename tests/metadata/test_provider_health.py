from __future__ import annotations

from typing import Any, Dict, List

import pytest

from namegnome.metadata import episode_fetcher as ef


def _dummy_episodes(tag: str, season: int = 1) -> List[Dict[str, Any]]:
    return [
        {"season": season, "episode": 1, "title": f"{tag} Episode 1"},
        {"season": season, "episode": 2, "title": f"{tag} Episode 2"},
    ]


def test_unhealthy_provider_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A provider that repeatedly errors should be skipped on subsequent calls."""

    call_counts = {"tvdb": 0, "tmdb": 0}

    def always_fails(*args: object, **kwargs: object):  # noqa: ANN001
        call_counts["tvdb"] += 1
        raise RuntimeError("Simulated 5xx error")

    def ok_tmdb(show: str, season: int, year: int | None = None):  # type: ignore[override]
        call_counts["tmdb"] += 1
        return _dummy_episodes("TMDB", season)

    monkeypatch.setattr(ef, "_provider_tvdb", always_fails)
    monkeypatch.setattr(ef, "_provider_tmdb", ok_tmdb)
    # Ensure aniList not in chain for this test to isolate behaviour
    monkeypatch.setattr(ef, "_provider_anilist", ok_tmdb)

    # Reset global state
    ef._EPISODE_CACHE.clear()  # type: ignore[attr-defined]
    if hasattr(ef, "_UNHEALTHY_PROVIDERS"):
        ef._UNHEALTHY_PROVIDERS.clear()  # type: ignore[attr-defined]

    # First fetch triggers failure → fallback
    eps1 = ef.fetch_episode_list("Test Show", 1)
    assert eps1[0]["title"].startswith("TMDB")
    first_tvdb_calls = call_counts["tvdb"]
    assert first_tvdb_calls >= 1
    assert call_counts["tmdb"] == 1
    assert "tvdb" in ef._UNHEALTHY_PROVIDERS  # type: ignore[attr-defined]

    # Clear only episode cache to force fetch logic again
    ef._EPISODE_CACHE.clear()  # type: ignore[attr-defined]

    # Second fetch should NOT call tvdb again
    eps2 = ef.fetch_episode_list("Test Show", 1)
    assert eps2 == eps1
    assert call_counts["tmdb"] == 2  # tmdb called again
    assert call_counts["tvdb"] == first_tvdb_calls  # unchanged: tvdb skipped
