# WARNING: API key loading from .env is for LOCAL DEVELOPMENT ONLY.
# Never commit your .env file or distribute your API keys.

"""TMDB metadata provider client.

Implements the MetadataClient interface for The Movie Database (TMDB) API.
"""

import logging

import httpx

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.clients.omdb import fetch_and_merge_omdb
from namegnome.metadata.models import ArtworkImage, MediaMetadata, MediaMetadataType
from namegnome.metadata.settings import Settings

# mypy: ignore-errors
# See docs/KNOWN_ISSUES.md for context on the persistent mypy false positive in
# this file.

YEAR_LENGTH = 4  # Minimum length for a valid year string


class TMDBClient(MetadataClient):
    """Client for The Movie Database (TMDB) API.

    Loads API key from environment via Settings. Implements search and details
    lookups for movies and TV shows.
    """

    def __init__(self) -> None:
        """Initialize TMDBClient and load API keys from settings."""
        self.settings = Settings()
        self.api_key = self.settings.TMDB_API_KEY
        self.read_access_token = self.settings.TMDB_READ_ACCESS_TOKEN

    async def search(self, title: str, year: int | None = None) -> list[MediaMetadata]:
        """Search for movies and TV shows by title and optional year (minimal).

        Args:
            title: The title to search for.
            year: Optional year to filter results.

        Returns:
            List of MediaMetadata objects for matching movies and TV shows.
        """
        results: list[MediaMetadata] = []
        # Movie search
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"query": title, "api_key": self.api_key}
        if year:
            params["year"] = year
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        for item in data.get("results", []):
            # Remove debug logging to resolve E501
            year: int | None = _extract_year(item.get("release_date"))
            media = MediaMetadata(
                title=item["title"],
                media_type=MediaMetadataType.MOVIE,
                original_title=item.get("original_title"),
                overview=item.get("overview"),
                provider="tmdb",
                provider_id=str(item["id"]),
                vote_average=item.get("vote_average"),
                vote_count=item.get("vote_count"),
                popularity=item.get("popularity"),
            )
            media.year = year  # type: ignore[assignment]
            results.append(media)
        # TV search (minimal: always also search TV endpoint)
        url_tv = "https://api.themoviedb.org/3/search/tv"
        params_tv = {"query": title, "api_key": self.api_key}
        async with httpx.AsyncClient() as client:
            resp_tv = await client.get(url_tv, params=params_tv)
            resp_tv.raise_for_status()
            data_tv = resp_tv.json()
        for item in data_tv.get("results", []):
            results.append(
                MediaMetadata(
                    title=item["name"],
                    media_type=MediaMetadataType.TV_SHOW,
                    original_title=item.get("original_name"),
                    overview=item.get("overview"),
                    provider="tmdb",
                    provider_id=str(item["id"]),
                    year=_extract_year(item.get("first_air_date")),
                    vote_average=item.get("vote_average"),
                    vote_count=item.get("vote_count"),
                    popularity=item.get("popularity"),
                )
            )
        return results

    async def details(
        self, provider_id: str, media_type: MediaMetadataType
    ) -> MediaMetadata:
        """Fetch full metadata details for a given TMDB ID and media type.

        Args:
            provider_id: The TMDB ID for the movie or TV show.
            media_type: The type of media (movie or TV_SHOW).

        Returns:
            MediaMetadata object with full details and artwork.

        Raises:
            ValueError: If media_type is not supported.
        """
        params = {"api_key": self.api_key}
        image_base = "https://image.tmdb.org/t/p/"
        async with httpx.AsyncClient() as client:
            if media_type == MediaMetadataType.MOVIE:
                url = f"https://api.themoviedb.org/3/movie/{provider_id}"
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                artwork = []
                if data.get("poster_path"):
                    artwork.append(
                        ArtworkImage(
                            url=f"{image_base}w500{data['poster_path']}",  # type: ignore[arg-type]
                            type="poster",
                            provider="tmdb",
                        )
                    )
                if data.get("backdrop_path"):
                    artwork.append(
                        ArtworkImage(
                            url=f"{image_base}w780{data['backdrop_path']}",  # type: ignore[arg-type]
                            type="backdrop",
                            provider="tmdb",
                        )
                    )
                logging.debug(f"TMDB details: id={data['id']}")
                year: int | None = _extract_year(data.get("release_date"))
                meta = MediaMetadata(
                    title=data["title"],
                    media_type=MediaMetadataType.MOVIE,
                    original_title=data.get("original_title"),
                    overview=data.get("overview"),
                    provider="tmdb",
                    provider_id=str(data["id"]),
                    year=year,
                    vote_average=data.get("vote_average"),
                    vote_count=data.get("vote_count"),
                    popularity=data.get("popularity"),
                    artwork=artwork,
                )
                # OMDb supplement: only if OMDB_API_KEY is set
                omdb_key = self.settings.OMDB_API_KEY
                if omdb_key:
                    meta = await fetch_and_merge_omdb(
                        meta, omdb_key, data["title"], year or 0
                    )
                return meta
            elif media_type == MediaMetadataType.TV_SHOW:
                url = f"https://api.themoviedb.org/3/tv/{provider_id}"
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                artwork = []
                if data.get("poster_path"):
                    artwork.append(
                        ArtworkImage(
                            url=f"{image_base}w500{data['poster_path']}",  # type: ignore[arg-type]
                            type="poster",
                            provider="tmdb",
                        )
                    )
                if data.get("backdrop_path"):
                    artwork.append(
                        ArtworkImage(
                            url=f"{image_base}w780{data['backdrop_path']}",  # type: ignore[arg-type]
                            type="backdrop",
                            provider="tmdb",
                        )
                    )
                return MediaMetadata(
                    title=data["name"],
                    media_type=MediaMetadataType.TV_SHOW,
                    original_title=data.get("original_name"),
                    overview=data.get("overview"),
                    provider="tmdb",
                    provider_id=str(data["id"]),
                    year=_extract_year(data.get("first_air_date")),
                    vote_average=data.get("vote_average"),
                    vote_count=data.get("vote_count"),
                    popularity=data.get("popularity"),
                    artwork=artwork,
                )
            else:
                raise ValueError(f"Unsupported media_type: {media_type}")


def _extract_year(date_str: str | None) -> int | None:
    """Extracts the year as int from a YYYY-MM-DD string, or returns None."""
    if date_str and len(date_str) >= YEAR_LENGTH and date_str[:YEAR_LENGTH].isdigit():
        return int(date_str[:YEAR_LENGTH])
    return None
