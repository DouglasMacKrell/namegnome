"""Pytest configuration and fixtures for end-to-end testing."""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest
import requests
from unittest.mock import patch


# Test markers registration
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests requiring NAMEGNOME_E2E_TESTS=1"
    )
    config.addinivalue_line("markers", "api: Tests requiring real API keys")
    config.addinivalue_line("markers", "llm: Tests requiring real Ollama instance")


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless explicitly enabled."""
    if not os.environ.get("NAMEGNOME_E2E_TESTS"):
        skip_e2e = pytest.mark.skip(reason="E2E tests require NAMEGNOME_E2E_TESTS=1")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)


@pytest.fixture(scope="session")
def e2e_environment() -> Dict[str, Any]:
    """Detect available E2E testing dependencies and configuration.

    Returns:
        Dict containing environment information:
        {
            "api_keys_available": bool,
            "ollama_available": bool,
            "tvdb_key": str | None,
            "tmdb_key": str | None,
            "omdb_key": str | None,
            "ollama_url": str,
        }
    """
    env = {
        "api_keys_available": False,
        "ollama_available": False,
        "tvdb_key": None,
        "tmdb_key": None,
        "omdb_key": None,
        "ollama_url": "http://localhost:11434",
    }

    # Check for API keys
    tvdb_key = os.environ.get("TVDB_API_KEY") or os.environ.get(
        "NAMEGNOME_TVDB_API_KEY"
    )
    tmdb_key = os.environ.get("TMDB_API_KEY") or os.environ.get(
        "NAMEGNOME_TMDB_API_KEY"
    )
    omdb_key = os.environ.get("OMDB_API_KEY") or os.environ.get(
        "NAMEGNOME_OMDB_API_KEY"
    )

    if tvdb_key or tmdb_key or omdb_key:
        env["api_keys_available"] = True
        env["tvdb_key"] = tvdb_key
        env["tmdb_key"] = tmdb_key
        env["omdb_key"] = omdb_key

    # Check for Ollama availability
    try:
        response = requests.get(f"{env['ollama_url']}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:  # At least one model available
                env["ollama_available"] = True
    except (requests.RequestException, Exception):
        pass  # Ollama not available

    return env


@pytest.fixture
def skip_if_no_api_keys(e2e_environment):
    """Skip test if no API keys are available."""
    if not e2e_environment["api_keys_available"]:
        pytest.skip(
            "Test requires API keys (TVDB_API_KEY, TMDB_API_KEY, or OMDB_API_KEY)"
        )


@pytest.fixture
def skip_if_no_ollama(e2e_environment):
    """Skip test if Ollama is not available."""
    if not e2e_environment["ollama_available"]:
        pytest.skip("Test requires running Ollama instance with available models")


@pytest.fixture
def e2e_temp_dir():
    """Create isolated temporary directory for E2E test file operations."""
    with tempfile.TemporaryDirectory(prefix="namegnome_e2e_") as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def cached_api_responses():
    """Load cached API responses for dependency-free testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"

    responses = {"tvdb": {}, "tmdb": {}, "omdb": {}}

    # Load cached responses if available
    for provider in responses.keys():
        provider_dir = fixtures_dir / provider
        if provider_dir.exists():
            for json_file in provider_dir.glob("*.json"):
                import json

                with open(json_file) as f:
                    responses[provider][json_file.stem] = json.load(f)

    return responses


@pytest.fixture
def mock_api_providers(cached_api_responses):
    """Mock API providers to use cached responses instead of real API calls."""
    from namegnome.metadata.clients.tvdb import TVDBClient
    from namegnome.metadata.clients.tmdb import TMDBClient
    from namegnome.metadata.clients.omdb import OMDbClient

    # Create mock MediaMetadata objects from cached data
    from namegnome.metadata.models import MediaMetadata, MediaMetadataType, TVEpisode

    def mock_tvdb_search(self, title, year=None):
        # Convert cached TVDB data to MediaMetadata objects
        series_data = cached_api_responses["tvdb"].get("search_danger_mouse", [])
        episodes_data = cached_api_responses["tvdb"].get("episodes_danger_mouse", [])

        results = []
        for series in series_data:
            episodes = [
                TVEpisode(
                    title=ep["episodeName"],
                    episode_number=ep["airedEpisodeNumber"],
                    season_number=ep["airedSeason"],
                    air_date=None,
                    overview=ep.get("overview", ""),
                )
                for ep in episodes_data
            ]

            meta = MediaMetadata(
                title=series["seriesName"],
                media_type=MediaMetadataType.TV_SHOW,
                provider="tvdb",
                provider_id=str(series["id"]),
                year=int(series["firstAired"].split("-")[0])
                if series.get("firstAired")
                else None,
                episodes=episodes,
                overview=series.get("overview", ""),
            )
            results.append(meta)
        return results

    def mock_tmdb_search(self, title, year=None):
        # Convert cached TMDB data to MediaMetadata objects
        search_data = cached_api_responses["tmdb"].get("search_danger_mouse", {})
        results = []

        for result in search_data.get("results", []):
            meta = MediaMetadata(
                title=result["name"],
                media_type=MediaMetadataType.TV_SHOW,
                provider="tmdb",
                provider_id=str(result["id"]),
                year=int(result["first_air_date"].split("-")[0])
                if result.get("first_air_date")
                else None,
                overview=result.get("overview", ""),
            )
            results.append(meta)
        return results

    def mock_omdb_search(self, title, year=None):
        # Convert cached OMDb data to MediaMetadata objects
        omdb_data = cached_api_responses["omdb"].get("search_danger_mouse", {})

        if omdb_data.get("Response") == "True":
            meta = MediaMetadata(
                title=omdb_data["Title"],
                media_type=MediaMetadataType.TV_SHOW,
                provider="omdb",
                provider_id=omdb_data["imdbID"],
                year=int(omdb_data["Year"].split("–")[0])
                if omdb_data.get("Year")
                else None,
                overview=omdb_data.get("Plot", ""),
            )
            return [meta]
        return []

    with (
        patch.object(TVDBClient, "search", mock_tvdb_search),
        patch.object(TMDBClient, "search", mock_tmdb_search),
        patch.object(OMDbClient, "search", mock_omdb_search),
    ):
        yield


@pytest.fixture
def mock_llm_deterministic():
    """Mock LLM to return deterministic responses for testing."""
    from tests.helpers.fake_prompt_orchestrator import stub_llm

    # Use high confidence for deterministic "auto" responses
    with stub_llm(confidence=0.90) as fake_orchestrator:
        yield fake_orchestrator


@pytest.fixture
def e2e_test_files(e2e_temp_dir):
    """Create test files for E2E testing using real mock data."""
    import shutil

    # Copy test files from existing mocks
    source_dir = Path(__file__).parent.parent / "mocks" / "tv" / "Danger Mouse 2015"
    target_dir = e2e_temp_dir / "Danger Mouse 2015"

    if source_dir.exists():
        shutil.copytree(source_dir, target_dir)
        # Return first few files for focused testing
        test_files = list(target_dir.glob("*.mp4"))[:3]  # Limit to 3 files for speed
        return test_files
    else:
        # Create minimal test files if mocks don't exist
        target_dir.mkdir(parents=True)
        test_files = []
        for i in range(1, 4):
            test_file = (
                target_dir / f"Danger Mouse 2015-S01E{i:02d}-Test Episode {i}.mp4"
            )
            test_file.write_text("fake video content")
            test_files.append(test_file)
        return test_files
