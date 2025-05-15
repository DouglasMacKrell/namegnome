"""Utility functions for metadata processing.

This module provides helpers for loading test fixtures, normalizing titles, and
stripping articles for metadata providers.

- Used by metadata clients and tests to ensure consistent, provider-agnostic
  processing of media titles and metadata.
- Designed for testability, normalization, and cross-provider compatibility
  (see PLANNING.md, README.md, and provider integration docs).

Design:
- load_fixture enables deterministic, offline testing of metadata clients using
  static JSON files.
- normalize_title and strip_articles provide consistent title processing for
  fuzzy matching and deduplication.
"""

import json
from pathlib import Path
from typing import Any


def load_fixture(provider: str, fixture_name: str) -> dict[str, Any]:
    """Load a fixture JSON file from the tests/fixtures directory.

    Args:
        provider: The provider name (e.g., 'tmdb', 'tvdb').
        fixture_name: The name of the fixture file without extension.

    Returns:
        The loaded JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the fixture file doesn't exist.
        json.JSONDecodeError: If the fixture contains invalid JSON.

    Reason:
        Enables deterministic, offline testing of metadata clients using static
        JSON files (see tests/fixtures/stubs).
    """
    # Calculate the path relative to the current file
    # When running tests, this will be in the project's test fixtures directory
    # The path should point to namegnome/tests/fixtures/stubs/provider
    # Using parents[3] since: current file -> metadata -> src -> namegnome -> tests
    base_path = Path(__file__).parents[3] / "tests" / "fixtures" / "stubs" / provider

    fixture_path = base_path / f"{fixture_name}.json"

    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def normalize_title(title: str) -> str:
    """Normalize a title by removing special characters and converting to lowercase.

    Args:
        title: The title to normalize.

    Returns:
        The normalized title.

    Reason:
        Ensures consistent, provider-agnostic title matching for fuzzy search and
        deduplication.
    """
    # Remove special characters, extra spaces, and convert to lowercase
    normalized = "".join(c.lower() for c in title if c.isalnum() or c.isspace())
    normalized = " ".join(normalized.split())
    return normalized


def strip_articles(title: str) -> str:
    """Remove leading articles (the, a, an) from a title.

    Args:
        title: The title to process.

    Returns:
        The title without leading articles.

    Reason:
        Improves sorting, matching, and display by ignoring common English
        articles.
    """
    articles = ["the ", "a ", "an "]
    lower_title = title.lower()

    for article in articles:
        if lower_title.startswith(article):
            return title[len(article) :]

    return title
