"""TMDB (The Movie Database) API client implementation."""

from datetime import datetime
from typing import Any

from pydantic import HttpUrl

from namegnome.metadata.clients.base import MetadataClient
from namegnome.metadata.models import (
    ArtworkImage,
    ExternalIDs,
    MediaMetadata,
    MediaMetadataType,
    TVEpisode,
)
from namegnome.metadata.utils import load_fixture, normalize_title


class StubTMDBClient(MetadataClient):
    """Stub implementation of TMDB API client using fixture data.

    This client loads pre-defined responses from JSON fixtures,
    allowing for testing without making real API calls.
    """

    def __init__(self) -> None:
        """Initialize the stub TMDB client."""
        # Default base URLs for constructing image URLs
        self.base_image_url = "https://image.tmdb.org/t/p/"
        self.poster_size = "w500"
        self.backdrop_size = "w1280"

    @property
    def provider_name(self) -> str:
        """Get the name of this metadata provider.

        Returns:
            The string 'tmdb'.
        """
        return "tmdb"

    async def search_movie(
        self, title: str, year: int | None = None
    ) -> list[dict[str, Any]]:
        """Search for movies by title and optional year (stub implementation).

        Args:
            title: The movie title to search for.
            year: Optional release year to filter results.

        Returns:
            A list of movie metadata dictionaries from fixture data.
        """
        # Load the movie search fixture
        try:
            search_results = load_fixture("tmdb", "search_movie")
        except FileNotFoundError:
            # If fixture doesn't exist, return empty results
            return []

        # Create a normalized version of the search title for comparison
        normalized_search = normalize_title(title)

        # Filter results by title
        filtered_results = []
        for movie in search_results.get("results", []):
            movie_title = movie.get("title", "")
            if normalized_search in normalize_title(movie_title):
                # If year is provided, filter by year
                if year is not None:
                    release_date = movie.get("release_date", "")
                    try:
                        movie_year = datetime.strptime(release_date, "%Y-%m-%d").year
                        if movie_year != year:
                            continue
                    except ValueError:
                        # Skip if release date is invalid
                        continue
                filtered_results.append(movie)

        return filtered_results

    async def search_tv(
        self, title: str, year: int | None = None
    ) -> list[dict[str, Any]]:
        """Search for TV shows by title and optional year (stub implementation).

        Args:
            title: The TV show title to search for.
            year: Optional first air date year to filter results.

        Returns:
            A list of TV show metadata dictionaries from fixture data.
        """
        # Load the TV search fixture
        try:
            search_results = load_fixture("tmdb", "search_tv")
        except FileNotFoundError:
            # If fixture doesn't exist, return empty results
            return []

        # Create a normalized version of the search title for comparison
        normalized_search = normalize_title(title)

        # Filter results by title
        filtered_results = []
        for show in search_results.get("results", []):
            show_title = show.get("name", "")
            if normalized_search in normalize_title(show_title):
                # If year is provided, filter by year
                if year is not None:
                    first_air_date = show.get("first_air_date", "")
                    try:
                        show_year = datetime.strptime(first_air_date, "%Y-%m-%d").year
                        if show_year != year:
                            continue
                    except ValueError:
                        # Skip if first air date is invalid
                        continue
                filtered_results.append(show)

        return filtered_results

    async def get_movie_details(
        self, movie_id: str
    ) -> dict[str, Any]:
        """Get detailed information about a specific movie (stub implementation).

        Args:
            movie_id: The ID of the movie in TMDB.

        Returns:
            A dictionary containing detailed movie metadata from fixture data.

        Raises:
            FileNotFoundError: If the movie details fixture is not found.
        """
        fixture_name = f"movie_details_{movie_id}"
        try:
            return load_fixture("tmdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic movie details fixture
            return load_fixture("tmdb", "movie_details")

    async def get_tv_details(
        self, show_id: str
    ) -> dict[str, Any]:
        """Get detailed information about a specific TV show (stub implementation).

        Args:
            show_id: The ID of the TV show in TMDB.

        Returns:
            A dictionary containing detailed TV show metadata from fixture data.

        Raises:
            FileNotFoundError: If the TV show details fixture is not found.
        """
        fixture_name = f"tv_details_{show_id}"
        try:
            return load_fixture("tmdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic TV details fixture
            return load_fixture("tmdb", "tv_details")

    async def get_tv_season(
        self, show_id: str, season_number: int
    ) -> dict[str, Any]:
        """Get detailed information about a specific TV season (stub implementation).

        Args:
            show_id: The ID of the TV show in TMDB.
            season_number: The season number to retrieve.

        Returns:
            A dictionary containing season metadata from fixture data.

        Raises:
            FileNotFoundError: If the season details fixture is not found.
        """
        fixture_name = f"tv_season_{show_id}_{season_number}"
        try:
            return load_fixture("tmdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic season details fixture
            return load_fixture("tmdb", "tv_season")

    async def get_tv_episode(
        self,
        show_id: str,
        season_number: int,
        episode_number: int,
    ) -> dict[str, Any]:
        """Get detailed information about a specific TV episode (stub implementation).

        Args:
            show_id: The ID of the TV show in TMDB.
            season_number: The season number of the episode.
            episode_number: The episode number within the season.

        Returns:
            A dictionary containing episode metadata from fixture data.

        Raises:
            FileNotFoundError: If the episode details fixture is not found.
        """
        fixture_name = f"tv_episode_{show_id}_{season_number}_{episode_number}"
        try:
            return load_fixture("tmdb", fixture_name)
        except FileNotFoundError:
            # Fallback to generic episode details fixture
            return load_fixture("tmdb", "tv_episode")

    def _create_image_url(
        self, path: str, size: str
    ) -> HttpUrl:
        """Create an HttpUrl for an image path.

        Args:
            path: The image path (e.g., "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg").
            size: The size to use (e.g., "w500").

        Returns:
            An HttpUrl instance for the image URL.
        """
        url_str = f"{self.base_image_url}{size}{path}"
        return HttpUrl(url_str)

    def map_to_media_metadata(
        self, data: dict[str, Any], media_type: MediaMetadataType
    ) -> MediaMetadata:
        """Map TMDB API response to a standardized MediaMetadata object.

        Args:
            data: The raw TMDB API response.
            media_type: The type of media represented by the data.

        Returns:
            A MediaMetadata object with the standardized data.
        """
        # Extract common fields
        provider_id = str(data.get("id", ""))

        # Create external IDs
        external_ids = ExternalIDs(tmdb_id=provider_id, imdb_id=data.get("imdb_id"))

        # Create artwork URLs
        artwork = []
        if poster_path := data.get("poster_path"):
            artwork.append(
                ArtworkImage(
                    url=self._create_image_url(poster_path, self.poster_size),
                    type="poster",
                    provider=self.provider_name,
                )
            )

        if backdrop_path := data.get("backdrop_path"):
            artwork.append(
                ArtworkImage(
                    url=self._create_image_url(backdrop_path, self.backdrop_size),
                    type="backdrop",
                    provider=self.provider_name,
                )
            )

        # Extract genres as strings
        genres = [genre.get("name") for genre in data.get("genres", [])]

        # Process based on media type
        if media_type == MediaMetadataType.MOVIE:
            title = data.get("title", "")
            release_date = data.get("release_date")
            year = None

            if release_date:
                try:
                    year = datetime.strptime(release_date, "%Y-%m-%d").year
                except ValueError:
                    pass

            return MediaMetadata(
                title=title,
                media_type=media_type,
                original_title=data.get("original_title"),
                overview=data.get("overview"),
                provider=self.provider_name,
                provider_id=provider_id,
                external_ids=external_ids,
                release_date=release_date,
                year=year,
                vote_average=data.get("vote_average"),
                vote_count=data.get("vote_count"),
                popularity=data.get("popularity"),
                artwork=artwork,
                runtime=data.get("runtime"),
                genres=genres,
            )

        elif media_type == MediaMetadataType.TV_SHOW:
            title = data.get("name", "")
            first_air_date = data.get("first_air_date")
            year = None

            if first_air_date:
                try:
                    year = datetime.strptime(first_air_date, "%Y-%m-%d").year
                except ValueError:
                    pass

            # Extract seasons and episode counts
            seasons = [
                season.get("season_number", 0) for season in data.get("seasons", [])
            ]
            seasons = [s for s in seasons if s > 0]  # Filter out specials (season 0)

            return MediaMetadata(
                title=title,
                media_type=media_type,
                original_title=data.get("original_name"),
                overview=data.get("overview"),
                provider=self.provider_name,
                provider_id=provider_id,
                external_ids=external_ids,
                release_date=first_air_date,
                year=year,
                vote_average=data.get("vote_average"),
                vote_count=data.get("vote_count"),
                popularity=data.get("popularity"),
                artwork=artwork,
                genres=genres,
                number_of_seasons=data.get("number_of_seasons"),
                number_of_episodes=data.get("number_of_episodes"),
                seasons=seasons,
                episode_run_time=data.get("episode_run_time", [0])[0],
            )

        elif media_type == MediaMetadataType.TV_EPISODE:
            show_data = data.get("show", {})
            show_title = show_data.get("name", "Unknown Show")
            episode_title = data.get("name", "")

            air_date = data.get("air_date")

            # Create episode metadata
            episode = TVEpisode(
                title=episode_title,
                episode_number=data.get("episode_number", 0),
                season_number=data.get("season_number", 0),
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
                vote_average=data.get("vote_average"),
                vote_count=data.get("vote_count"),
                artwork=artwork,
                episodes=[episode],
                season_number=data.get("season_number"),
                episode_number=data.get("episode_number"),
            )

        # Default fallback
        return MediaMetadata(
            title=data.get("title", data.get("name", "Unknown")),
            media_type=media_type,
            provider=self.provider_name,
            provider_id=provider_id,
            external_ids=external_ids,
            artwork=artwork,
        )
