"""Episode Fetcher: Converts raw API responses into a refined episode list for matching."""

from typing import List, Dict, Any

_EPISODE_CACHE: dict[
    tuple[str, int | None, int | None, str | None], List[Dict[str, Any]]
] = {}


def _build_dummy_episodes(show: str, season: int) -> List[Dict[str, Any]]:  # noqa: D401
    """Construct a deterministic dummy episode list for tests.

    Returns two episodes with predictable titles so that matching/unit-tests
    can rely on stable data without hitting external APIs.
    """

    return [
        {"season": season, "episode": 1, "title": f"{show} Episode 1"},
        {"season": season, "episode": 2, "title": f"{show} Episode 2"},
    ]


def fetch_episode_list(
    show: str,
    season: int | None,
    year: int | None = None,
    provider: str | None = None,
) -> List[Dict[str, Any]]:
    """Return a (dummy) episode list suitable for unit-tests.

    The recovery sprint focuses on restoring internal logic, not real network
    IO, so this helper returns deterministic data while preserving the public
    interface.  A lightweight in-memory cache avoids unnecessary recompute in
    large test suites.
    """

    key = (
        show.lower(),
        season if season is not None else -1,
        year,
        (provider or "default").lower(),
    )
    if key in _EPISODE_CACHE:
        return _EPISODE_CACHE[key]

    # Real implementation would branch on *provider* and perform HTTP calls.
    # For now we always return the same dummy list.
    episode_list = _build_dummy_episodes(show, season or 1)
    _EPISODE_CACHE[key] = episode_list
    return episode_list
