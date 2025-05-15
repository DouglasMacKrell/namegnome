"""AniList GraphQL client implementation.

This module provides an implementation of the MetadataClient interface for the
AniList GraphQL API, focusing on anime metadata with absolute episode numbering.
"""

from typing import Any, Dict, List, Optional

import httpx

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.models import (
    ExternalIDs,
    MediaMetadata,
    MediaMetadataType,
    TVEpisode,
)

# GraphQL queries
SEARCH_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    episodes
    type
    format
    season
    seasonYear
    airingSchedule {
      nodes {
        episode
        airingAt
      }
    }
  }
}
"""

DETAILS_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    description
    episodes
    type
    format
    season
    seasonYear
    streamingEpisodes {
      title
      thumbnail
      url
      site
    }
    airingSchedule {
      nodes {
        episode
        airingAt
      }
    }
  }
}
"""


class AniListClient(MetadataClient):
    """AniList GraphQL client for anime metadata.

    This client uses the AniList GraphQL API to fetch metadata for anime, with a
    focus on absolute episode numbering for anime series. AniList's public GraphQL
    API does not require authentication.
    """

    def __init__(self) -> None:
        """Initialize AniList client."""
        self.api_url = "https://graphql.anilist.co"

    async def search(
        self, title: str, year: Optional[int] = None
    ) -> List[MediaMetadata]:
        """Search for anime by title and optional year.

        Args:
            title: The anime title to search for.
            year: Optional release year to narrow results.

        Returns:
            A list of MediaMetadata objects matching the query.
        """
        # Prepare GraphQL variables
        variables = {"search": title}

        try:
            # Execute GraphQL query
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": SEARCH_QUERY, "variables": variables},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                # Check for errors
                if "errors" in data:
                    return []

                # Check if media was found
                if not data.get("data", {}).get("Media"):
                    return []

                # Map result to MediaMetadata
                media = data["data"]["Media"]
                metadata = self._map_to_metadata(media)

                # Filter by year if provided
                if year and metadata.year and metadata.year != year:
                    return []

                return [metadata]

        except Exception:
            return []

    async def details(self, provider_id: str) -> MediaMetadata:
        """Fetch full metadata for an anime by AniList ID.

        Args:
            provider_id: The AniList ID.

        Returns:
            A MediaMetadata object with full details.

        Raises:
            Exception: If the anime cannot be found or other API error.
        """
        # Prepare GraphQL variables
        variables = {"id": int(provider_id)}

        try:
            # Execute GraphQL query
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": DETAILS_QUERY, "variables": variables},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                # Check for errors
                if "errors" in data:
                    raise Exception(data["errors"][0]["message"])

                # Check if media was found
                if not data.get("data", {}).get("Media"):
                    raise Exception(f"No anime found for ID: {provider_id}")

                # Map result to MediaMetadata with episodes
                media = data["data"]["Media"]
                metadata = self._map_to_metadata(media)

                # Add episodes if available
                if media.get("streamingEpisodes"):
                    metadata.episodes = self._map_episodes(media)

                return metadata

        except Exception:
            raise

    def _map_to_metadata(self, media: Dict[str, Any]) -> MediaMetadata:
        """Map AniList GraphQL response to MediaMetadata object.

        Args:
            media: The AniList Media object.

        Returns:
            A MediaMetadata object with mapped fields.
        """
        # Get the best title (prefer English, fall back to romaji, then native)
        title = (
            media["title"].get("english")
            or media["title"].get("romaji")
            or media["title"].get("native")
            or "Unknown Anime"
        )

        # Create external IDs - store anilist ID in extra field
        external_ids = ExternalIDs()

        # Create metadata
        return MediaMetadata(
            title=title,
            media_type=MediaMetadataType.TV_SHOW,
            provider="anilist",
            provider_id=str(media["id"]),
            original_title=media["title"].get("native"),
            year=media.get("seasonYear"),
            number_of_episodes=media.get("episodes"),
            overview=media.get("description"),
            external_ids=external_ids,
            extra={"anilist_id": str(media["id"])},
        )

    def _map_episodes(self, media: Dict[str, Any]) -> List[TVEpisode]:
        """Map AniList streaming episodes to TVEpisode objects.

        Args:
            media: The AniList Media object.

        Returns:
            A list of TVEpisode objects with absolute numbering.
        """
        episodes = []

        for idx, episode in enumerate(media.get("streamingEpisodes", []), 1):
            # Default to episode index if no episode number is available
            tv_episode = TVEpisode(
                title=episode.get("title", f"Episode {idx}"),
                episode_number=idx,  # Use index as episode number
                season_number=1,  # Default to season 1 for anime
                absolute_number=idx,  # Same as episode number for absolute numbering
            )
            episodes.append(tv_episode)

        return episodes
