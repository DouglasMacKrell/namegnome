"""Tests for namegnome.metadata.utils helper functions."""

from namegnome.metadata import utils as mu
import pytest


def test_normalize_title():
    raw = "The: Adventures of _Sherlock_ Holmes!"
    expected = "the adventures of sherlock holmes"
    assert mu.normalize_title(raw) == expected


def test_strip_articles():
    assert mu.strip_articles("The Great Escape") == "Great Escape"
    assert mu.strip_articles("An Unexpected Journey") == "Unexpected Journey"
    assert mu.strip_articles("A Series of Unfortunate Events") == "Series of Unfortunate Events"
    # Titles without articles remain unchanged
    assert mu.strip_articles("Escape Plan") == "Escape Plan"


def test_sanitize_title():
    raw = "Pups & The °Baa-aa"  # special chars and ampersand
    # Hyphens and special chars are removed, multiple 'a' collapse remains
    assert mu.sanitize_title(raw) == "pups the baaaa"


def test_load_fixture_not_found(tmp_path, monkeypatch):
    """load_fixture should raise FileNotFoundError when file is absent."""
    # Monkeypatch Path.parents to use tmp path to ensure isolation
    monkeypatch.setattr(mu.Path, "exists", lambda self: False)
    with pytest.raises(FileNotFoundError):
        mu.load_fixture("tvdb", "nonexistent_file") 