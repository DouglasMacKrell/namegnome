"""Hot-spot tests for provider-fallback episode-list fetching.

They define the minimal contract required by plan orchestration:
`fetch_episode_list(show, season, year=None, provider=None)` must return a
non-empty list of dicts with integer `season` and `episode` plus a `title`
key, regardless of provider argument.  The stub currently returns an empty
list, so these tests will fail until the implementation is completed.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from namegnome.metadata import episode_fetcher as ef


@pytest.mark.parametrize("provider", [None, "tvdb", "tmdb"])
def test_fetch_episode_list_contract(provider: str | None):
    """The fetcher must always return at least one episode dict."""

    eps: List[Dict[str, Any]] = ef.fetch_episode_list("Demo Show", 1, provider=provider)  # type: ignore[arg-type]

    # Expect non-empty list
    assert eps, "Episode list should not be empty"

    # Expect required keys and correct types on the first item
    first = eps[0]
    assert set(first).issuperset({"season", "episode", "title"})
    assert isinstance(first["season"], int) and isinstance(first["episode"], int)
    assert isinstance(first["title"], str) 