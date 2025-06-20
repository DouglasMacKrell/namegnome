"""Base abstract classes for media file naming rule sets.

This module defines the abstract base class and configuration dataclass for all
platform-specific naming rule sets.
- RuleSetConfig: Groups all configuration options that may affect naming (show name,
  year, anthology, etc.).
- RuleSet: Abstract base class for all rule sets, enforcing a consistent interface
  for target path generation and media type support.

Design:
- All platform-specific rulesets (e.g., Plex, Jellyfin) must inherit from RuleSet and
  implement its abstract methods.
- This abstraction allows new platforms to be added without changing the core planner
  or CLI logic.
- Naming conventions and configuration options are derived from MEDIA-SERVER
  FILE-NAMING & METADATA GUIDE.md and PLANNING.md.

Extensibility:
- To add a new platform, subclass RuleSet and implement target_path,
  supports_media_type, and supported_media_types.
- RuleSetConfig can be extended with new options as needed for future platforms or
  features.

See README.md and PLANNING.md for rationale and usage examples.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Self

from namegnome.models.core import MediaFile, MediaType

if TYPE_CHECKING:
    from namegnome.metadata.models import MediaMetadata


# Reason: RuleSetConfig groups all options that may affect naming, making it easy
# to pass config between CLI, planner, and rules.
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
    untrusted_titles: bool = (
        False  # If true, ignore input titles and use only canonical data
    )
    max_duration: int | None = (
        None  # Max allowed duration (minutes) for pairing episodes in anthology mode
    )


# Reason: RuleSet is an abstract base class (ABC) to enforce a consistent
# interface for all platform-specific naming logic.
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
        metadata: "MediaMetadata | None" = None,
        episode_span: str | None = None,
        joined_titles: str | None = None,
        **kwargs: object,
    ) -> Path:
        """Generate a target path for the given media file.

        This method determines where a file should be moved/renamed to based on
        the platform's naming rules, the file's metadata, and optional provider
        metadata.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path.
            config: Optional configuration for the rule set.
            metadata: Optional provider metadata (e.g., from TMDB/TVDB) to
                influence naming.
            episode_span: Optional episode span for the media file.
            joined_titles: Optional joined titles for the media file.
            **kwargs: Additional keyword arguments.

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


# TODO: NGN-205 - Consider adding a method for custom validation or post-processing
# hooks for advanced platforms.
