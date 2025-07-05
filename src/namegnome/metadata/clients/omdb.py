"""OMDb client for supplementing TMDB metadata in NameGnome.

Fetches ratings and plot from OMDb and merges into MediaMetadata, as required
by Sprint 2.5. TMDB fields take priority over OMDb when both are present.

Also provides a standalone OMDbClient for use in provider fallback chains.
"""

from http import HTTPStatus
from typing import List

import httpx

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.models import MediaMetadata, MediaMetadataType, TVEpisode


async def fetch_and_merge_omdb(
    tmdb_metadata: MediaMetadata,
    api_key: str,
    title: str,
    year: int,
) -> MediaMetadata:
    """Fetch OMDb data and merge IMDb rating and plot into MediaMetadata.

    TMDB fields take priority over OMDb when both are present.
    """
    url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}&y={year}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise Exception("OMDb rate limit exceeded")
        data = resp.json()
    merged = tmdb_metadata.copy()
    if merged.vote_average is None and data.get("imdbRating"):
        try:
            merged.vote_average = float(data["imdbRating"])
        except Exception:
            pass
    if merged.overview is None and data.get("Plot"):
        merged.overview = data["Plot"]
    return merged


class OMDbClient(MetadataClient):
    """Standalone OMDb client for TV show and movie metadata.

    Note: OMDb has limited episode-level data compared to TVDB/TMDB.
    This client focuses on series-level metadata for TV shows.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize OMDb client with API key.

        Args:
            api_key: OMDb API key from environment or settings.
        """
        self.api_key = api_key

    async def search(self, title: str, year: int | None = None) -> List[MediaMetadata]:
        """Search for TV shows and movies by title and optional year.

        Args:
            title: The title to search for.
            year: Optional release year to narrow results.

        Returns:
            List of MediaMetadata objects matching the query.
        """
        params = {
            "apikey": self.api_key,
            "s": title,  # Search parameter
            "type": "series",  # Focus on TV series for episode fetching
        }

        if year:
            params["y"] = str(year)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get("http://www.omdbapi.com/", params=params)
                resp.raise_for_status()

                if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    raise Exception("OMDb rate limit exceeded")

                data = resp.json()

                if data.get("Response") == "False":
                    return []

                results = []
                for item in data.get("Search", []):
                    # Convert year string to int
                    item_year = None
                    if item.get("Year"):
                        try:
                            # Handle year ranges like "2010-2015"
                            year_str = item["Year"].split("-")[0]
                            item_year = int(year_str)
                        except (ValueError, AttributeError):
                            pass

                    media = MediaMetadata(
                        title=item.get("Title", "Unknown"),
                        media_type=MediaMetadataType.TV_SHOW,
                        provider="omdb",
                        provider_id=item.get("imdbID", "unknown"),
                        year=item_year,
                        # OMDb search doesn't provide detailed metadata
                        episodes=[],
                    )
                    results.append(media)

                return results

            except httpx.HTTPError:
                return []

    async def details(self, provider_id: str) -> MediaMetadata:
        """Fetch full metadata details for a given OMDb/IMDb ID.

        Args:
            provider_id: The IMDb ID (e.g., "tt0944947").

        Returns:
            A MediaMetadata object with full details and episode list.
        """
        params = {
            "apikey": self.api_key,
            "i": provider_id,  # IMDb ID
            "plot": "full",  # Get full plot
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get("http://www.omdbapi.com/", params=params)
            resp.raise_for_status()

            if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise Exception("OMDb rate limit exceeded")

            data = resp.json()

            if data.get("Response") == "False":
                raise Exception(f"OMDb: {data.get('Error', 'Unknown error')}")

            # Convert year string to int
            year = None
            if data.get("Year"):
                try:
                    year_str = data["Year"].split("-")[0]
                    year = int(year_str)
                except (ValueError, AttributeError):
                    pass

            # Convert rating to float
            vote_average = None
            if data.get("imdbRating") and data["imdbRating"] != "N/A":
                try:
                    vote_average = float(data["imdbRating"])
                except ValueError:
                    pass

            # For TV series, try to fetch episode information
            episodes = []
            if data.get("Type") == "series" and data.get("totalSeasons"):
                try:
                    total_seasons = int(data["totalSeasons"])
                    episodes = await self._fetch_episodes(provider_id, total_seasons)
                except (ValueError, TypeError):
                    pass

            return MediaMetadata(
                title=data.get("Title", "Unknown"),
                media_type=MediaMetadataType.TV_SHOW
                if data.get("Type") == "series"
                else MediaMetadataType.MOVIE,
                provider="omdb",
                provider_id=provider_id,
                original_title=data.get("Title"),
                overview=data.get("Plot"),
                year=year,
                vote_average=vote_average,
                episodes=episodes,
                runtime=self._parse_runtime(data.get("Runtime")),
                genres=data.get("Genre", "").split(", ") if data.get("Genre") else [],
            )

    async def _fetch_episodes(
        self, imdb_id: str, total_seasons: int
    ) -> List[TVEpisode]:
        """Fetch episode list for a TV series from OMDb.

        Args:
            imdb_id: IMDb ID of the series.
            total_seasons: Number of seasons to fetch.

        Returns:
            List of TVEpisode objects.
        """
        episodes = []

        # Limit to reasonable number of seasons to avoid too many API calls
        max_seasons = min(total_seasons, 10)

        for season_num in range(1, max_seasons + 1):
            params = {
                "apikey": self.api_key,
                "i": imdb_id,
                "Season": str(season_num),
            }

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("http://www.omdbapi.com/", params=params)
                    resp.raise_for_status()

                    data = resp.json()

                    if data.get("Response") == "False":
                        continue

                    for ep_data in data.get("Episodes", []):
                        try:
                            episode_num = int(ep_data.get("Episode", 0))
                            if episode_num > 0:
                                episode = TVEpisode(
                                    title=ep_data.get(
                                        "Title", f"Episode {episode_num}"
                                    ),
                                    episode_number=episode_num,
                                    season_number=season_num,
                                    overview=ep_data.get("Plot"),
                                )
                                episodes.append(episode)
                        except (ValueError, TypeError):
                            continue

            except httpx.HTTPError:
                # Continue with other seasons if one fails
                continue

        return episodes

    def _parse_runtime(self, runtime_str: str | None) -> int | None:
        """Parse runtime string like "42 min" to integer minutes.

        Args:
            runtime_str: Runtime string from OMDb.

        Returns:
            Runtime in minutes or None if unparseable.
        """
        if not runtime_str:
            return None

        try:
            # Extract number from strings like "42 min" or "120 min"
            import re

            match = re.search(r"(\d+)", runtime_str)
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass

        return None
