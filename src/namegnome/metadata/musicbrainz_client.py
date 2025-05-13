"""MusicBrainz metadata client for album/track lookup.

Implements async search_album for fetching album metadata by title and artist.
Maps MusicBrainz API response to MediaMetadata model.
"""

import asyncio
import time
from typing import Optional

import httpx

from namegnome.metadata.models import MediaMetadata, MediaMetadataType


class NotFoundError(Exception):
    """Raised when the requested album is not found in MusicBrainz."""

    pass


class RateLimitError(Exception):
    """Raised when MusicBrainz rate limit is exceeded."""

    pass


HTTP_STATUS_RATE_LIMITED = 503  # Magic number for rate limit response


class MusicBrainzClient:
    """Async client for MusicBrainz album/track metadata lookup.

    - Enforces 1 request/sec rate limit (per instance)
    - Sets a custom User-Agent header for all requests (per MusicBrainz API policy)
    """

    BASE_URL = "https://musicbrainz.org/ws/2/release/"
    DEFAULT_USER_AGENT = "namegnome/0.1.0 (https://github.com/yourrepo)"

    def __init__(self, user_agent: Optional[str] = None) -> None:
        """Initialize the MusicBrainzClient with optional custom User-Agent."""
        self._user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._rate_lock = asyncio.Lock()
        self._last_request = 0.0

    async def _rate_limit(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
            self._last_request = time.monotonic()

    async def search_album(self, album_title: str, artist_name: str) -> MediaMetadata:
        """Fetch album metadata from MusicBrainz by album and artist name.

        Args:
            album_title: The album title to search for.
            artist_name: The artist name to search for.

        Returns:
            MediaMetadata: Normalized album metadata.

        Raises:
            NotFoundError: If no album is found.
            RateLimitError: If rate limited by MusicBrainz.
        """
        await self._rate_limit()
        params = {
            "query": f"release:{album_title} AND artist:{artist_name}",
            "fmt": "json",
        }
        headers = {"User-Agent": self._user_agent}
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(self.BASE_URL, params=params)
            if resp.status_code == HTTP_STATUS_RATE_LIMITED:
                raise RateLimitError("MusicBrainz rate limit exceeded.")
            data = resp.json()
            releases = data.get("releases", [])
            if not releases:
                raise NotFoundError(
                    f"Album '{album_title}' by '{artist_name}' not found."
                )
            release = releases[0]
            year = None
            if "date" in release:
                try:
                    year = int(release["date"].split("-")[0])
                except Exception:
                    year = None
            artists = [ac["name"] for ac in release.get("artist-credit", [])]
            return MediaMetadata(
                title=release["title"],
                media_type=MediaMetadataType.MUSIC_ALBUM,
                provider="musicbrainz",
                provider_id=release["id"],
                year=year,
                release_date=None,
                artists=artists,
                extra={},
            )
