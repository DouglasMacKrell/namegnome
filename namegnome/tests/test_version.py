"""Test version import works correctly."""

from namegnome import __version__


def test_version() -> None:
    """Test that version is a string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0
