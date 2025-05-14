"""Tests for the Fanart.tv client (fetch_fanart_poster)."""

from pathlib import Path

import httpx
import pytest
import respx

from namegnome.metadata.clients.fanarttv import fetch_fanart_poster
from namegnome.metadata.models import ArtworkImage, MediaMetadata, MediaMetadataType


@pytest.mark.asyncio
@respx.mock
async def test_fetch_fanart_poster_expected_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected-flow: fetches and caches highest-res poster for a movie by TMDB ID."""
    monkeypatch.setenv("FANARTTV_API_KEY", "dummykey")
    monkeypatch.setenv("TMDB_API_KEY", "dummytmdbkey")
    tmdbid = "12345"
    api_url = f"https://webservice.fanart.tv/v3/movies/{tmdbid}"
    # Mock Fanart.tv API response with two poster images
    respx.get(api_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "movieposter": [
                    {"url": "http://img1.jpg", "width": 500, "height": 750},
                    {"url": "http://img2.jpg", "width": 1000, "height": 1500},
                ]
            },
        )
    )
    # Mock image download
    respx.get("http://img2.jpg").mock(
        return_value=httpx.Response(200, content=b"FAKEIMAGE")
    )
    # Call the function
    meta = MediaMetadata(
        title="Test Movie",
        media_type=MediaMetadataType.MOVIE,
        provider="tmdb",
        provider_id=tmdbid,
    )
    artwork_dir = tmp_path / ".namegnome" / "artwork" / tmdbid
    result = await fetch_fanart_poster(meta, artwork_dir)
    # Assert poster file exists and is correct
    poster_path = artwork_dir / "poster.jpg"
    assert poster_path.exists()
    assert poster_path.read_bytes() == b"FAKEIMAGE"
    # Assert returned ArtworkImage is correct
    assert isinstance(result, ArtworkImage)
    assert str(result.url) == "http://img2.jpg/"
    assert result.width == 1000
    assert result.height == 1500
    assert result.type == "poster"
    assert result.provider == "fanart"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_fanart_poster_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """404: Fanart.tv returns not found; should return None."""
    monkeypatch.setenv("FANARTTV_API_KEY", "dummykey")
    monkeypatch.setenv("TMDB_API_KEY", "dummytmdbkey")
    tmdbid = "404"
    api_url = f"https://webservice.fanart.tv/v3/movies/{tmdbid}"
    respx.get(api_url).mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    meta = MediaMetadata(
        title="Missing Movie",
        media_type=MediaMetadataType.MOVIE,
        provider="tmdb",
        provider_id=tmdbid,
    )
    artwork_dir = tmp_path / ".namegnome" / "artwork" / tmdbid
    result = await fetch_fanart_poster(meta, artwork_dir)
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_fanart_poster_429(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """429: Fanart.tv rate-limit error; should raise exception."""
    monkeypatch.setenv("FANARTTV_API_KEY", "dummykey")
    monkeypatch.setenv("TMDB_API_KEY", "dummytmdbkey")
    tmdbid = "ratelimit"
    api_url = f"https://webservice.fanart.tv/v3/movies/{tmdbid}"
    respx.get(api_url).mock(
        return_value=httpx.Response(429, json={"error": "Too Many Requests"})
    )
    meta = MediaMetadata(
        title="Rate Limited Movie",
        media_type=MediaMetadataType.MOVIE,
        provider="tmdb",
        provider_id=tmdbid,
    )
    artwork_dir = tmp_path / ".namegnome" / "artwork" / tmdbid
    with pytest.raises(Exception):
        await fetch_fanart_poster(meta, artwork_dir)
