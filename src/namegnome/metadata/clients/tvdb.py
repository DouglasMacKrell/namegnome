"""TVDB (The TV Database) API client implementation."""

from datetime import datetime
from typing import Any

from namegnome.metadata.clients.base import MetadataClient
from namegnome.metadata.models import (
    ExternalIDs,
    MediaMetadata,
    MediaMetadataType,
    TVEpisode,
)
from namegnome.metadata.utils import load_fixture, normalize_title


class StubTVDBClient(MetadataClient):
    """Stub implementation of TVDB API client using fixture data.

    This client loads pre-defined responses from JSON fixtures,
    allowing for testing without making real API calls.
    """

    def __init__(self) -> None:
        """Initialize the stub TVDB client."""
        # Base image URL for constructing image URLs
        self.base_image_url = "https://artworks.thetvdb.com"

    @property
    def provider_name(self) -> str:
        """Get the name of this metadata provider.

        Returns:
            The string 'tvdb'.
        """
        return "tvdb"

    async def search_movie(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search for movies by title and optional year (stub implementation).

        Args:
            title: The movie title to search for.
            year: Optional release year to filter results.

        Returns:
            A list of movie metadata dictionaries from fixture data.
        """
        # TVDB API supports movies, but for our stub we'll focus on TV
        # The real implementation would make a similar call to their movie endpoint
        return []

    async def search_tv(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search for TV shows by title and optional year (stub implementation).

        Args:
            title: The TV show title to search for.
            year: Optional first air date year to filter results.

        Returns:
            A list of TV show metadata dictionaries from fixture data.
        """
        # Load the TV search fixture
        try:
            search_results = load_fixture("tvdb", "search_tv")
        except FileNotFoundError:
            # If fixture doesn't exist, return empty results
            return []

        # Create a normalized version of the search title for comparison
        normalized_search = normalize_title(title)

        # Filter results by title
        filtered_results = []
        for show in search_results.get("data", []):
            show_title = show.get("name", "")
            if normalized_search in normalize_title(show_title):
                # If year is provided, filter by year
                if year is not None:
                    first_aired = show.get("firstAired", "")
                    try:
                        show_year = datetime.strptime(first_aired, "%Y-%m-%d").year
                        if show_year != year:
                            continue
                    except ValueError:
                        # Skip if first air date is invalid
                        continue
                filtered_results.append(show)

        return filtered_results

    async def get_movie_details(self, movie_id: str) -> dict[str, Any]:
        """Get detailed information about a specific movie (stub implementation).

        Args:
            movie_id: The ID of the movie in TVDB.

        Returns:
            A dictionary containing detailed movie metadata from fixture data.

        Raises:
            FileNotFoundError: If the movie details fixture is not found.
        """
        # Same as with search, we'll focus on TV for the stub
        fixture_name = f"movie_details_{movie_id}"
        try:
            return load_fixture("tvdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic movie details fixture
            return load_fixture("tvdb", "movie_details")

    async def get_tv_details(self, show_id: str) -> dict[str, Any]:
        """Get detailed information about a specific TV show (stub implementation).

        Args:
            show_id: The ID of the TV show in TVDB.

        Returns:
            A dictionary containing detailed TV show metadata from fixture data.

        Raises:
            FileNotFoundError: If the TV show details fixture is not found.
        """
        fixture_name = f"tv_details_{show_id}"
        try:
            return load_fixture("tvdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic TV details fixture
            return load_fixture("tvdb", "tv_details")

    async def get_tv_season(self, show_id: str, season_number: int) -> dict[str, Any]:
        """Get detailed information about a specific TV season (stub implementation).

        Args:
            show_id: The ID of the TV show in TVDB.
            season_number: The season number to retrieve.

        Returns:
            A dictionary containing season metadata from fixture data.

        Raises:
            FileNotFoundError: If the season details fixture is not found.
        """
        fixture_name = f"tv_season_{show_id}_{season_number}"
        try:
            return load_fixture("tvdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic season details fixture
            return load_fixture("tvdb", "tv_season")

    async def get_tv_episode(
        self, show_id: str, season_number: int, episode_number: int
    ) -> dict[str, Any]:
        """Get detailed information about a specific TV episode (stub implementation).

        Args:
            show_id: The ID of the TV show in TVDB.
            season_number: The season number of the episode.
            episode_number: The episode number within the season.

        Returns:
            A dictionary containing episode metadata from fixture data.

        Raises:
            FileNotFoundError: If the episode details fixture is not found.
        """
        fixture_name = f"tv_episode_{show_id}_{season_number}_{episode_number}"
        try:
            return load_fixture("tvdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic episode details fixture
            return load_fixture("tvdb", "tv_episode")

    def map_to_media_metadata(
        self, data: dict[str, Any], media_type: MediaMetadataType
    ) -> MediaMetadata:
        """Map TVDB API response to a standardized MediaMetadata object.

        Args:
            data: The raw TVDB API response.
            media_type: The type of media represented by the data.

        Returns:
            A MediaMetadata object with the standardized data.
        """
        # Extract common fields
        provider_id = str(data.get("id", ""))

        # Create external IDs
        external_ids = ExternalIDs(
            tvdb_id=provider_id,
            imdb_id=data.get("imdbId"),
        )

        # Process based on media type
        if media_type == MediaMetadataType.TV_SHOW:
            title = data.get("name", "")
            first_aired = data.get("firstAired")
            year = None

            if first_aired:
                try:
                    year = datetime.strptime(first_aired, "%Y-%m-%d").year
                except ValueError:
                    pass

            # Extract seasons and episodes
            seasons = data.get("seasons", [])
            season_numbers = [s.get("number") for s in seasons if s.get("number") > 0]

            return MediaMetadata(
                title=title,
                media_type=media_type,
                original_title=data.get("originalName"),
                overview=data.get("overview"),
                provider=self.provider_name,
                provider_id=provider_id,
                external_ids=external_ids,
                release_date=first_aired,
                year=year,
                vote_average=data.get("rating"),
                vote_count=data.get("userRatings", {}).get("totalCount"),
                artwork=[],  # TVDB images need special handling
                genres=data.get("genres", []),
                number_of_seasons=len(season_numbers),
                number_of_episodes=data.get("episodes", {}).get("count"),
                seasons=season_numbers,
            )

        elif media_type == MediaMetadataType.TV_EPISODE:
            # Extract episode details
            episode_title = data.get("name", "")
            season_number = data.get("seasonNumber", 0)
            episode_number = data.get("number", 0)
            air_date = data.get("aired")

            # Get show details if available
            show = data.get("series", {})
            show_title = show.get("name", "Unknown Show")

            # Create episode object
            episode = TVEpisode(
                title=episode_title,
                episode_number=episode_number,
                season_number=season_number,
                absolute_number=data.get("absoluteNumber"),
                air_date=air_date,
                overview=data.get("overview"),
                runtime=data.get("runtime"),
            )

            return MediaMetadata(
                title=f"{show_title} - {episode_title}",
                media_type=media_type,
                overview=data.get("overview"),
                provider=self.provider_name,
                provider_id=provider_id,
                external_ids=external_ids,
                release_date=air_date,
                episodes=[episode],
                season_number=season_number,
                episode_number=episode_number,
            )

        # Default fallback
        return MediaMetadata(
            title=data.get("name", "Unknown"),
            media_type=media_type,
            provider=self.provider_name,
            provider_id=provider_id,
            external_ids=external_ids,
        )
