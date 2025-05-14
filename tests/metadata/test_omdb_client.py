"""Tests for the OMDb client in NameGnome.

This module verifies that OMDb data is fetched and merged into MediaMetadata
as required by Sprint 2.5. TMDB fields take priority over OMDb when both are
present.
"""

from unittest.mock import patch

import pytest

from namegnome.metadata.models import ExternalIDs, MediaMetadata, MediaMetadataType


@pytest.mark.asyncio
async def test_omdb_fetch_and_merge(monkeypatch: object) -> None:
    """Test that OMDb data is fetched and merged into MediaMetadata.

    TMDB fields take priority over OMDb when both are present. This is the
    expected-flow test for the OMDb client.
    """
    # Mock OMDb API response
    omdb_response = {
        "Title": "Inception",
        "Year": "2010",
        "imdbRating": "8.8",
        "Plot": "A thief who steals corporate secrets...",  # pragma: allowlist secret
        "Response": "True",
    }
    # Mock TMDB metadata (no rating, no plot)
    tmdb_metadata = MediaMetadata(
        title="Inception",
        media_type=MediaMetadataType.MOVIE,
        provider="tmdb",
        provider_id="12345",
        year=2010,
        external_ids=ExternalIDs(imdb_id="tt1375666"),
        overview=None,
        vote_average=None,
    )

    # Patch httpx.AsyncClient.get to return the OMDb response
    class MockResponse:
        def __init__(self, json_data: dict) -> None:
            self._json = json_data
            self.status_code = 200

        def json(self) -> dict:
            return self._json

    async def mock_get(*args: object, **kwargs: object) -> object:
        return MockResponse(omdb_response)

    with patch("httpx.AsyncClient.get", new=mock_get):
        from namegnome.metadata.clients.omdb import fetch_and_merge_omdb

        merged = await fetch_and_merge_omdb(
            tmdb_metadata, api_key="dummy", title="Inception", year=2010
        )
    assert merged.title == "Inception"
    assert merged.year == 2010
    assert merged.vote_average == 8.8
    assert merged.overview == "A thief who steals corporate secrets..."


@pytest.mark.asyncio
async def test_omdb_merge_priority(monkeypatch: object) -> None:
    """Test that TMDB fields take priority over OMDb when both are present.

    If TMDB provides vote_average or overview, OMDb data does not overwrite
    them. This is the merge-priority test for the OMDb client.
    """
    omdb_response = {
        "Title": "Inception",
        "Year": "2010",
        "imdbRating": "7.0",
        "Plot": "OMDb plot should not overwrite TMDB.",  # pragma: allowlist secret
        "Response": "True",
    }
    tmdb_metadata = MediaMetadata(
        title="Inception",
        media_type=MediaMetadataType.MOVIE,
        provider="tmdb",
        provider_id="12345",
        year=2010,
        external_ids=ExternalIDs(imdb_id="tt1375666"),
        overview="TMDB plot should win.",
        vote_average=9.1,
    )

    class MockResponse:
        def __init__(self, json_data: dict) -> None:
            self._json = json_data
            self.status_code = 200

        def json(self) -> dict:
            return self._json

    async def mock_get(*args: object, **kwargs: object) -> object:
        return MockResponse(omdb_response)

    with patch("httpx.AsyncClient.get", new=mock_get):
        from namegnome.metadata.clients.omdb import fetch_and_merge_omdb

        merged = await fetch_and_merge_omdb(
            tmdb_metadata, api_key="dummy", title="Inception", year=2010
        )
    assert merged.vote_average == 9.1
    assert merged.overview == "TMDB plot should win."
