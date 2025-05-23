"""Utilities for computing file hashes.

This module provides functions for computing SHA-256 checksums of files, used for
file integrity verification and duplicate detection.
- Default chunk size is 8 MB for efficient hashing of large media files (see
  PLANNING.md for rationale).
- Used throughout the codebase for verifying file moves and detecting identical
  files.
"""

import hashlib
from pathlib import Path
from typing import Union


def sha256sum(path: Union[str, Path], chunk_size: int = 8_388_608) -> str:
    """Compute the SHA-256 checksum of a file.

    Args:
        path: The path to the file to hash
        chunk_size: The size of chunks to read (8 MB default)

    Returns:
        The hexadecimal digest of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
        ValueError: If the path is not a file
    """
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Reason: 8 MB chunk size balances memory usage and performance for large
    # media files (see PLANNING.md).
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()
