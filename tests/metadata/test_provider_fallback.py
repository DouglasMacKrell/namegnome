from __future__ import annotations

import time
from typing import Any, Dict, List

import pytest

from namegnome.metadata import episode_fetcher as ef


def _dummy_episodes(tag: str, season: int = 1) -> List[Dict[str, Any]]:
    """Return a predictable dummy episode list labelled by *tag*."""
    return [
        {"season": season, "episode": 1, "title": f"{tag} Episode 1"},
        {"season": season, "episode": 2, "title": f"{tag} Episode 2"},
    ]


@pytest.mark.parametrize("retry_attempts", [1, 2, 3])
def test_provider_fallback(
    monkeypatch: pytest.MonkeyPatch, retry_attempts: int
) -> None:
    """If the primary provider fails, the fetcher must fall back to the next one."""

    # Fail the TVDB provider *retry_attempts* times to force a fallback.
    call_counts = {"tvdb": 0, "tmdb": 0, "anilist": 0}

    def fail_tvdb(*args: object, **kwargs: object):  # noqa: ANN001
        call_counts["tvdb"] += 1
        raise RuntimeError("Simulated provider failure")

    def ok_tmdb(show: str, season: int, year: int | None = None):  # type: ignore[override]
        call_counts["tmdb"] += 1
        return _dummy_episodes("TMDB", season)

    def untouched_anilist(*args: object, **kwargs: object):  # noqa: ANN001
        call_counts["anilist"] += 1
        return _dummy_episodes("AniList")

    monkeypatch.setattr(ef, "_provider_tvdb", fail_tvdb)
    monkeypatch.setattr(ef, "_provider_tmdb", ok_tmdb)
    monkeypatch.setattr(ef, "_provider_anilist", untouched_anilist)

    # Clear any existing cache to ensure a fresh call sequence.
    ef._EPISODE_CACHE.clear()  # type: ignore[attr-defined]
    if hasattr(ef, "_UNHEALTHY_PROVIDERS"):
        ef._UNHEALTHY_PROVIDERS.clear()  # type: ignore[attr-defined]

    episodes = ef.fetch_episode_list("Demo Show", 1)

    # The fallback should succeed with TMDB data
    assert episodes[0]["title"].startswith("TMDB"), "Should use TMDB fallback"
    # Expect TVDB retried, TMDB called exactly once, AniList not called
    assert call_counts["tvdb"] >= retry_attempts
    assert call_counts["tmdb"] == 1
    assert call_counts["anilist"] == 0


def test_episode_cache_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    """Episode list should be re-fetched after the TTL expires."""

    # Provide a deterministic provider that increments a counter each call.
    call_counter = {"count": 0}

    def counting_provider(show: str, season: int, year: int | None = None):  # type: ignore[override]
        call_counter["count"] += 1
        return _dummy_episodes("TVDB", season)

    # Patch only the primary provider; fallback not needed here.
    monkeypatch.setattr(ef, "_provider_tvdb", counting_provider)
    monkeypatch.setattr(ef, "_provider_tmdb", counting_provider)
    monkeypatch.setattr(ef, "_provider_anilist", counting_provider)

    # Use a very short TTL for testing.
    monkeypatch.setattr(ef, "DEFAULT_TTL", 1, raising=False)

    ef._EPISODE_CACHE.clear()  # type: ignore[attr-defined]

    # First call populates the cache
    eps1 = ef.fetch_episode_list("Foo Show", 1)
    assert call_counter["count"] == 1

    # Immediate second call should hit the cache, avoiding a provider call
    eps2 = ef.fetch_episode_list("Foo Show", 1)
    assert eps1 == eps2
    assert call_counter["count"] == 1

    # Wait for TTL to expire and call again – should trigger another provider call
    time.sleep(1.1)
    eps3 = ef.fetch_episode_list("Foo Show", 1)
    assert eps3 == eps1
    assert call_counter["count"] == 2, (
        "Provider should be called again after TTL expiry"
    )
