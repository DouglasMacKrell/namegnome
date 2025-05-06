"""Directory scanner for media files.

This module provides functionality to scan directories for media files
and classify them based on file extensions and patterns.
"""

import logging
import re
import time
from datetime import datetime
from pathlib import Path

from namegnome.models.core import MediaFile, MediaType, ScanResult

# Logger for this module
logger = logging.getLogger(__name__)

# Common media file extensions by type
MEDIA_EXTENSIONS = {
    MediaType.TV: {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".webm"},
    MediaType.MOVIE: {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".webm"},
    MediaType.MUSIC: {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".alac"},
}

# Extensions that should be ignored completely
IGNORED_EXTENSIONS = {
    ".nfo",
    ".txt",
    ".srt",
    ".sub",
    ".idx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".db",
    ".ini",
    ".log",
    ".DS_Store",
    ".part",
    ".!qb",
    ".aria2",
    ".xml",
    ".tmp",
    ".bak",
    ".url",
}

# Patterns that strongly indicate TV shows
TV_PATTERNS = [
    r"s\d{1,2}e\d{1,2}",  # S01E01
    r"\d{1,2}x\d{1,2}",  # 1x01
    r"season\s\d+",  # Season 1
    r"episode\s\d+",  # Episode 1
]

# Directory names that suggest specific media types
DIRECTORY_HINTS = {
    MediaType.TV: {"tv", "shows", "series", "tv shows", "television"},
    MediaType.MOVIE: {"movies", "film", "films", "cinema"},
    MediaType.MUSIC: {"music", "audio", "songs", "albums", "mp3"},
}


def guess_media_type(path: Path) -> MediaType:
    """Guess the media type of a file based on its path and extension.

    Args:
        path: The file path to analyze.

    Returns:
        The best guess for MediaType.
    """
    # Start with extension-based classification
    ext = path.suffix.lower()

    # If it's not a known media extension, return UNKNOWN
    if not any(ext in extensions for extensions in MEDIA_EXTENSIONS.values()):
        return MediaType.UNKNOWN

    # Check for TV show patterns in the filename
    path_str = str(path).lower()

    # Compile TV show patterns with case insensitivity
    tv_patterns_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in TV_PATTERNS]

    # Check if any pattern matches
    if any(pattern.search(path_str) for pattern in tv_patterns_compiled):
        return MediaType.TV

    # Look at parent directory names for hints
    for parent in path.parents:
        parent_name = parent.name.lower()
        for media_type, hints in DIRECTORY_HINTS.items():
            if parent_name in hints:
                return media_type

    # Default to UNKNOWN if we can't determine the type
    return MediaType.UNKNOWN


def scan_directory(
    root_dir: Path,
    media_types: list[MediaType] | None = None,
    recursive: bool = True,
    include_hidden: bool = False,
) -> ScanResult:
    """Scan a directory for media files.

    Args:
        root_dir: The directory to scan.
        media_types: Optional list of media types to include (defaults to all).
        recursive: Whether to scan subdirectories.
        include_hidden: Whether to include hidden files and directories.

    Returns:
        A ScanResult object containing the scan results.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        PermissionError: If there are permission issues accessing files.
    """
    if not root_dir.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")

    if not root_dir.is_dir():
        raise ValueError(f"Path is not a directory: {root_dir}")

    # Use all media types if none specified
    if media_types is None:
        media_types = [MediaType.TV, MediaType.MOVIE, MediaType.MUSIC]

    # Set of extensions to look for based on requested media types
    target_extensions: set[str] = set()
    for media_type in media_types:
        if media_type in MEDIA_EXTENSIONS:
            target_extensions.update(MEDIA_EXTENSIONS[media_type])

    start_time = time.time()
    total_files = 0
    skipped_files = 0
    errors: list[str] = []
    media_files: list[MediaFile] = []
    by_media_type: dict[MediaType, int] = {media_type: 0 for media_type in media_types}

    # Start the scan
    logger.info(f"Starting scan of {root_dir} for media types: {media_types}")

    # Pattern for hidden files and directories
    def is_hidden(path: Path) -> bool:
        return any(part.startswith(".") for part in path.parts)

    # Define the glob pattern based on recursive flag
    glob_func = root_dir.rglob if recursive else root_dir.glob

    try:
        for path in glob_func("*"):
            # Skip directories
            if path.is_dir():
                continue

            # Skip hidden files/directories if not included
            if not include_hidden and is_hidden(path):
                skipped_files += 1
                continue

            # Count all files for statistics
            total_files += 1

            # Skip based on extension
            ext = path.suffix.lower()
            if ext in IGNORED_EXTENSIONS:
                skipped_files += 1
                continue

            if ext not in target_extensions:
                skipped_files += 1
                continue

            try:
                # Get file stats
                stats = path.stat()
                size = stats.st_size
                modified_date = datetime.fromtimestamp(stats.st_mtime)

                # Guess the media type
                media_type = guess_media_type(path)

                # Only include media types we're looking for
                if media_type not in media_types and media_type != MediaType.UNKNOWN:
                    skipped_files += 1
                    continue

                # Create a MediaFile object
                media_file = MediaFile(
                    path=path.absolute(),
                    size=size,
                    media_type=media_type,
                    modified_date=modified_date,
                )

                # Add to results
                media_files.append(media_file)

                # Update type counter
                if media_type in by_media_type:
                    by_media_type[media_type] += 1

            except (PermissionError, OSError) as e:
                error_msg = f"Error accessing file {path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

    except (PermissionError, OSError) as e:
        error_msg = f"Error scanning directory {root_dir}: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Calculate scan duration
    scan_duration = time.time() - start_time

    # Create the scan result
    result = ScanResult(
        total_files=total_files,
        media_files=media_files,
        skipped_files=skipped_files,
        by_media_type=by_media_type,
        errors=errors,
        scan_duration_seconds=scan_duration,
        root_dir=root_dir.absolute(),
    )

    logger.info(
        f"Scan completed in {scan_duration:.2f}s. "
        f"Found {len(media_files)} media files out of {total_files} total files."
    )

    return result
