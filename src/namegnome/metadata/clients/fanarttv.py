"""Fanart.tv client for fetching high-quality artwork for movies/TV.

Implements fetch_fanart_poster for Sprint 2.6. Loads API key from settings,
fetches poster list for TMDB ID, selects highest-res, downloads and saves as
poster.jpg, returns ArtworkImage. Never hard-codes API keys.
"""

import os
from http import HTTPStatus
from pathlib import Path
from typing import Optional

import httpx

from namegnome.metadata.models import ArtworkImage, MediaMetadata
from namegnome.metadata.settings import Settings


async def fetch_fanart_poster(
    meta: MediaMetadata, artwork_dir: Path
) -> Optional[ArtworkImage]:
    """Fetch and cache the highest-res poster from Fanart.tv for a movie by TMDB ID.

    Args:
        meta: MediaMetadata for the movie (must have provider_id as TMDB ID).
        artwork_dir: Directory to save the poster image.

    Returns:
        ArtworkImage for the highest-res poster, or None if not found (404).
    """
    # Initialize settings with required TMDB_API_KEY to satisfy mypy
    # This key isn't used by this function but is required by the Settings class
    settings = Settings(TMDB_API_KEY=os.environ.get("TMDB_API_KEY", ""))
    api_key = settings.FANARTTV_API_KEY
    tmdbid = meta.provider_id
    url = f"https://webservice.fanart.tv/v3/movies/{tmdbid}"
    async with httpx.AsyncClient() as client:
        headers = {"api-key": str(api_key) if api_key else ""}
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == HTTPStatus.NOT_FOUND:
                return None
            raise
        data = resp.json()
        posters = data.get("movieposter", [])
        if not posters:
            raise ValueError(f"No posters found for TMDB ID {tmdbid}")
        # Pick highest-res poster
        best = max(posters, key=lambda p: p.get("width", 0) * p.get("height", 0))
        img_url = best["url"]
        width = best["width"]
        height = best["height"]
        # Download image
        img_resp = await client.get(img_url)
        img_resp.raise_for_status()
        artwork_dir.mkdir(parents=True, exist_ok=True)
        poster_path = artwork_dir / "poster.jpg"
        poster_path.write_bytes(img_resp.content)
        return ArtworkImage(
            url=img_url,
            width=width,
            height=height,
            type="poster",
            provider="fanart",
        )
