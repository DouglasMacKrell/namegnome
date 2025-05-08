"""Plex-specific naming rules for media files."""

import re
from pathlib import Path
from typing import ClassVar, Optional, Self

from namegnome.models.core import MediaFile, MediaType
from namegnome.rules.base import RuleSet, RuleSetConfig


class PlexRuleSet(RuleSet):
    """Rule set for Plex Media Server naming conventions.

    Follows the naming guide at:
    https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/

    TV Show format:
        /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext
    Movie format:
        /Movies/Movie Name (Year)/Movie Name (Year).ext
    """

    # Patterns for TV shows and movies
    tv_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(.*?)[\.|\s]S(\d{2})E(\d{2})(?:[\.|\s](.+))?$", re.IGNORECASE
    )
    movie_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(.*?)\s*\((\d{4})\)(?:\.(.+))?$", re.IGNORECASE
    )
    year_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"(.*?)\.(\d{4})(?:\.(.+))?$", re.IGNORECASE
    )

    def __init__(self: Self) -> None:
        """Initialize the PlexRuleSet."""
        super().__init__("plex")

        # Common media extensions
        self.video_extensions = {
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".wmv",
            ".m4v",
            ".mpg",
            ".mpeg",
            ".flv",
            ".webm",
        }

    def supports_media_type(self: Self, media_type: MediaType) -> bool:
        """Check if this rule set supports the given media type.

        Args:
            media_type: The media type to check support for.

        Returns:
            True if the media type is supported, False otherwise.
        """
        return media_type in self.supported_media_types

    @property
    def supported_media_types(self: Self) -> list[MediaType]:
        """Get a list of media types supported by this rule set.

        Returns:
            A list of supported MediaType values.
        """
        return [MediaType.TV, MediaType.MOVIE]

    def target_path(
        self: Self,
        media_file: MediaFile,
        base_dir: Optional[Path] = None,
        config: Optional[RuleSetConfig] = None,
    ) -> Path:
        """Generate a target path for a media file using Plex naming conventions.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path. If None,
                      the target path will use the same parent as the source.
            config: Optional configuration for the rule set.

        Returns:
            A Path object representing the target location for this file.

        Raises:
            ValueError: If the media_file type is not supported or cannot be processed.
        """
        if not self.supports_media_type(media_file.media_type):
            raise ValueError(
                f"Media type {media_file.media_type} is not supported by Plex rule set"
            )

        # Use base_dir or the parent of the original file
        root_dir = base_dir if base_dir else media_file.path.parent

        # Use default config if none provided
        if config is None:
            config = RuleSetConfig()

        # Get the file extension
        ext = media_file.path.suffix.lower()

        if media_file.media_type == MediaType.TV:
            return self._tv_show_path(
                media_file,
                root_dir,
                ext,
                config=config,
            )
        elif media_file.media_type == MediaType.MOVIE:
            return self._movie_path(
                media_file,
                root_dir,
                ext,
                config=config,
            )
        else:
            # This should never happen due to the earlier check
            raise ValueError(f"Unsupported media type: {media_file.media_type}")

    def _tv_show_path(
        self: Self,
        media_file: MediaFile,
        root_dir: Path,
        ext: str,
        config: Optional[RuleSetConfig] = None,
    ) -> Path:
        """Generate a target path for a TV show file.

        Format: /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext

        Args:
            media_file: The media file to generate a target path for.
            root_dir: The base directory to build the path from.
            ext: The file extension.
            config: Optional configuration for the rule set.

        Returns:
            A Path object for the target file.

        Raises:
            ValueError: If the filename doesn't match expected patterns.
        """
        if config is None:
            config = RuleSetConfig()

        filename = media_file.path.name
        match = self.tv_pattern.match(filename)

        if not match:
            # If no match, try to extract what we can from the file path
            # For now, just use the filename as is
            show_name = config.show_name or "Unknown Show"
            season_num = 1
            episode_num = 1
            episode_title = "Unknown Episode"
        else:
            show_name = config.show_name or match.group(1).strip().replace(".", " ")
            season_num = int(match.group(2))
            episode_num = int(match.group(3))
            # If group 4 is empty or just the extension, use "Unknown Episode"
            episode_title_raw = match.group(4).strip() if match.group(4) else ""

            # Remove the file extension from the episode title if it ends with it
            if episode_title_raw.endswith(ext):
                episode_title_raw = episode_title_raw[: -len(ext)]

            if (
                not episode_title_raw
                or episode_title_raw.lower() == ext.lstrip(".").lower()
            ):
                episode_title = "Unknown Episode"
            else:
                episode_title = episode_title_raw.replace(".", " ").strip()

        # Create the target path components
        tv_dir = root_dir / "TV Shows"
        show_dir = tv_dir / show_name
        season_dir = show_dir / f"Season {season_num:02d}"

        # Create the filename in Plex format
        target_filename = (
            f"{show_name} - S{season_num:02d}E{episode_num:02d} - {episode_title}{ext}"
        )

        return season_dir / target_filename

    def _movie_path(
        self: Self,
        media_file: MediaFile,
        root_dir: Path,
        ext: str,
        config: Optional[RuleSetConfig] = None,
    ) -> Path:
        """Generate a target path for a movie file.

        Format: /Movies/Movie Name (Year)/Movie Name (Year).ext

        Args:
            media_file: The media file to generate a target path for.
            root_dir: The base directory to build the path from.
            ext: The file extension.
            config: Optional configuration for the rule set.

        Returns:
            A Path object for the target file.

        Raises:
            ValueError: If the filename doesn't match expected patterns.
        """
        if config is None:
            config = RuleSetConfig()

        filename = media_file.path.name
        # First try the standard pattern with (Year)
        match = self.movie_pattern.match(filename)

        if match and match.group(2):
            # We have a standard "Movie Name (Year)" format
            movie_title = match.group(1).strip().replace(".", " ")
            year = config.movie_year or match.group(2)
        else:
            # Try the alternate "Movie.Name.Year.ext" format
            alt_match = self.year_pattern.match(filename)
            if alt_match:
                movie_title = alt_match.group(1).strip().replace(".", " ")
                year = config.movie_year or alt_match.group(2)
            else:
                # If no match, try to extract what we can
                movie_title = filename.rsplit(".", 1)[0].replace(".", " ").strip()
                year = config.movie_year

        # Create the target path components
        movies_dir = root_dir / "Movies"

        # Add year if available
        if year:
            movie_dir_name = f"{movie_title} ({year})"
            target_filename = f"{movie_title} ({year}){ext}"
        else:
            movie_dir_name = movie_title
            target_filename = f"{movie_title}{ext}"

        # Create collection directory if using strict directory structure
        if config.strict_directory_structure:
            movie_dir = movies_dir / movie_dir_name
            return movie_dir / target_filename
        else:
            return movies_dir / target_filename
