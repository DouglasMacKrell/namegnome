"""Base abstract classes for media file naming rule sets."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Self

from namegnome.models.core import MediaFile, MediaType


@dataclass
class RuleSetConfig:
    """Configuration for rule sets."""

    show_name: Optional[str] = None
    movie_year: Optional[int] = None
    anthology: bool = False
    adjust_episodes: bool = False
    verify: bool = False
    llm_model: Optional[str] = None
    strict_directory_structure: bool = True


class RuleSet(ABC):
    """Abstract base class for media naming rule sets.

    Rule sets define how media files should be renamed and organized
    based on their metadata and the target platform's naming conventions.
    """

    def __init__(self: Self, platform_name: str) -> None:
        """Initialize a rule set.

        Args:
            platform_name: The name of the platform this rule set is for.
        """
        self.platform_name = platform_name

    @abstractmethod
    def target_path(
        self: Self,
        media_file: MediaFile,
        base_dir: Optional[Path] = None,
        config: Optional[RuleSetConfig] = None,
    ) -> Path:
        """Generate a target path for the given media file.

        This method determines where a file should be moved/renamed to based on
        the platform's naming rules and the file's metadata.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path.
            config: Optional configuration for the rule set.

        Returns:
            A Path object representing the target location for this file.

        Raises:
            ValueError: If the media_file type is not supported.
        """
        pass

    @abstractmethod
    def supports_media_type(self: Self, media_type: MediaType) -> bool:
        """Check if this rule set supports the given media type.

        Args:
            media_type: The media type to check support for.

        Returns:
            True if the media type is supported, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def supported_media_types(self: Self) -> list[MediaType]:
        """Get a list of media types supported by this rule set.

        Returns:
            A list of supported MediaType values.
        """
        pass
