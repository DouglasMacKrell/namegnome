"""Tests for the MusicBrainzClient metadata provider implementation."""

import httpx
import pytest
import respx

from namegnome.metadata.models import MediaMetadataType
from namegnome.metadata.musicbrainz_client import (
    MusicBrainzClient,
    NotFoundError,
    RateLimitError,
)


@pytest.mark.asyncio
async def test_fetch_album_metadata_success(
    respx_mock: respx.MockRouter,
) -> None:
    """MusicBrainzClient returns correct MediaMetadata for a known album/artist."""
    album_title = "Discovery"
    artist_name = "Daft Punk"
    musicbrainz_id = "f27ec8db-af05-4f36-916e-3d57f91ecf5e"
    respx_mock.get(
        "https://musicbrainz.org/ws/2/release/",
        params={
            "query": f"release:{album_title} AND artist:{artist_name}",
            "fmt": "json",
        },
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "id": musicbrainz_id,
                        "title": album_title,
                        "date": "2001-03-12",
                        "artist-credit": [{"name": artist_name}],
                        "media": [
                            {
                                "tracks": [
                                    {
                                        "title": "One More Time",
                                        "number": "1",
                                        "length": 320000,
                                    },
                                    {
                                        "title": "Aerodynamic",
                                        "number": "2",
                                        "length": 210000,
                                    },
                                ]
                            }
                        ],
                    }
                ]
            },
        )
    )
    client = MusicBrainzClient()
    metadata = await client.search_album(album_title, artist_name)
    assert metadata.title == album_title
    assert metadata.media_type == MediaMetadataType.MUSIC_ALBUM
    assert metadata.provider == "musicbrainz"
    assert metadata.provider_id == musicbrainz_id
    assert metadata.year == 2001
    assert artist_name in metadata.artists
    # TODO: assert tracks when implemented


@pytest.mark.asyncio
async def test_fetch_album_metadata_not_found(
    respx_mock: respx.MockRouter,
) -> None:
    """MusicBrainzClient raises NotFoundError when album is not found."""
    album_title = "Nonexistent Album"
    artist_name = "Unknown Artist"
    respx_mock.get(
        "https://musicbrainz.org/ws/2/release/",
        params={
            "query": f"release:{album_title} AND artist:{artist_name}",
            "fmt": "json",
        },
    ).mock(return_value=httpx.Response(200, json={"releases": []}))
    client = MusicBrainzClient()
    with pytest.raises(NotFoundError):
        await client.search_album(album_title, artist_name)


@pytest.mark.asyncio
async def test_fetch_album_metadata_rate_limited(
    respx_mock: respx.MockRouter,
) -> None:
    """MusicBrainzClient raises RateLimitError on HTTP 503 or rate limit response."""
    album_title = "Discovery"
    artist_name = "Daft Punk"
    respx_mock.get(
        "https://musicbrainz.org/ws/2/release/",
        params={
            "query": f"release:{album_title} AND artist:{artist_name}",
            "fmt": "json",
        },
    ).mock(return_value=httpx.Response(503, json={"error": "Rate limit exceeded"}))
    client = MusicBrainzClient()
    with pytest.raises(RateLimitError):
        await client.search_album(album_title, artist_name)


@pytest.mark.asyncio
async def test_musicbrainz_user_agent_header(
    respx_mock: respx.MockRouter,
) -> None:
    """MusicBrainzClient sets the correct User-Agent header on all requests."""
    album_title = "Discovery"
    artist_name = "Daft Punk"
    custom_ua = "test-agent/1.2.3 (https://example.com)"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"] == custom_ua
        return httpx.Response(
            200,
            json={
                "releases": [
                    {
                        "id": "id",
                        "title": album_title,
                        "date": "2001-03-12",
                        "artist-credit": [{"name": artist_name}],
                        "media": [],
                    }
                ]
            },
        )

    route = respx_mock.get(
        "https://musicbrainz.org/ws/2/release/",
        params={
            "query": f"release:{album_title} AND artist:{artist_name}",
            "fmt": "json",
        },
    ).mock(side_effect=handler)
    client = MusicBrainzClient(user_agent=custom_ua)
    await client.search_album(album_title, artist_name)
    assert route.called
