"""Episode Fetcher: Converts raw API responses into a refined episode list for matching."""

from typing import List, Dict, Any
import time
import sys
import asyncio
from rich.prompt import Prompt
from rich.table import Table

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


async def fetch_episode_list_with_disambiguation(
    show: str,
    season: int | None,
    year: int | None = None,
    provider: str | None = None,
) -> List[Dict[str, Any]]:
    """Fetch episode list with show disambiguation support.

    When multiple series match the show name, prompts user to choose.
    Uses real metadata providers when available.

    Args:
        show: Series title to search for.
        season: Season number (optional).
        year: Release year (optional).
        provider: Specific provider to use (optional).

    Returns:
        List of episode dictionaries.
    """
    from namegnome.cli.console import console

    # Check environment for real metadata provider availability
    import os

    # Try to use real metadata providers if API keys are available
    if provider is None:
        # Auto-detect best available provider
        if os.getenv("TVDB_API_KEY"):
            provider = "tvdb"
        elif os.getenv("TMDB_API_KEY"):
            provider = "tmdb"
        elif os.getenv("OMDB_API_KEY"):
            provider = "omdb"

    if provider and _can_use_real_provider(provider):
        try:
            metadata_results = await _search_with_real_provider(show, year, provider)

            # Handle multiple series disambiguation
            if len(metadata_results) > 1:
                selected_metadata = _prompt_user_series_selection(metadata_results)
                if selected_metadata:
                    # Extract episodes from selected series
                    episodes = _extract_episodes_from_metadata(
                        selected_metadata, season
                    )
                    return episodes

            elif len(metadata_results) == 1:
                # Single result, use it directly
                episodes = _extract_episodes_from_metadata(metadata_results[0], season)
                return episodes

        except Exception as e:
            console.print(
                f"[yellow]Warning: Real provider failed ({e}), falling back to dummy data[/yellow]"
            )

    # Fallback to dummy data for tests or when real providers unavailable
    return _build_dummy_episodes(show, season or 1)


def _can_use_real_provider(provider: str) -> bool:
    """Check if we can use a real metadata provider."""
    import os

    if provider == "tvdb":
        return bool(os.getenv("TVDB_API_KEY"))
    elif provider == "tmdb":
        return bool(os.getenv("TMDB_API_KEY"))
    elif provider == "omdb":
        return bool(os.getenv("OMDB_API_KEY"))
    elif provider == "anilist":
        return True  # AniList doesn't require API key

    return False


async def _search_with_real_provider(show: str, year: int | None, provider: str):
    """Search using real metadata provider."""
    if provider == "tvdb":
        from namegnome.metadata.clients.tvdb import TVDBClient

        client = TVDBClient()
    elif provider == "tmdb":
        from namegnome.metadata.clients.tmdb import TMDBClient

        client = TMDBClient()
    elif provider == "omdb":
        from namegnome.metadata.clients.omdb import OMDbClient
        import os

        client = OMDbClient(os.getenv("OMDB_API_KEY"))
    elif provider == "anilist":
        from namegnome.metadata.clients.anilist import AniListClient

        client = AniListClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return await client.search(show, year)


def _prompt_user_series_selection(metadata_results):
    """Prompt user to select from multiple series."""
    from namegnome.cli.console import console

    # Check if we're in a non-interactive environment (tests, CI, etc.)
    import os

    if os.getenv("NAMEGNOME_NO_RICH") or os.getenv("CI"):
        # In non-interactive mode, just return the first result
        return metadata_results[0] if metadata_results else None

    console.print("\n[bold red]Multiple series found with the same name![/bold red]")
    console.print("Please select which series you want to use:\n")

    # Create a table showing the options
    table = Table()
    table.add_column("Option", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Year", style="green")
    table.add_column("Provider", style="yellow")

    for i, metadata in enumerate(metadata_results, 1):
        year_str = str(metadata.year) if metadata.year else "Unknown"
        table.add_row(str(i), metadata.title, year_str, metadata.provider)

    console.print(table)

    # Prompt for selection
    while True:
        try:
            choice = Prompt.ask(
                f"\nEnter your choice (1-{len(metadata_results)})",
                choices=[str(i) for i in range(1, len(metadata_results) + 1)],
            )
            return metadata_results[int(choice) - 1]
        except (ValueError, KeyboardInterrupt):
            console.print("[red]Invalid choice. Please try again.[/red]")


def _extract_episodes_from_metadata(metadata, season: int | None):
    """Extract episode list from metadata object."""
    episodes = []

    # Filter episodes by season if specified
    for ep in metadata.episodes:
        if season is None or ep.season_number == season:
            episodes.append(
                {
                    "season": ep.season_number,
                    "episode": ep.episode_number,
                    "title": ep.title,
                    "runtime": getattr(ep, "runtime", None),
                }
            )

    return episodes


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

    # For backwards compatibility, check if we should use real providers
    import os

    use_real_providers = (
        os.getenv("NAMEGNOME_USE_REAL_PROVIDERS", "false").lower() == "true"
    )

    if use_real_providers:
        # Use the new disambiguation-aware fetcher
        try:
            episodes = asyncio.run(
                fetch_episode_list_with_disambiguation(show, season, year, provider)
            )
        except Exception:
            # Fallback to dummy data if real providers fail
            episodes = _build_dummy_episodes(show, season or 1)
    else:
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
