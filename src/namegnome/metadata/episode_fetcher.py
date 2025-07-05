"""Episode Fetcher: Converts raw API responses into a refined episode list for matching."""

from typing import List, Dict, Any
import time
import sys

# Default cache TTL (in seconds). 12 hours mirrors spec in TASK doc.
DEFAULT_TTL: int = 12 * 60 * 60

# Internal: episode cache now stores (expires_ts, episode_list)
_EPISODE_CACHE: dict[
    tuple[str, int | None, int | None, str | None], tuple[float, List[Dict[str, Any]]]
] = {}

_PROVIDER_KEYS: tuple[str, ...] = ("tvdb", "tmdb", "omdb", "anilist")

# Track unhealthy providers for the lifetime of the process – cleared by tests as needed.
_UNHEALTHY_PROVIDERS: set[str] = set()


def _build_dummy_episodes(show: str, season: int) -> List[Dict[str, Any]]:  # noqa: D401
    """Construct a deterministic dummy episode list for tests.

    Returns two episodes with predictable titles so that matching/unit-tests
    can rely on stable data without hitting external APIs.
    """

    return [
        {"season": season, "episode": 1, "title": f"{show} Episode 1"},
        {"season": season, "episode": 2, "title": f"{show} Episode 2"},
    ]


def _provider_tvdb(
    show: str, season: int | None, year: int | None = None
) -> List[Dict[str, Any]]:  # noqa: D401
    """Return a dummy TVDB episode list (placeholder for real network IO)."""

    return _build_dummy_episodes(f"TVDB {show}", season or 1)


def _provider_tmdb(
    show: str, season: int | None, year: int | None = None
) -> List[Dict[str, Any]]:  # noqa: D401
    """Return a dummy TMDB episode list."""

    return _build_dummy_episodes(f"TMDB {show}", season or 1)


def _provider_omdb(
    show: str, season: int | None, year: int | None = None
) -> List[Dict[str, Any]]:  # noqa: D401
    """Return a dummy OMDb episode list."""

    return _build_dummy_episodes(f"OMDb {show}", season or 1)


def _provider_anilist(
    show: str, season: int | None, year: int | None = None
) -> List[Dict[str, Any]]:  # noqa: D401
    """Return a dummy AniList episode list."""

    return _build_dummy_episodes(f"AniList {show}", season or 1)


def _safe_call_provider(
    provider_key: str,
    show: str,
    season: int | None,
    year: int | None,
    *,
    retries: int = 3,
) -> List[Dict[str, Any]]:
    """Attempt to fetch episodes from *provider_key* with retries.

    Args:
        provider_key: One of "tvdb", "tmdb", "omdb", "anilist".
        show: Series title.
        season: Season number (optional).
        year: Release year (optional).
        retries: How many attempts before propagating the error.
    """

    provider_func = getattr(sys.modules[__name__], f"_provider_{provider_key}")
    delay = 0.5
    for attempt in range(1, retries + 1):
        try:
            return provider_func(show, season, year)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(delay)
            # Basic exponential back-off capped at 4 seconds.
            delay = min(delay * 2, 4)


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

    provider_key = (provider or "default").lower()

    cache_key = (show.lower(), season if season is not None else -1, year, provider_key)
    now = time.time()

    # Return cached value if present and not expired.
    cached = _EPISODE_CACHE.get(cache_key)
    if cached:
        exp_ts, episodes = cached
        if exp_ts > now:
            return episodes

    # Determine provider order: explicit first, otherwise default order.
    provider_chain = [p for p in [provider] if p] or list(_PROVIDER_KEYS)

    # Ensure chain is unique & valid.
    provider_chain_extended: list[str] = []
    for p in provider_chain + list(_PROVIDER_KEYS):
        if p and p not in provider_chain_extended and p in _PROVIDER_KEYS:
            provider_chain_extended.append(p)

    episodes: List[Dict[str, Any]] | None = None
    last_exc: Exception | None = None
    for prov in provider_chain_extended:
        if prov in _UNHEALTHY_PROVIDERS:
            # Skip providers previously marked unhealthy within this run.
            continue

        try:
            episodes = _safe_call_provider(prov, show, season, year)
            if episodes:
                break
        except Exception as exc:  # noqa: BLE001
            # Mark provider unhealthy so we don't attempt again in this process.
            _UNHEALTHY_PROVIDERS.add(prov)
            last_exc = exc
            continue

    if not episodes:
        # All providers failed; re-raise last exception or fallback to dummy.
        if last_exc is not None:
            raise last_exc
        episodes = _build_dummy_episodes(show, season or 1)

    # Store in cache with TTL.
    _EPISODE_CACHE[cache_key] = (now + DEFAULT_TTL, episodes)
    return episodes
