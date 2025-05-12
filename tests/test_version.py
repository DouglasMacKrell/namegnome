"""Test version import works correctly.

This test ensures that the package version is importable and non-empty.
- Guards against packaging errors where __version__ is missing or not set.
- Required for CI, release automation, and user-facing version reporting (see PLANNING.md).
"""

from namegnome import __version__


def test_version() -> None:
    """Test that version is a string and non-empty.

    Ensures that __version__ is defined, is a string, and is not empty.
    This is important for packaging, CI, and user-facing version reporting.
    """
    # Assert that __version__ is a string (required by packaging tools and PyPI).
    assert isinstance(__version__, str)
    # Assert that __version__ is not empty (prevents accidental blank releases).
    assert len(__version__) > 0
