"""OMDb client for supplementing TMDB metadata in NameGnome.

Fetches ratings and plot from OMDb and merges into MediaMetadata, as required
by Sprint 2.5. TMDB fields take priority over OMDb when both are present.
"""

from http import HTTPStatus

import httpx

from namegnome.metadata.models import MediaMetadata


async def fetch_and_merge_omdb(
    tmdb_metadata: MediaMetadata,
    api_key: str,
    title: str,
    year: int,
) -> MediaMetadata:
    """Fetch OMDb data and merge IMDb rating and plot into MediaMetadata.

    TMDB fields take priority over OMDb when both are present.
    """
    url = f"http://www.omdbapi.com/?apikey={api_key}&t={title}&y={year}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise Exception("OMDb rate limit exceeded")
        data = resp.json()
    merged = tmdb_metadata.copy()
    if merged.vote_average is None and data.get("imdbRating"):
        try:
            merged.vote_average = float(data["imdbRating"])
        except Exception:
            pass
    if merged.overview is None and data.get("Plot"):
        merged.overview = data["Plot"]
    return merged
