"""TheAudioDB metadata client for artist/album lookup.

Implements async search for fetching artist metadata by name.
"""

from pathlib import Path

import httpx

from namegnome.metadata.base import MetadataClient
from namegnome.metadata.models import ArtworkImage, MediaMetadata, MediaMetadataType


class TheAudioDBClient(MetadataClient):
    """Async client for TheAudioDB artist and album metadata/artwork lookup."""

    BASE_URL = "https://theaudiodb.com/api/v1/json/2/search.php"

    async def search(self, title: str, year: int | None = None) -> list[MediaMetadata]:
        """Search for artists by name using TheAudioDB API.

        Args:
            title: The artist name to search for.
            year: Optional year (ignored by TheAudioDB).

        Returns:
            List of MediaMetadata objects for matching artists.
        """
        params = {"s": title}
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.BASE_URL, params=params)
            data = resp.json()
            artists = data.get("artists")
            if not artists:
                return []
            artist = artists[0]
            artwork = []
            if artist.get("strArtistThumb"):
                artwork.append(
                    ArtworkImage(
                        url=artist["strArtistThumb"],
                        provider="theaudiodb",
                        type="thumb",
                    )
                )
            genres = []
            if artist.get("strGenre"):
                genres = [artist["strGenre"]]
            return [
                MediaMetadata(
                    title=artist["strArtist"],
                    media_type=MediaMetadataType.MUSIC_ARTIST,
                    provider="theaudiodb",
                    provider_id=artist["idArtist"],
                    genres=genres,
                    artwork=artwork,
                    overview=artist.get("strBiographyEN"),
                )
            ]

    async def details(self, provider_id: str) -> None:
        """Fetch full metadata details for a given provider-specific ID.

        Not implemented for TheAudioDBClient.
        """
        raise NotImplementedError


async def fetch_album_thumb(album_id: str, artwork_dir: Path) -> ArtworkImage:
    """Download and save album thumb by TheAudioDB ID, returning an ArtworkImage.

    Fetch album info by ID, download album thumb, save as thumb.jpg, and return
    ArtworkImage.

    Args:
        album_id: TheAudioDB album ID.
        artwork_dir: Directory to save the downloaded thumbnail.

    Returns:
        ArtworkImage object for the downloaded album thumb.

    Raises:
        ValueError: If album or thumb is not found.
    """
    album_url = "https://theaudiodb.com/api/v1/json/2/album.php"
    params = {"m": album_id}
    async with httpx.AsyncClient() as client:
        resp = await client.get(album_url, params=params)
        data = resp.json()
        albums = data.get("album")
        if not albums:
            raise ValueError(f"No album found for id {album_id}")
        album = albums[0]
        thumb_url = album.get("strAlbumThumb")
        if not thumb_url:
            raise ValueError(f"No album thumb for id {album_id}")
        # Download image
        img_resp = await client.get(thumb_url)
        artwork_dir.mkdir(parents=True, exist_ok=True)
        thumb_path = artwork_dir / "thumb.jpg"
        thumb_path.write_bytes(img_resp.content)
        return ArtworkImage(
            url=thumb_url,
            provider="theaudiodb",
            type="thumb",
        )
