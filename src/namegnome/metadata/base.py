"""Base abstraction for metadata provider clients.

Defines the interface for all metadata providers (TMDB, TVDB, MusicBrainz, etc.)
used by NameGnome. All provider clients must inherit from this class and implement
its methods. See PLANNING.md and TASK.md for requirements.
"""

from abc import ABC, abstractmethod

from namegnome.metadata.models import MediaMetadata


class MetadataClient(ABC):
    """Abstract base class for all metadata provider clients.

    All provider clients (TMDB, TVDB, MusicBrainz, etc.) must inherit from this
    class and implement its methods. Used for dependency injection and testability.
    """

    @abstractmethod
    async def search(self, title: str, year: int | None = None) -> list[MediaMetadata]:
        """Search for media items by title and optional year.

        Args:
            title: The title to search for.
            year: Optional release year to narrow results.

        Returns:
            A list of MediaMetadata objects matching the query.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    @abstractmethod
    async def details(self, provider_id: str) -> MediaMetadata:
        """Fetch full metadata details for a given provider-specific ID.

        Args:
            provider_id: The unique ID in the provider's system.

        Returns:
            A MediaMetadata object with full details.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError
