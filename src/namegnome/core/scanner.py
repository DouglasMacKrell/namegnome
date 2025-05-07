"""Directory scanner for media files.

This module provides functionality to scan directories for media files
and classify them based on file extensions and patterns.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, cast

from namegnome.models.core import MediaFile, MediaType, ScanResult
from namegnome.utils.hash import sha256sum

# Logger for this module
logger = logging.getLogger(__name__)

# Common media file extensions by type
MEDIA_EXTENSIONS = {
    MediaType.TV: {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".webm"},
    MediaType.MOVIE: {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".webm"},
    MediaType.MUSIC: {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".alac"},
    # Include UNKNOWN to handle files that don't match specific media types
    MediaType.UNKNOWN: {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".m4v",
        ".ts",
        ".webm",
        ".mp3",
        ".flac",
        ".m4a",
        ".wav",
        ".ogg",
        ".aac",
        ".wma",
        ".alac",
    },
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
    r"\bs\d{1,2}\s*e\d{1,2}\b",  # s01 e01, s01e01 with word boundaries
    r"\b\d{1,2}x\d{1,2}\b",  # 1x01 with word boundaries
    r"\bseason\s+\d+\b",  # Season 1 with word boundaries
    r"\bepisode\s+\d+\b",  # Episode 1 with word boundaries
    r"\b(?:s|season)\s*\d+\b.*\b(?:e|episode)\s*\d+\b",  # Season X Episode Y pattern
]

# Directory names that suggest specific media types
DIRECTORY_HINTS = {
    MediaType.TV: {"tv", "shows", "series", "tv shows", "television"},
    MediaType.MOVIE: {"movies", "film", "films", "cinema"},
    MediaType.MUSIC: {"music", "audio", "songs", "albums", "mp3"},
}


def is_hidden(path: Path) -> bool:
    """Check if a path is hidden (starts with a dot).

    Args:
        path: The path to check

    Returns:
        True if the path is hidden, False otherwise
    """
    return any(part.startswith(".") for part in path.parts)


def _check_movie_pattern(path_str: str) -> bool:
    """Check if path matches movie pattern (year in parentheses).

    Args:
        path_str: Path string to check

    Returns:
        True if matches movie pattern, False otherwise
    """
    movie_pattern = re.compile(r"\(\d{4}\)", re.IGNORECASE)
    return bool(movie_pattern.search(path_str))


def _check_tv_patterns(path_str: str) -> bool:
    """Check if path matches any TV show patterns.

    Args:
        path_str: Path string to check

    Returns:
        True if matches any TV pattern, False otherwise
    """
    tv_patterns_compiled = [
        re.compile(pattern, re.IGNORECASE) for pattern in TV_PATTERNS
    ]
    return any(pattern.search(path_str) for pattern in tv_patterns_compiled)


def _check_directory_hints(path: Path) -> Optional[MediaType]:
    """Check parent directories for media type hints.

    Args:
        path: File path to check

    Returns:
        Detected MediaType or None if no hints found
    """
    for parent in path.parents:
        parent_name = parent.name.lower()
        for media_type, hints in DIRECTORY_HINTS.items():
            if parent_name in hints:
                return media_type
    return None


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

    path_str = str(path).lower()

    # First check for movie pattern - this is a strong indicator
    if _check_movie_pattern(path_str):
        return MediaType.MOVIE

    # Check for TV show patterns in the filename
    if _check_tv_patterns(path_str):
        return MediaType.TV

    # Look at parent directory names for hints
    directory_hint = _check_directory_hints(path)
    if directory_hint:
        return directory_hint

    # Default to UNKNOWN if we can't determine the type
    return MediaType.UNKNOWN


def _is_valid_media_file(
    file_path: Path, target_extensions: Set[str], media_types: List[MediaType]
) -> bool:
    """Check if a file is a valid media file based on extension and media type.

    Args:
        file_path: Path to the file
        target_extensions: Set of extensions to include
        media_types: List of media types to include

    Returns:
        True if file should be included, False if it should be skipped
    """
    # Skip based on extension
    ext = file_path.suffix.lower()
    if ext in IGNORED_EXTENSIONS or ext not in target_extensions:
        return False

    # Guess the media type
    media_type = guess_media_type(file_path)

    # Only include files if their media type is in the requested types
    # If the media type is UNKNOWN, skip it unless we're explicitly looking for UNKNOWN
    if media_type == MediaType.UNKNOWN:
        return MediaType.UNKNOWN in media_types

    # Skip files that don't match the requested media types
    return media_type in media_types


def _create_media_file(
    file_path: Path, verify_hash: bool, errors: List[str]
) -> Tuple[MediaFile, MediaType]:
    """Create a MediaFile object from a file path.

    Args:
        file_path: Path to the file
        verify_hash: Whether to calculate file hash
        errors: List to append any errors to

    Returns:
        Tuple of (MediaFile, MediaType)
    """
    # Get file stats
    stats = file_path.stat()
    size = stats.st_size
    modified_date = datetime.fromtimestamp(stats.st_mtime)

    # Guess the media type
    media_type = guess_media_type(file_path)

    # Calculate hash if requested
    file_hash = None
    if verify_hash:
        try:
            file_hash = sha256sum(file_path)
        except (PermissionError, OSError) as e:
            error_msg = f"Error calculating hash for {file_path}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Create a MediaFile object
    media_file = MediaFile(
        path=file_path.absolute(),
        size=size,
        media_type=media_type,
        modified_date=modified_date,
        hash=file_hash,
    )

    return media_file, media_type


def _process_file(
    file_path: Path,
    target_extensions: Set[str],
    media_types: List[MediaType],
    verify_hash: bool,
    errors: List[str],
) -> Tuple[Optional[MediaFile], MediaType, bool]:
    """Process a single file and determine if it should be included.

    Args:
        file_path: Path to the file
        target_extensions: Set of extensions to include
        media_types: List of media types to include
        verify_hash: Whether to calculate file hash
        errors: List to append any errors to

    Returns:
        Tuple of (MediaFile or None, MediaType, should_skip)
        If should_skip is True, the file should be skipped and not counted.
    """
    try:
        # Check if this is a valid media file we should process
        if not _is_valid_media_file(file_path, target_extensions, media_types):
            return None, MediaType.UNKNOWN, True

        # Create the media file object
        media_file, media_type = _create_media_file(file_path, verify_hash, errors)
        return media_file, media_type, False

    except (PermissionError, OSError) as e:
        error_msg = f"Error accessing file {file_path}: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return None, MediaType.UNKNOWN, True


@dataclass
class ScanOptions:
    """Options for the scan process."""

    recursive: bool = True
    include_hidden: bool = False
    verify_hash: bool = False
    target_extensions: Set[str] = field(default_factory=set)
    media_types: List[MediaType] = field(default_factory=list)


def _handle_directory_item(
    item: Path,
    options: ScanOptions,
) -> Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]]:
    """Process a single directory item recursively if needed.

    Args:
        item: Directory item (file or subdirectory) to process
        options: Scan options

    Returns:
        Tuple of (total_files, skipped_files, media_files, by_media_type, errors)
    """
    # If the item is a directory and recursion is enabled, process it
    if item.is_dir() and options.recursive:
        return _process_directory(item, options)

    # Return empty results for directories with recursion disabled
    if item.is_dir():
        return 0, 0, [], {media_type: 0 for media_type in options.media_types}, []

    # Process file (counts as 1 total file)
    total_files = 1
    skipped_files = 0
    media_files: List[MediaFile] = []
    by_media_type: Dict[MediaType, int] = {
        media_type: 0 for media_type in options.media_types
    }
    errors: List[str] = []

    # Process the file
    media_file, media_type, should_skip = _process_file(
        item,
        options.target_extensions,
        options.media_types,
        options.verify_hash,
        errors,
    )

    if should_skip:
        skipped_files += 1
    elif media_file:
        # Add to results
        media_files.append(media_file)

        # Update type counter
        if media_type in by_media_type:
            by_media_type[media_type] += 1

    return total_files, skipped_files, media_files, by_media_type, errors


def _update_aggregated_results(
    aggregated: list[Union[int, List[MediaFile], Dict[MediaType, int], List[str]]],
    additional: Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]],
) -> None:
    """Update aggregated results with additional results in-place.

    Args:
        aggregated: List containing current aggregated results
        additional: Tuple containing additional results to aggregate
    """
    sub_total, sub_skipped, sub_media_files, sub_by_media_type, sub_errors = additional

    # Update totals using the proper types
    aggregated[0] = cast(int, aggregated[0]) + sub_total  # total_files
    aggregated[1] = cast(int, aggregated[1]) + sub_skipped  # skipped_files

    # Add media files and errors
    cast(List[MediaFile], aggregated[2]).extend(sub_media_files)  # media_files
    cast(List[str], aggregated[4]).extend(sub_errors)  # errors

    # Update media type counters
    by_media_type = cast(Dict[MediaType, int], aggregated[3])
    for m_type, count in sub_by_media_type.items():
        if m_type in by_media_type:
            by_media_type[m_type] += count


def _process_directory(
    current_dir: Path,
    options: ScanOptions,
) -> Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]]:
    """Process a directory recursively.

    Args:
        current_dir: Directory to process
        options: Scan options

    Returns:
        Tuple of (total_files, skipped_files, media_files, by_media_type, errors)
    """
    # Initialize results
    total_files = 0
    skipped_files = 0
    media_files: List[MediaFile] = []
    by_media_type: Dict[MediaType, int] = {
        media_type: 0 for media_type in options.media_types
    }
    errors: List[str] = []

    # Using properly typed result list
    result: list[Union[int, List[MediaFile], Dict[MediaType, int], List[str]]] = [
        total_files,  # total_files
        skipped_files,  # skipped_files
        media_files,  # media_files
        by_media_type,  # by_media_type
        errors,  # errors
    ]

    try:
        for item in current_dir.iterdir():
            # Skip hidden items if not included
            if not options.include_hidden and is_hidden(item):
                if item.is_file():
                    skipped_files = cast(int, result[1]) + 1
                    result[1] = skipped_files
                continue

            # Process the item (file or directory)
            item_result = _handle_directory_item(item, options)

            # Aggregate results
            _update_aggregated_results(result, item_result)

    except (PermissionError, OSError) as e:
        error_msg = f"Error reading directory {current_dir}: {str(e)}"
        logger.error(error_msg)
        cast(List[str], result[4]).append(error_msg)  # errors

    # Convert result list to tuple with specific types for return
    return (
        cast(int, result[0]),
        cast(int, result[1]),
        cast(List[MediaFile], result[2]),
        cast(Dict[MediaType, int], result[3]),
        cast(List[str], result[4]),
    )


def scan_directory(
    root_dir: Path,
    media_types: List[MediaType] | None = None,
    recursive: bool = True,
    include_hidden: bool = False,
    verify_hash: bool = False,
) -> ScanResult:
    """Scan a directory for media files.

    Args:
        root_dir: The directory to scan.
        media_types: Optional list of media types to include (defaults to all).
        recursive: Whether to scan subdirectories.
        include_hidden: Whether to include hidden files and directories.
        verify_hash: Whether to calculate SHA-256 hash for each file.

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

    # When include_hidden is True, also include UNKNOWN media type
    # to detect files in hidden dirs
    if include_hidden and MediaType.UNKNOWN not in media_types:
        media_types = media_types + [MediaType.UNKNOWN]

    # Set of extensions to look for based on requested media types
    target_extensions: Set[str] = set()
    for media_type in media_types:
        if media_type in MEDIA_EXTENSIONS:
            target_extensions.update(MEDIA_EXTENSIONS[media_type])

    # Create scan options
    options = ScanOptions(
        recursive=recursive,
        include_hidden=include_hidden,
        verify_hash=verify_hash,
        target_extensions=target_extensions,
        media_types=media_types,
    )

    start_time = time.perf_counter()

    # Start the scan
    logger.info(f"Starting scan of {root_dir} for media types: {media_types}")

    try:
        # Process the root directory
        total_files, skipped_files, media_files, by_media_type, errors = (
            _process_directory(root_dir, options)
        )
    except (PermissionError, OSError) as e:
        error_msg = f"Error scanning directory {root_dir}: {str(e)}"
        logger.error(error_msg)
        return ScanResult(
            total_files=0,
            media_files=[],
            skipped_files=0,
            by_media_type={media_type: 0 for media_type in media_types},
            errors=[error_msg],
            scan_duration_seconds=0.0,
            root_dir=root_dir.absolute(),
        )

    # Calculate scan duration
    scan_duration_seconds = time.perf_counter() - start_time

    # Create the scan result
    result = ScanResult(
        total_files=total_files,
        media_files=media_files,
        skipped_files=skipped_files,
        by_media_type=by_media_type,
        errors=errors,
        scan_duration_seconds=scan_duration_seconds,
        root_dir=root_dir.absolute(),
    )

    logger.info(
        f"Scan completed in {scan_duration_seconds:.2f}s. "
        f"Found {len(media_files)} media files out of {total_files} total files."
    )

    return result
