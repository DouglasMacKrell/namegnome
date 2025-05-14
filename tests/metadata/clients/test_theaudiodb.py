"""Tests for the TheAudioDBClient metadata provider implementation."""

from pathlib import Path

import httpx
import pytest
import respx

from namegnome.metadata.clients.theaudiodb import TheAudioDBClient, fetch_album_thumb
from namegnome.metadata.models import ArtworkImage, MediaMetadataType


@pytest.mark.asyncio
async def test_search_artist_expected_flow(respx_mock: respx.MockRouter) -> None:
    """TheAudioDBClient returns correct MediaMetadata for a known artist."""
    artist_name = "Daft Punk"
    theaudiodb_id = "112024"
    api_url = "https://theaudiodb.com/api/v1/json/2/search.php"
    respx_mock.get(api_url, params={"s": artist_name}).mock(
        return_value=httpx.Response(
            200,
            json={
                "artists": [
                    {
                        "idArtist": theaudiodb_id,
                        "strArtist": artist_name,
                        "intFormedYear": "1993",
                        "strGenre": "Electronic",
                        "strArtistThumb": "https://www.theaudiodb.com/images/media/artist/thumb/daftpunk.jpg",
                        "strBiographyEN": "Daft Punk is a French electronic music duo...",
                    }
                ]
            },
        )
    )
    client = TheAudioDBClient()
    results = await client.search(artist_name)
    assert results
    meta = results[0]
    assert meta.title == artist_name
    assert meta.media_type == MediaMetadataType.MUSIC_ARTIST
    assert meta.provider == "theaudiodb"
    assert meta.provider_id == theaudiodb_id
    assert "Electronic" in meta.genres
    assert meta.artwork
    assert (
        str(meta.artwork[0].url)
        == "https://www.theaudiodb.com/images/media/artist/thumb/daftpunk.jpg"
    )
    assert meta.overview is not None
    assert meta.overview.startswith("Daft Punk is a French electronic music duo")


@pytest.mark.asyncio
async def test_search_artist_not_found(respx_mock: respx.MockRouter) -> None:
    """TheAudioDBClient returns an empty list if artist is not found."""
    artist_name = "Nonexistent Artist"
    api_url = "https://theaudiodb.com/api/v1/json/2/search.php"
    respx_mock.get(api_url, params={"s": artist_name}).mock(
        return_value=httpx.Response(200, json={"artists": None})
    )
    client = TheAudioDBClient()
    results = await client.search(artist_name)
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_fetch_album_thumb_expected_flow(tmp_path: Path) -> None:
    """Fetches and saves album thumbnail for a known album by TheAudioDB ID."""
    album_id = "211024"
    album_name = "Discovery"
    api_url = "https://theaudiodb.com/api/v1/json/2/album.php"
    respx.get(api_url, params={"m": album_id}).mock(
        return_value=httpx.Response(
            200,
            json={
                "album": [
                    {
                        "idAlbum": album_id,
                        "strAlbum": album_name,
                        "strAlbumThumb": "https://www.theaudiodb.com/images/media/album/thumb/discovery.jpg",
                    }
                ]
            },
        )
    )
    # Mock image download
    respx.get("https://www.theaudiodb.com/images/media/album/thumb/discovery.jpg").mock(
        return_value=httpx.Response(200, content=b"FAKEALBUMIMG")
    )
    # Call the function
    artwork_dir = tmp_path / ".namegnome" / "artwork" / album_id
    result = await fetch_album_thumb(album_id, artwork_dir)
    # Assert file exists and is correct
    thumb_path = artwork_dir / "thumb.jpg"
    assert thumb_path.exists()
    assert thumb_path.read_bytes() == b"FAKEALBUMIMG"
    # Assert returned ArtworkImage is correct
    assert isinstance(result, ArtworkImage)
    assert (
        str(result.url)
        == "https://www.theaudiodb.com/images/media/album/thumb/discovery.jpg"
    )
    assert result.type == "thumb"
    assert result.provider == "theaudiodb"


@pytest.mark.asyncio
async def test_search_artist_404(respx_mock: respx.MockRouter) -> None:
    """TheAudioDBClient returns empty list if API returns 404."""
    artist_name = "404 Artist"
    api_url = "https://theaudiodb.com/api/v1/json/2/search.php"
    respx_mock.get(api_url, params={"s": artist_name}).mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    client = TheAudioDBClient()
    results = await client.search(artist_name)
    assert results == []


@pytest.mark.asyncio
async def test_search_artist_429(respx_mock: respx.MockRouter) -> None:
    """TheAudioDBClient.search raises on 429 rate-limit error."""
    artist_name = "RateLimit Artist"
    api_url = "https://theaudiodb.com/api/v1/json/2/search.php"
    respx_mock.get(api_url, params={"s": artist_name}).mock(
        return_value=httpx.Response(429, json={"error": "Too Many Requests"})
    )
    client = TheAudioDBClient()
    with pytest.raises(Exception):
        await client.search(artist_name)
