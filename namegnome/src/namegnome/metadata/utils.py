"""Utility functions for metadata processing."""

import json
import logging
from pathlib import Path
from typing import Any

# Create a logger for this module
logger = logging.getLogger(__name__)


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
    """
    # Calculate the path relative to the current file
    # When running tests, this will be in the project's test fixtures directory
    # The path should point to namegnome/tests/fixtures/stubs/provider
    # Using parents[3] since: current file -> metadata -> src -> namegnome -> tests
    base_path = Path(__file__).parents[3] / "tests" / "fixtures" / "stubs" / provider

    # Check if path exists and is a directory, if not create it
    if not base_path.exists():
        logger.warning(f"Creating missing fixture directory: {base_path}")
        base_path.mkdir(parents=True, exist_ok=True)

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
    """
    articles = ["the ", "a ", "an "]
    lower_title = title.lower()

    for article in articles:
        if lower_title.startswith(article):
            return title[len(article) :]

    return title
