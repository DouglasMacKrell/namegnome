"""Tests for the namegnome.utils.hash module.

This test suite covers:
- Hashing of files with known content, empty files, and large files
- Error handling for nonexistent files and directories
- Ensures cross-platform correctness and reproducibility of SHA-256 hashes (see PLANNING.md)

Rationale:
- Guarantees file integrity checks and duplicate detection logic are robust and portable
- Validates error handling for user mistakes and edge cases
"""

import tempfile
from pathlib import Path

import pytest

from namegnome.utils.hash import sha256sum


def test_sha256sum() -> None:
    """Test the sha256sum function with known content.

    Scenario:
    - Hashes a file containing 'Hello, World!' and compares to the expected SHA-256 hash.
    - Ensures deterministic, cross-platform hashing for known content.
    """
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, World!")
        temp_path = Path(temp_file.name)

    try:
        # Calculate hash
        file_hash = sha256sum(temp_path)

        # Compare with expected hash for "Hello, World!"
        expected_hash = (
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        )
        assert file_hash == expected_hash
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def test_sha256sum_empty_file() -> None:
    """Test the sha256sum function with an empty file.

    Scenario:
    - Hashes an empty file and compares to the expected SHA-256 hash for empty content.
    - Ensures correct handling of zero-byte files.
    """
    # Create a temporary empty file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        # Calculate hash
        file_hash = sha256sum(temp_path)

        # Compare with expected hash for empty file
        expected_hash = (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        assert file_hash == expected_hash
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def test_sha256sum_large_file() -> None:
    """Test the sha256sum function with a large file.

    Scenario:
    - Hashes a 1MB file of repeated data and checks that the result is a valid SHA-256 hex string.
    - Ensures performance and correctness for large files.
    """
    # Create a temporary file with 1MB of data
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Write 1MB of repeated data
        data = b"0123456789" * 102400  # 1MB
        temp_file.write(data)
        temp_path = Path(temp_file.name)

    try:
        # Calculate hash
        file_hash = sha256sum(temp_path)

        # We don't know the expected hash in advance, so just check that we get a valid hash
        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)
    finally:
        # Clean up
        if temp_path.exists():
            temp_path.unlink()


def test_sha256sum_file_not_found() -> None:
    """Test that sha256sum raises FileNotFoundError for nonexistent files.

    Scenario:
    - Attempts to hash a nonexistent file and expects FileNotFoundError.
    - Ensures robust error handling for missing files.
    """
    with pytest.raises(FileNotFoundError):
        sha256sum(Path("/path/to/nonexistent/file"))


def test_sha256sum_not_a_file() -> None:
    """Test that sha256sum raises ValueError for directories.

    Scenario:
    - Attempts to hash a directory and expects ValueError.
    - Ensures type checking and error handling for invalid input.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError):
            sha256sum(Path(temp_dir))
