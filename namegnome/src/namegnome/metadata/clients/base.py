"""Base classes for metadata API clients."""

from abc import ABC, abstractmethod
from typing import Any


class MetadataClient(ABC):
    """Abstract base class for all metadata provider clients.

    This defines the contract that all media metadata clients must implement,
    regardless of the underlying API they communicate with.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of this metadata provider.

        Returns:
            The provider's name (e.g., 'tmdb', 'tvdb').
        """
        pass

    @abstractmethod
    async def search_movie(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search for movies by title and optional year.

        Args:
            title: The movie title to search for.
            year: Optional release year to filter results.

        Returns:
            A list of movie metadata dictionaries.
        """
        pass

    @abstractmethod
    async def search_tv(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search for TV shows by title and optional year.

        Args:
            title: The TV show title to search for.
            year: Optional first air date year to filter results.

        Returns:
            A list of TV show metadata dictionaries.
        """
        pass

    @abstractmethod
    async def get_movie_details(self, movie_id: str) -> dict[str, Any]:
        """Get detailed information about a specific movie.

        Args:
            movie_id: The ID of the movie in this provider's system.

        Returns:
            A dictionary containing detailed movie metadata.
        """
        pass

    @abstractmethod
    async def get_tv_details(self, show_id: str) -> dict[str, Any]:
        """Get detailed information about a specific TV show.

        Args:
            show_id: The ID of the TV show in this provider's system.

        Returns:
            A dictionary containing detailed TV show metadata.
        """
        pass

    @abstractmethod
    async def get_tv_season(self, show_id: str, season_number: int) -> dict[str, Any]:
        """Get detailed information about a specific TV season.

        Args:
            show_id: The ID of the TV show in this provider's system.
            season_number: The season number to retrieve.

        Returns:
            A dictionary containing season metadata, including episodes.
        """
        pass

    @abstractmethod
    async def get_tv_episode(
        self, show_id: str, season_number: int, episode_number: int
    ) -> dict[str, Any]:
        """Get detailed information about a specific TV episode.

        Args:
            show_id: The ID of the TV show in this provider's system.
            season_number: The season number of the episode.
            episode_number: The episode number within the season.

        Returns:
            A dictionary containing episode metadata.
        """
        pass
