"""Plex-specific naming rules for media files."""

import re
from pathlib import Path

from namegnome.models.core import MediaFile, MediaType
from namegnome.rules.base import RuleSet


class PlexRuleSet(RuleSet):
    """Rule set for Plex Media Server naming conventions.

    Follows the naming guide at:
    https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/

    TV Show format:
        /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext
    Movie format:
        /Movies/Movie Name (Year)/Movie Name (Year).ext
    """

    def __init__(self) -> None:
        """Initialize the Plex rule set."""
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

        # Patterns for extracting metadata from filenames
        self.tv_pattern = re.compile(
            r"^(.*?)[\s\._-]*S(\d{1,2})[\s\._-]*E(\d{1,2})[\s\._-]*(.*?)(?:\.[^.]+)?$",
            re.IGNORECASE,
        )
        self.movie_pattern = re.compile(
            r"^(.*?)[\s\._-]*(?:\((\d{4})\))?(?:\.[^.]+)?$", re.IGNORECASE
        )

        # Pattern for year at the end of a filename (e.g., The.Matrix.1999.mp4)
        self.year_pattern = re.compile(
            r"^(.*?)[\s\._-]*(\d{4})(?:\.[^.]+)?$", re.IGNORECASE
        )

    def supports_media_type(self, media_type: MediaType) -> bool:
        """Check if this rule set supports the given media type.

        Args:
            media_type: The media type to check support for.

        Returns:
            True if the media type is supported, False otherwise.
        """
        return media_type in self.supported_media_types

    @property
    def supported_media_types(self) -> list[MediaType]:
        """Get a list of media types supported by this rule set.

        Returns:
            A list of supported MediaType values.
        """
        return [MediaType.TV, MediaType.MOVIE]

    def target_path(self, media_file: MediaFile, base_dir: Path | None = None) -> Path:
        """Generate a target path for a media file using Plex naming conventions.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path. If None,
                      the target path will use the same parent as the source.

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

        # Get the file extension
        ext = media_file.path.suffix.lower()

        if media_file.media_type == MediaType.TV:
            return self._tv_show_path(media_file, root_dir, ext)
        elif media_file.media_type == MediaType.MOVIE:
            return self._movie_path(media_file, root_dir, ext)
        else:
            # This should never happen due to the earlier check
            raise ValueError(f"Unsupported media type: {media_file.media_type}")

    def _tv_show_path(self, media_file: MediaFile, root_dir: Path, ext: str) -> Path:
        """Generate a target path for a TV show file.

        Format: /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext

        Args:
            media_file: The media file to generate a target path for.
            root_dir: The base directory to build the path from.
            ext: The file extension.

        Returns:
            A Path object for the target file.

        Raises:
            ValueError: If the filename doesn't match expected patterns.
        """
        filename = media_file.path.name
        match = self.tv_pattern.match(filename)

        if not match:
            # If no match, try to extract what we can from the file path
            # For now, just use the filename as is
            show_name = "Unknown Show"
            season_num = 1
            episode_num = 1
            episode_title = "Unknown Episode"
        else:
            show_name = match.group(1).strip().replace(".", " ")
            season_num = int(match.group(2))
            episode_num = int(match.group(3))
            # If group 4 is empty or just the extension, use "Unknown Episode"
            episode_title_raw = match.group(4).strip() if match.group(4) else ""
            if (
                not episode_title_raw
                or episode_title_raw.lower() == ext.lstrip(".").lower()
            ):
                episode_title = "Unknown Episode"
            else:
                episode_title = episode_title_raw.replace(".", " ")

        # Create the target path components
        tv_dir = root_dir / "TV Shows"
        show_dir = tv_dir / show_name
        season_dir = show_dir / f"Season {season_num:02d}"

        # Create the filename in Plex format
        target_filename = (
            f"{show_name} - S{season_num:02d}E{episode_num:02d} - {episode_title}{ext}"
        )

        return season_dir / target_filename

    def _movie_path(self, media_file: MediaFile, root_dir: Path, ext: str) -> Path:
        """Generate a target path for a movie file.

        Format: /Movies/Movie Title (Year)/Movie Title (Year).ext

        Args:
            media_file: The media file to generate a target path for.
            root_dir: The base directory to build the path from.
            ext: The file extension.

        Returns:
            A Path object for the target file.

        Raises:
            ValueError: If the filename doesn't match expected patterns.
        """
        filename = media_file.path.name
        # First try the standard pattern with (Year)
        match = self.movie_pattern.match(filename)

        if match and match.group(2):
            # We have a standard "Movie Name (Year)" format
            movie_title = match.group(1).strip().replace(".", " ")
            year = match.group(2)
        else:
            # Try the alternate "Movie.Name.Year.ext" format
            alt_match = self.year_pattern.match(filename)
            if alt_match:
                movie_title = alt_match.group(1).strip().replace(".", " ")
                year = alt_match.group(2)
            else:
                # If no match, try to extract what we can
                movie_title = filename.rsplit(".", 1)[0].replace(".", " ").strip()
                year = None

        # Create the target path components
        movies_dir = root_dir / "Movies"

        # Add year if available
        if year:
            movie_dir_name = f"{movie_title} ({year})"
            target_filename = f"{movie_title} ({year}){ext}"
        else:
            movie_dir_name = movie_title
            target_filename = f"{movie_title}{ext}"

        movie_dir = movies_dir / movie_dir_name

        return movie_dir / target_filename
