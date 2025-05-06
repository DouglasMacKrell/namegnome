"""Scanner for media files.

This module provides functionality to scan directories for media files
and filter them based on media type, show name, and movie year.
"""

import logging
from pathlib import Path

from namegnome.models.core import MediaFile, MediaType
from namegnome.models.scanner import ScanResult

# Logger for this module
logger = logging.getLogger(__name__)


def guess_media_type(file_path: Path) -> MediaType | None:
    """Guess the media type of a file based on its path.

    Args:
        file_path: Path to the file

    Returns:
        MediaType if detected, None otherwise
    """
    path_str = str(file_path)
    if "TV Shows" in path_str:
        return MediaType.TV
    elif "Movies" in path_str:
        return MediaType.MOVIE
    elif "Music" in path_str:
        return MediaType.MUSIC
    return None


def scan_directory(
    root_dir: Path,
    media_types: set[MediaType],
    show_name: str | None = None,
    movie_year: int | None = None,
    recursive: bool = True,
) -> ScanResult:
    """Scan a directory for media files of specified types.

    Args:
        root_dir: Root directory to scan
        media_types: Set of media types to scan for
        show_name: Optional show name to filter TV files by
        movie_year: Optional year to filter movie files by
        recursive: Whether to scan subdirectories recursively

    Returns:
        ScanResult containing found media files

    Raises:
        FileNotFoundError: If directory does not exist
        NotADirectoryError: If path is not a directory
    """
    if not root_dir.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")
    if not root_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_dir}")

    # Initialize counters
    total_files = 0
    skipped_files = 0
    by_media_type = {media_type: 0 for media_type in media_types}
    media_files = []
    errors = []

    # Scan directory
    pattern = "**/*.mp4" if recursive else "*.mp4"
    for file_path in root_dir.glob(pattern):
        try:
            # Determine media type based on path
            media_type = guess_media_type(file_path)

            # Skip if not a requested media type
            if not media_type or media_type not in media_types:
                skipped_files += 1
                continue

            # Create media file
            media_file = MediaFile(
                path=file_path.absolute(),
                size=file_path.stat().st_size,
                media_type=media_type,
                modified_date=file_path.stat().st_mtime,
            )

            # Filter by show name or movie year if specified
            if show_name and media_type == MediaType.TV:
                if show_name not in str(file_path):
                    skipped_files += 1
                    continue
            if movie_year and media_type == MediaType.MOVIE:
                if str(movie_year) not in str(file_path):
                    skipped_files += 1
                    continue

            # Add to results
            media_files.append(media_file)
            by_media_type[media_type] += 1
            total_files += 1

        except Exception as e:
            errors.append(f"Error processing {file_path}: {e}")
            skipped_files += 1

    return ScanResult(
        total_files=total_files,
        skipped_files=skipped_files,
        by_media_type=by_media_type,
        media_files=media_files,
        errors=errors,
        root_dir=root_dir,
    )
