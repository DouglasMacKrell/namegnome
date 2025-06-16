# mypy: disable-error-code=unreachable
"""Plex-specific naming rules for media files.

This module implements the RuleSet for Plex Media Server, following the official
naming guide and conventions:
https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/

Design:
- TV and Movie formats are derived from MEDIA-SERVER FILE-NAMING & METADATA
  GUIDE.md and Plex documentation.
- Regex patterns are used to extract show/movie names, season/episode numbers,
  and years from filenames.
- Handles edge cases where filenames are incomplete or do not match expected
  patterns, falling back to config or defaults.
- Directory structure is enforced to match Plex's expectations for library
  scanning and metadata matching.

Extensibility:
- To support new edge cases or additional metadata, extend the regex patterns or
  add new config options.
- This class can be subclassed for Plex variants or customizations.

See README.md and PLANNING.md for rationale and usage examples.
"""

import re
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional, Self

from namegnome.metadata.utils import sanitize_title
from namegnome.models.core import MediaFile, MediaType
from namegnome.rules.base import RuleSet, RuleSetConfig

if TYPE_CHECKING:
    from namegnome.metadata.models import MediaMetadata


class PlexRuleSet(RuleSet):
    """Rule set for Plex Media Server naming conventions.

    Follows the naming guide at:
    https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/

    TV Show format:
        /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext
    Movie format:
        /Movies/Movie Name (Year)/Movie Name (Year).ext
    """

    # Reason: Regex patterns are designed to match the most common Plex naming
    # conventions, as well as common user mistakes.
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

        # Reason: Only include extensions supported by Plex for video files.
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
        metadata: "MediaMetadata | None" = None,
    ) -> Path:
        """Generate a target path for a media file using Plex naming conventions.

        Args:
            media_file: The media file to generate a target path for.
            base_dir: Optional base directory for the target path. If None,
                the target path will use the same parent as the source.
            config: Optional configuration for the rule set.
            metadata: Optional provider metadata (e.g., from TMDB/TVDB) to
                influence naming.

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
                metadata=metadata,
            )
        elif media_file.media_type == MediaType.MOVIE:
            return self._movie_path(
                media_file,
                root_dir,
                ext,
                config=config,
                metadata=metadata,
            )
        else:
            # This should never happen due to the earlier check
            raise ValueError(f"Unsupported media type: {media_file.media_type}")

    def _tv_show_path(  # type: ignore  # noqa: C901, PLR0912, PLR0915
        self: Self,
        media_file: MediaFile,
        root_dir: Path,
        ext: str,
        config: Optional[RuleSetConfig] = None,
        metadata: "MediaMetadata | None" = None,
    ) -> Path:
        """Generate a target path for a TV show file.

        Format: /TV Shows/Show Name/Season XX/Show Name - SXXEXX - Episode Title.ext
        Anthology: /TV Shows/Show Name/Season XX/Show Name - SXXEXX-EYY - Title1 &
        Title2.ext
        """
        if config is None:
            config = RuleSetConfig()
        filename = media_file.path.name
        # Prefer explicit metadata from MediaFile (for anthology/LLM splits)
        if media_file.title and (
            media_file.episode is not None or media_file.episode == 0
        ):
            show_name = media_file.title.replace(".", " ").title()
            season_val = media_file.season if media_file.season is not None else 1
            episode_val = media_file.episode if media_file.episode is not None else 1
            # Convert to int if numeric, else keep as str
            if isinstance(season_val, int):
                season_num: int | str = season_val
            elif isinstance(season_val, str) and season_val.isdigit():
                season_num = int(season_val)
            else:
                season_num = str(season_val)
            episode_title = (media_file.episode_title or "Unknown Episode").replace(
                ".", " "
            )
            # Use metadata for episode title if available
            if metadata and metadata.episodes:
                for ep in metadata.episodes:
                    if (
                        ep.season_number == season_num
                        and ep.episode_number == episode_val
                        and ep.title
                        and ep.title.strip()
                    ):
                        episode_title = ep.title.strip().replace(".", " ")
                        break
                if not episode_title:
                    episode_title = "Unknown Episode"
            elif not episode_title:
                episode_title = "Unknown Episode"

            # Always sanitize the episode title for output (after metadata override)
            sanitized_episode_title = (
                sanitize_title(episode_title).title()
                if episode_title
                else "Unknown Episode"
            )
            # PATCH: Use episode span directly if it's a string
            if isinstance(media_file.episode, str):
                filename = (
                    f"{show_name} - S{season_num:02d}E{media_file.episode} - "
                    f"{sanitized_episode_title}{ext}"
                )
            else:
                filename = (
                    f"{show_name} - S{season_num:02d}E{episode_val:02d} - "
                    f"{sanitized_episode_title}{ext}"
                )
            return (
                root_dir
                / "TV Shows"
                / show_name
                / f"Season {int(season_num):02d}"
                / filename
            ).resolve()
        else:
            match = self.tv_pattern.match(filename)
            if not match:
                show_name = (
                    config.show_name
                    or (metadata.title if metadata else None)
                    or "Unknown Show"
                )
                show_name = show_name.title()
                season_num: int | str = 1
                episode_num: int | str = 1
                episode_title = "Unknown Episode"
            else:
                show_name = (
                    config.show_name
                    or (metadata.title if metadata else None)
                    or match.group(1).strip().replace(".", " ")
                )
                show_name = show_name.title()
                season_str = match.group(2)
                episode_str = match.group(3)
                if season_str.isdigit():
                    season_num = int(season_str)
                else:
                    season_num = season_str
                if episode_str.isdigit():
                    episode_num = int(episode_str)
                else:
                    episode_num = episode_str
                episode_title_raw = match.group(4).strip() if match.group(4) else ""
                if episode_title_raw.endswith(ext):
                    episode_title_raw = episode_title_raw[: -len(ext)]
                if (
                    not episode_title_raw
                    or episode_title_raw.lower() == ext.lstrip(".").lower()
                ):
                    episode_title = None
                else:
                    episode_title = episode_title_raw.replace(".", " ").strip()
        # Use metadata for episode title if available
        if "season_num" not in locals():
            season_num = 1
        if "episode_num" not in locals():
            episode_num = 1
        if metadata and metadata.episodes:
            for ep in metadata.episodes:
                if (
                    ep.season_number == season_num
                    and ep.episode_number == episode_num
                    and ep.title
                    and ep.title.strip()
                ):
                    episode_title = ep.title.strip().replace(".", " ")
                    break
            if not episode_title:
                episode_title = "Unknown Episode"
        elif not episode_title:
            episode_title = "Unknown Episode"
        # Always sanitize the episode title for output
        sanitized_episode_title = (
            sanitize_title(episode_title).title()
            if episode_title
            else "Unknown Episode"
        )
        filename = (
            f"{show_name} - S{int(season_num):02d}E{str(episode_num).zfill(2)} - "
            f"{sanitized_episode_title}{ext}"
        )
        return (
            root_dir
            / "TV Shows"
            / show_name
            / f"Season {int(season_num):02d}"
            / filename
        ).resolve()

    def _movie_path(
        self: Self,
        media_file: MediaFile,
        root_dir: Path,
        ext: str,
        config: Optional[RuleSetConfig] = None,
        metadata: "MediaMetadata | None" = None,
    ) -> Path:
        """Generate a target path for a movie file.

        Format: /Movies/Movie Name (Year)/Movie Name (Year).ext

        Args:
            media_file: The media file to generate a target path for.
            root_dir: The base directory to build the path from.
            ext: The file extension.
            config: Optional configuration for the rule set.
            metadata: Optional provider metadata (e.g., from TMDB) to
                influence naming.

        Returns:
            A Path object for the target file.
        """
        if config is None:
            config = RuleSetConfig()

        filename = media_file.path.name
        match = self.movie_pattern.match(filename)
        if match:
            movie_name = match.group(1).strip().replace(".", " ")
            year = int(match.group(2)) if match.group(2) else None
        else:
            # Try year pattern (e.g., The.Matrix.1999.mp4)
            match_year = self.year_pattern.match(filename)
            if match_year:
                movie_name = match_year.group(1).strip().replace(".", " ")
                year = int(match_year.group(2)) if match_year.group(2) else None
            else:
                movie_name = (
                    metadata.title
                    if metadata and metadata.title
                    else (filename.rsplit(".", 1)[0].replace(".", " "))
                )
                year = None

        # Prefer metadata year if available
        if metadata and metadata.year:
            year = metadata.year

        if year:
            movie_dir = root_dir / "Movies" / f"{movie_name} ({year})"
            filename = f"{movie_name} ({year}){ext}"
        else:
            movie_dir = root_dir / "Movies" / movie_name
            filename = f"{movie_name}{ext}"
        return movie_dir / filename
