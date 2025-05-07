"""Utilities for tests."""

import os
from pathlib import Path


def abs_path(path_str: str) -> Path:
    r"""Create a platform-independent absolute path.

    Args:
        path_str: A Unix-style path string starting with '/'.

    Returns:
        A Path object with an absolute path that's valid on the current OS.
        On Windows, converts '/tmp/file.txt' to 'C:\\tmp\\file.txt'
        On Unix, keeps the path as is.
    """
    if os.name == "nt":  # Windows
        # Convert Unix-style paths to Windows absolute paths
        if path_str.startswith("/"):
            return Path("C:" + path_str.replace("/", "\\"))
    # For Unix systems, keep the path as is
    return Path(path_str)
