"""Tests for .env.example provider API key template.

Checks for file existence and required key variables.
"""

from pathlib import Path

REQUIRED_KEYS = [
    "TMDB_API_KEY",
    "TVDB_API_KEY",
    "OMDB_API_KEY",
    "FANARTTV_API_KEY",
]


def test_env_example_exists() -> None:
    """Test that .env.example exists in the project root."""
    path = Path(".env.example")
    assert path.exists(), ".env.example does not exist"


def test_env_example_includes_required_keys() -> None:
    """Test that .env.example includes all required provider API key variables."""
    path = Path(".env.example")
    content = path.read_text(encoding="utf-8")
    for key in REQUIRED_KEYS:
        assert key in content, f"{key} not found in .env.example"
