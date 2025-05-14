"""Tests for the AniList GraphQL client.

This module contains tests for the AniList GraphQL client implementation,
which is used to fetch anime metadata with absolute episode numbering support.
Tests cover expected flow, edge cases, and errors.
"""

import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from namegnome.metadata.clients.anilist.client import AniListClient
from namegnome.metadata.models import MediaMetadataType


@pytest.fixture
def test_fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "test_fixtures" / "anilist"


@pytest.fixture
def search_response(test_fixtures_dir: Path) -> dict:
    """Load the AniList search response fixture."""
    with open(test_fixtures_dir / "search_response.json") as f:
        return json.load(f)


@pytest.fixture
def details_response(test_fixtures_dir: Path) -> dict:
    """Load the AniList details response fixture."""
    with open(test_fixtures_dir / "details_response.json") as f:
        return json.load(f)


@pytest.fixture
def rate_limit_response(test_fixtures_dir: Path) -> dict:
    """Load the AniList rate-limit (429) error response fixture."""
    with open(test_fixtures_dir / "rate_limit_response.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_anilist_search(search_response: dict) -> None:
    """Test that AniList search returns correctly mapped MediaMetadata."""
    # Mock the API response
    with respx.mock:
        respx.post("https://graphql.anilist.co").mock(
            return_value=Response(200, json=search_response)
        )

        # Create client and search
        client = AniListClient()
        results = await client.search("Death Note")

        # Assertions
        assert len(results) == 1
        assert results[0].title == "Death Note"
        assert results[0].media_type == MediaMetadataType.TV_SHOW
        assert results[0].provider == "anilist"
        assert results[0].provider_id == "1535"
        assert results[0].year == 2006
        assert results[0].number_of_episodes == 37


@pytest.mark.asyncio
async def test_anilist_search_not_found() -> None:
    """Test that AniList search handles empty results."""
    # Mock empty API response
    empty_response = {"data": {"Media": None}}

    with respx.mock:
        respx.post("https://graphql.anilist.co").mock(
            return_value=Response(200, json=empty_response)
        )

        # Create client and search
        client = AniListClient()
        results = await client.search("NonExistentAnime12345")

        # Assertions
        assert len(results) == 0


@pytest.mark.asyncio
async def test_anilist_details(details_response: dict) -> None:
    """Test that AniList details returns correctly mapped MediaMetadata with episode info."""
    # Mock the API response
    with respx.mock:
        respx.post("https://graphql.anilist.co").mock(
            return_value=Response(200, json=details_response)
        )

        # Create client and fetch details
        client = AniListClient()
        result = await client.details("1535")

        # Assertions
        assert result.title == "Death Note"
        assert result.media_type == MediaMetadataType.TV_SHOW
        assert result.provider == "anilist"
        assert result.provider_id == "1535"
        assert result.year == 2006
        assert result.number_of_episodes == 37
        assert result.overview is not None

        # Check episodes
        assert len(result.episodes) == 2
        assert result.episodes[0].title == "Rebirth"
        assert result.episodes[0].episode_number == 1
        assert result.episodes[0].season_number == 1
        assert result.episodes[0].absolute_number == 1

        assert result.episodes[1].title == "Confrontation"
        assert result.episodes[1].episode_number == 2
        assert result.episodes[1].season_number == 1
        assert result.episodes[1].absolute_number == 2


@pytest.mark.asyncio
async def test_anilist_error_handling() -> None:
    """Test that AniList client handles API errors gracefully."""
    # Mock error response
    error_response = {
        "errors": [
            {
                "message": "Not Found",
                "status": 404,
            }
        ]
    }

    with respx.mock:
        respx.post("https://graphql.anilist.co").mock(
            return_value=Response(404, json=error_response)
        )

        # Create client
        client = AniListClient()

        # Assertions for search error
        results = await client.search("Error Test")
        assert len(results) == 0

        # Assertions for details error
        with pytest.raises(Exception):
            await client.details("9999999")


@pytest.mark.asyncio
async def test_anilist_rate_limit_handling(rate_limit_response: dict) -> None:
    """Test that AniList client handles rate-limit (HTTP 429) errors gracefully."""
    with respx.mock:
        respx.post("https://graphql.anilist.co").mock(
            return_value=Response(429, json=rate_limit_response)
        )

        client = AniListClient()

        # Search should return empty list on 429
        results = await client.search("AnyTitle")
        assert results == []

        # Details should raise an exception on 429
        with pytest.raises(Exception):
            await client.details("1535")
