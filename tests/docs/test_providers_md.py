"""Tests for docs/providers.md provider configuration documentation.

Checks for file existence, table structure, and provider listing.
"""

from pathlib import Path

PROVIDERS = [
    ("TMDB", "TMDB_API_KEY"),
    ("TVDB", "TVDB_API_KEY"),
    ("MusicBrainz", None),
    ("OMDb", "OMDB_API_KEY"),
    ("Fanart.tv", "FANARTTV_API_KEY"),
    ("TheAudioDB", None),
    ("AniList", None),
]

REQUIRED_COLUMNS = ["Provider", "Required Key", "Free Tier", "Scopes"]


def test_providers_md_exists() -> None:
    """Test that docs/providers.md exists."""
    path = Path("docs/providers.md")
    assert path.exists(), "docs/providers.md does not exist"


def test_providers_md_table_structure() -> None:
    """Test that the provider table contains all required columns."""
    path = Path("docs/providers.md")
    content = path.read_text(encoding="utf-8")
    for col in REQUIRED_COLUMNS:
        assert col in content, f"Missing column: {col} in providers.md table"


def test_providers_md_lists_all_providers() -> None:
    """Test that all implemented providers are listed in the table."""
    path = Path("docs/providers.md")
    content = path.read_text(encoding="utf-8")
    for provider, _ in PROVIDERS:
        assert provider in content, f"Provider {provider} not found in providers.md"
