"""Base abstract classes for media file naming rule sets."""

from abc import ABC, abstractmethod
from pathlib import Path

from namegnome.models.core import MediaFile, MediaType


class RuleSet(ABC):
    """Abstract base class for media naming rule sets.

    Rule sets define how media files should be renamed and organized
    based on their metadata and the target platform's naming conventions.
    """

    def __init__(self, platform_name: str) -> None:
        """Initialize a rule set.

        Args:
            platform_name: The name of the platform this rule set is for (e.g., "plex", "jellyfin").
        """
        self.platform_name = platform_name

    @abstractmethod
    def target_path(
        self,
        media_file: MediaFile,
        base_dir: Path | None = None,
        show_name: str | None = None,
        movie_year: int | None = None,
        anthology: bool = False,
        adjust_episodes: bool = False,
        verify: bool = False,
        llm_model: str | None = None,
        strict_directory_structure: bool = True,
    ) -> Path:
        """Generate a target path for the given media file.

        This method determines where a file should be moved/renamed to based on
        the platform's naming rules and the file's metadata.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path. If None,
                      the target path will be absolute.
            show_name: Optional show name override.
            movie_year: Optional movie year override.
            anthology: Whether to treat as an anthology series.
            adjust_episodes: Whether to adjust episode numbers.
            verify: Whether to verify metadata.
            llm_model: Optional LLM model to use for metadata extraction.
            strict_directory_structure: Whether to enforce strict directory structure.

        Returns:
            A Path object representing the target location for this file.

        Raises:
            ValueError: If the media_file type is not supported by this rule set.
        """
        pass

    @abstractmethod
    def supports_media_type(self, media_type: MediaType) -> bool:
        """Check if this rule set supports the given media type.

        Args:
            media_type: The media type to check support for.

        Returns:
            True if the media type is supported, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def supported_media_types(self) -> list[MediaType]:
        """Get a list of media types supported by this rule set.

        Returns:
            A list of supported MediaType values.
        """
        pass
