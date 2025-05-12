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

# MEDIA_EXTENSIONS is intentionally broad to support all major video/audio
# formats used by Plex, Jellyfin, Emby, etc.
# Reason: This ensures maximum compatibility with the naming rules outlined in
# MEDIA-SERVER FILE-NAMING & METADATA GUIDE.md.
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

# IGNORED_EXTENSIONS covers common sidecar, subtitle, and metadata files that
# should never be treated as media.
# Reason: These files are not ingested by media servers as primary content and
# would pollute scan results.
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

# TV_PATTERNS are derived from the most common episode naming conventions in the
# media server ecosystem.
# Reason: These patterns are recommended in the MEDIA-SERVER FILE-NAMING &
# METADATA GUIDE.md and are recognized by Plex/Jellyfin scanners.
TV_PATTERNS = [
    r"s\d{1,2}e\d{1,2}",  # S01E01
    r"\bs\d{1,2}\s*e\d{1,2}\b",  # s01 e01, s01e01 with word boundaries
    r"\b\d{1,2}x\d{1,2}\b",  # 1x01 with word boundaries
    r"\bseason\s+\d+\b",  # Season 1 with word boundaries
    r"\bepisode\s+\d+\b",  # Episode 1 with word boundaries
    r"\b(?:s|season)\s*\d+\b.*\b(?:e|episode)\s*\d+\b",  # Season X Episode Y pattern
]

# Directory hints are used to infer media type from parent folder names.
# Reason: Most media libraries are organized by top-level folders (e.g., Movies/,
# TV/, Music/), so this provides a strong hint when file patterns are ambiguous.
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
    # Only include if the guessed type is in the allowed list
    return media_type in media_types


def _create_media_file(
    file_path: Path, verify_hash: bool, errors: List[str]
) -> Tuple[MediaFile, MediaType]:
    """Create a MediaFile object from a file path.

    Args:
        file_path: Path to the file
        verify_hash: Whether to compute the file hash
        errors: List to append any errors to

    Returns:
        Tuple of (MediaFile, MediaType)
    """
    # Guess media type
    media_type = guess_media_type(file_path)

    try:
        # Get file size and modified date
        stat = file_path.stat()
        size = stat.st_size
        modified_date = datetime.fromtimestamp(stat.st_mtime)

        # Compute hash if requested
        file_hash = None
        if verify_hash:
            try:
                file_hash = sha256sum(file_path)
            except (PermissionError, FileNotFoundError, IOError) as e:
                # Log but continue if hash can't be computed
                errors.append(f"Failed to compute hash for {file_path}: {str(e)}")

        # Create the MediaFile object
        media_file = MediaFile(
            path=file_path.absolute(),
            size=size,
            media_type=media_type,
            modified_date=modified_date,
            hash=file_hash,
        )

        return media_file, media_type
    except (PermissionError, FileNotFoundError, OSError) as e:
        # Log the error and return a placeholder
        errors.append(f"Error accessing {file_path}: {str(e)}")
        # Return a placeholder with minimal information
        media_file = MediaFile(
            path=file_path.absolute(),
            size=0,
            media_type=media_type,
            modified_date=datetime.now(),
        )
        return media_file, media_type


def _process_file(
    file_path: Path,
    target_extensions: Set[str],
    media_types: List[MediaType],
    verify_hash: bool,
    errors: List[str],
) -> Tuple[Optional[MediaFile], MediaType, bool]:
    """Process a single file and create a MediaFile if it's a valid media file.

    Args:
        file_path: Path to the file
        target_extensions: Set of extensions to include
        media_types: List of media types to include
        verify_hash: Whether to compute file hash
        errors: List to append any errors to

    Returns:
        Tuple of (MediaFile or None, MediaType, whether the file was skipped)
    """
    try:
        # Check if it's a valid media file
        if not _is_valid_media_file(file_path, target_extensions, media_types):
            # Return placeholder for skipped files
            media_type = guess_media_type(file_path)
            return None, media_type, True

        # Create the MediaFile object
        media_file, media_type = _create_media_file(file_path, verify_hash, errors)
        return media_file, media_type, False
    except Exception as e:
        # Log unexpected errors but continue processing
        errors.append(f"Unexpected error processing {file_path}: {str(e)}")
        return None, MediaType.UNKNOWN, True


@dataclass
class ScanOptions:
    """Options for the scan process."""

    recursive: bool = True
    include_hidden: bool = False
    verify_hash: bool = False
    platform: str = "plex"
    target_extensions: Set[str] = field(default_factory=set)
    media_types: List[MediaType] = field(default_factory=list)


def _handle_directory_item(
    item: Path,
    options: ScanOptions,
) -> Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]]:
    """Handle a single directory item (file or subdirectory).

    Args:
        item: Path to the item
        options: Scan options

    Returns:
        Tuple of (
            total files examined,
            skipped files,
            list of media files found,
            count by media type,
            list of errors
        )
    """
    # Initialize results
    total_files = 0
    skipped_files = 0
    media_files: List[MediaFile] = []
    by_media_type: Dict[MediaType, int] = {}
    errors: List[str] = []

    # Check if it's a hidden item
    if is_hidden(item) and not options.include_hidden:
        return total_files, skipped_files, media_files, by_media_type, errors

    try:
        if item.is_file():
            # Process the file
            total_files += 1
            media_file, media_type, was_skipped = _process_file(
                item,
                options.target_extensions,
                options.media_types,
                options.verify_hash,
                errors,
            )

            if was_skipped:
                skipped_files += 1
            elif media_file is not None:
                media_files.append(media_file)
                # Update count by media type
                by_media_type[media_type] = by_media_type.get(media_type, 0) + 1

        elif item.is_dir() and options.recursive:
            # For hidden directories, we need to check again for include_hidden
            if not is_hidden(item) or options.include_hidden:
                # Recursively process subdirectory
                sub_results = _process_directory(item, options)
                _update_aggregated_results(
                    [total_files, skipped_files, media_files, by_media_type, errors],
                    sub_results,
                )
    except (PermissionError, FileNotFoundError, OSError) as e:
        # Log access errors but continue processing
        errors.append(f"Error accessing {item}: {str(e)}")

    return total_files, skipped_files, media_files, by_media_type, errors


def _update_aggregated_results(
    aggregated: list[Union[int, List[MediaFile], Dict[MediaType, int], List[str]]],
    additional: Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]],
) -> None:
    """Update aggregated results with additional results.

    Args:
        aggregated: List of aggregated results (will be modified in-place)
        additional: Tuple of additional results

    Returns:
        None (updates aggregated in-place)
    """
    # Update total_files
    aggregated[0] = cast(int, aggregated[0]) + additional[0]
    # Update skipped_files
    aggregated[1] = cast(int, aggregated[1]) + additional[1]
    # Update media_files
    cast(List[MediaFile], aggregated[2]).extend(additional[2])
    # Update by_media_type
    by_media_type = cast(Dict[MediaType, int], aggregated[3])
    for media_type, count in additional[3].items():
        by_media_type[media_type] = by_media_type.get(media_type, 0) + count
    # Update errors
    cast(List[str], aggregated[4]).extend(additional[4])


def _process_directory(
    current_dir: Path,
    options: ScanOptions,
) -> Tuple[int, int, List[MediaFile], Dict[MediaType, int], List[str]]:
    """Process a directory and find media files.

    Args:
        current_dir: Directory to process
        options: Scan options

    Returns:
        Tuple of (
            total files examined,
            skipped files,
            list of media files found,
            count by media type,
            list of errors
        )
    """
    # Initialize results
    total_files = 0
    skipped_files = 0
    media_files: List[MediaFile] = []
    by_media_type: Dict[MediaType, int] = {}
    errors: List[str] = []

    # Check if it's a hidden directory
    if is_hidden(current_dir) and not options.include_hidden:
        return total_files, skipped_files, media_files, by_media_type, errors

    # Skip directory if it doesn't exist or can't be accessed
    if not current_dir.exists():
        errors.append(f"Directory does not exist: {current_dir}")
        return total_files, skipped_files, media_files, by_media_type, errors
    elif not current_dir.is_dir():
        errors.append(f"Path is not a directory: {current_dir}")
        return total_files, skipped_files, media_files, by_media_type, errors

    try:
        # Process each item in the directory
        for item in current_dir.iterdir():
            item_results = _handle_directory_item(item, options)
            _update_aggregated_results(
                [total_files, skipped_files, media_files, by_media_type, errors],
                item_results,
            )
    except (PermissionError, OSError) as e:
        errors.append(f"Error accessing directory {current_dir}: {str(e)}")

    return total_files, skipped_files, media_files, by_media_type, errors


def scan_directory(
    root_dir: Path,
    media_types: List[MediaType] | None = None,
    *,  # Force the rest of the parameters to be keyword-only
    options: Optional[ScanOptions] = None,
) -> ScanResult:
    """Scan a directory for media files.

    Args:
        root_dir: The directory to scan
        media_types: Types of media to include. If None, includes all types.
        options: Scan options including recursive, include_hidden, verify,
            and platform settings. If None, default options will be used.

    Returns:
        ScanResult object containing the found media files and statistics

    Raises:
        FileNotFoundError: If the directory doesn't exist
        ValueError: If the path is not a directory
    """
    # Validate the directory exists
    if not root_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {root_dir}")
    if not root_dir.is_dir():
        raise ValueError(f"Path is not a directory: {root_dir}")

    # Use absolute path to avoid relative path issues
    root_dir = root_dir.absolute()

    # Set up options with defaults if none provided
    if options is None:
        options = ScanOptions()

    # Set up media types
    if media_types:
        options.media_types = media_types
    elif not options.media_types:
        # If no media types specified, include all
        options.media_types = [
            MediaType.TV,
            MediaType.MOVIE,
            MediaType.MUSIC,
        ]

    # Set up target extensions based on media types
    options.target_extensions = set()
    for media_type in options.media_types:
        if media_type in MEDIA_EXTENSIONS:
            options.target_extensions.update(MEDIA_EXTENSIONS[media_type])

    # Start timing the scan
    start_time = time.time()

    # Process the directory
    total_files, skipped_files, media_files, by_media_type, errors = _process_directory(
        root_dir, options
    )

    # Calculate scan duration
    scan_duration = time.time() - start_time

    # For backward compatibility with tests
    total_files_examined = total_files
    skipped_files_count = skipped_files
    media_files_list = media_files
    by_media_type_dict = by_media_type
    errors_list = errors
    scan_duration_seconds = scan_duration

    # Create and return the scan result
    result = ScanResult(
        files=media_files_list,
        root_dir=root_dir,
        media_types=options.media_types,
        platform=options.platform,
        # Include backward compatibility fields
        total_files=max(
            total_files_examined, len(media_files_list)
        ),  # Ensure total files is at least the number of files found
        skipped_files=skipped_files_count,
        by_media_type=by_media_type_dict,
        errors=errors_list,
        scan_duration_seconds=scan_duration_seconds,
    )

    return result
