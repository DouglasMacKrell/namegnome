"""Utilities for calculating file hashes."""

import hashlib
from pathlib import Path


def sha256sum(path: Path, chunk_size: int = 8_388_608) -> str:
    """Calculate the SHA-256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Size of chunks to read (8MB default).

    Returns:
        The SHA-256 hash as a hexadecimal string.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If there are permission issues reading the file.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    sha256 = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
