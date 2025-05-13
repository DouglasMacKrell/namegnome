"""TVDB metadata provider client.

Implements the MetadataClient interface for TheTVDB API.
"""

import os
from http import HTTPStatus

import httpx

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.models import (
    ExternalIDs,
    MediaMetadata,
    MediaMetadataType,
    TVEpisode,
)


class TVDBClient(MetadataClient):
    """Async client for TheTVDB API."""

    BASE_URL = "https://api.thetvdb.com"

    async def search(self, title: str, year: int | None = None) -> list[MediaMetadata]:
        """Search for TV series by title and return MediaMetadata with episodes.

        Args:
            title: The series title to search for.
            year: Optional year (unused in this minimal implementation).

        Returns:
            List of MediaMetadata objects for matching series.
        """
        api_key = os.environ["TVDB_API_KEY"]
        async with httpx.AsyncClient() as client:
            # Authenticate
            login_resp = await client.post(
                f"{self.BASE_URL}/login", json={"apikey": api_key}
            )
            token = login_resp.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            # Search series
            series_resp = await client.get(
                f"{self.BASE_URL}/search/series",
                params={"name": title},
                headers=headers,
            )
            series_data = series_resp.json()["data"]
            results = []
            for series in series_data:
                series_id = str(series["id"])
                episodes = []
                page = 1
                while True:
                    ep_resp = await client.get(
                        f"{self.BASE_URL}/series/{series_id}/episodes",
                        params={"page": page},
                        headers=headers,
                    )
                    if ep_resp.status_code == HTTPStatus.UNAUTHORIZED:
                        # Token expired, retry login once
                        login_resp2 = await client.post(
                            f"{self.BASE_URL}/login", json={"apikey": api_key}
                        )
                        token2 = login_resp2.json()["token"]
                        headers2 = {"Authorization": f"Bearer {token2}"}
                        ep_resp = await client.get(
                            f"{self.BASE_URL}/series/{series_id}/episodes",
                            params={"page": page},
                            headers=headers2,
                        )
                        # Use new token for subsequent requests
                        headers = headers2
                    ep_json = ep_resp.json()
                    for ep in ep_json["data"]:
                        episodes.append(
                            TVEpisode(
                                title=ep["episodeName"],
                                episode_number=ep["airedEpisodeNumber"],
                                season_number=ep["airedSeason"],
                                air_date=None,
                                overview=ep.get("overview"),
                            )
                        )
                    if not ep_json["links"].get("next"):
                        break
                    page = ep_json["links"]["next"]
                meta = MediaMetadata(
                    title=series["seriesName"],
                    media_type=MediaMetadataType.TV_SHOW,
                    original_title=None,
                    overview=series.get("overview"),
                    provider="tvdb",
                    provider_id=series_id,
                    external_ids=ExternalIDs(tvdb_id=series_id),
                    release_date=None,
                    year=int(series["firstAired"].split("-")[0])
                    if series.get("firstAired")
                    else None,
                    artwork=[],
                    runtime=None,
                    genres=[],
                    production_companies=[],
                    cast=[],
                    crew=[],
                    number_of_seasons=None,
                    number_of_episodes=None,
                    seasons=[],
                    episodes=episodes,
                    episode_run_time=None,
                    season_number=None,
                    episode_number=None,
                    artists=[],
                    album=None,
                    track_number=None,
                    disc_number=None,
                    duration_ms=None,
                    extra={},
                )
                results.append(meta)
            return results

    async def details(self, provider_id: str) -> MediaMetadata:
        """Fetch full metadata details for a given provider-specific ID.

        Args:
            provider_id: The unique ID in the provider's system.

        Returns:
            A MediaMetadata object with full details.
        """
        api_key = os.environ["TVDB_API_KEY"]
        async with httpx.AsyncClient() as client:
            # Authenticate
            login_resp = await client.post(
                f"{self.BASE_URL}/login", json={"apikey": api_key}
            )
            token = login_resp.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            # Fetch series details
            details_resp = await client.get(
                f"{self.BASE_URL}/series/{provider_id}", headers=headers
            )
            series = details_resp.json()["data"]
            # Fetch episodes (first page)
            episodes = []
            page = 1
            while True:
                ep_resp = await client.get(
                    f"{self.BASE_URL}/series/{provider_id}/episodes",
                    params={"page": page},
                    headers=headers,
                )
                ep_json = ep_resp.json()
                for ep in ep_json["data"]:
                    episodes.append(
                        TVEpisode(
                            title=ep["episodeName"],
                            episode_number=ep["airedEpisodeNumber"],
                            season_number=ep["airedSeason"],
                            air_date=None,
                            overview=ep.get("overview"),
                        )
                    )
                if not ep_json["links"].get("next"):
                    break
                page = ep_json["links"]["next"]
            meta = MediaMetadata(
                title=series["seriesName"],
                media_type=MediaMetadataType.TV_SHOW,
                original_title=None,
                overview=series.get("overview"),
                provider="tvdb",
                provider_id=str(series["id"]),
                external_ids=ExternalIDs(tvdb_id=str(series["id"])),
                release_date=None,
                year=int(series["firstAired"].split("-")[0])
                if series.get("firstAired")
                else None,
                artwork=[],
                runtime=None,
                genres=[],
                production_companies=[],
                cast=[],
                crew=[],
                number_of_seasons=None,
                number_of_episodes=None,
                seasons=[],
                episodes=episodes,
                episode_run_time=None,
                season_number=None,
                episode_number=None,
                artists=[],
                album=None,
                track_number=None,
                disc_number=None,
                duration_ms=None,
                extra={},
            )
            return meta
