"""Data models for media metadata.

This module defines unified, provider-agnostic data models for all supported media
types (movies, TV, music).
- Used to normalize metadata from multiple providers (TMDb, TVDb, MusicBrainz,
  etc.) into a single schema.
- Enables consistent access to metadata fields regardless of source, simplifying
  downstream logic.
- Designed for extensibility and cross-provider compatibility (see PLANNING.md,
  README.md, and provider integration docs).

Design:
- MediaMetadataType enum covers all supported media object types for flexible API
  integration.
- MediaMetadata is the central model, with fields for all common and provider-specific
  data.
- Extra fields and dicts allow for future provider expansion without breaking schema.
"""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class MediaMetadataType(str, Enum):
    """Types of media supported by the metadata API.

    Used to distinguish between movies, TV shows, seasons, episodes, music artists,
    albums, and tracks. Enables flexible normalization and downstream logic.
    """

    MOVIE = "movie"
    TV_SHOW = "tv_show"
    TV_SEASON = "tv_season"
    TV_EPISODE = "tv_episode"
    MUSIC_ARTIST = "music_artist"
    MUSIC_ALBUM = "music_album"
    MUSIC_TRACK = "music_track"


class ExternalIDs(BaseModel):
    """External IDs for a media item across different services.

    Stores unique identifiers for the same media item in various provider systems
    (e.g., TMDb, IMDb, MusicBrainz). Used for cross-referencing and enrichment.
    """

    imdb_id: str | None = None
    tmdb_id: str | None = None
    tvdb_id: str | None = None
    musicbrainz_id: str | None = None
    theaudiodb_id: str | None = None


class ArtworkImage(BaseModel):
    """Represents artwork for a media item.

    Used to store URLs and metadata for posters, backdrops, logos, etc., from any
    provider.
    """

    url: HttpUrl
    aspect_ratio: float | None = None
    width: int | None = None
    height: int | None = None
    type: str = "poster"  # poster, backdrop, logo, etc.
    provider: str  # The source of this image (tmdb, tvdb, fanart, etc.)


class PersonInfo(BaseModel):
    """Information about a person involved in a media item.

    Used for cast, crew, and artist credits, with optional role and character fields.
    """

    name: str
    id: str | None = None
    role: str | None = None  # actor, director, etc.
    character: str | None = None
    order: int | None = None
    profile_url: HttpUrl | None = None


class TVEpisode(BaseModel):
    """Information about a TV episode.

    Used to represent a single episode, including absolute and season/episode numbers,
    for normalization across providers.
    """

    title: str
    episode_number: int
    season_number: int
    absolute_number: int | None = None
    air_date: date | None = None
    overview: str | None = None
    runtime: int | None = None  # minutes
    still_url: HttpUrl | None = None
    external_ids: ExternalIDs | None = None


class MediaMetadata(BaseModel):
    """Unified metadata model for all media types.

    Converts provider-specific metadata into a standardized format that can be used
    throughout the application regardless of the source. All fields are optional except
    for title, media_type, provider, and provider_id. Extra fields and dicts allow for
    future provider expansion without breaking schema.
    """

    # Common fields for all media types
    title: str
    """Canonical title of the media item (from provider or best guess)."""
    media_type: MediaMetadataType
    """Type of media (movie, tv_show, music_album, etc.)."""
    original_title: str | None = None
    """Original title in provider's language, if different from canonical title."""
    overview: str | None = None
    """Short summary or description of the media item."""
    provider: str
    """The source of this metadata (e.g., 'tmdb', 'tvdb', 'musicbrainz')."""
    provider_id: str
    """The ID of this item in the provider's system (for lookups and debugging)."""

    # IDs in external systems
    external_ids: ExternalIDs = Field(default_factory=ExternalIDs)
    """IDs in external systems (for cross-referencing and enrichment)."""

    # Release info
    release_date: date | None = None
    """Release date (YYYY-MM-DD) if available."""
    year: int | None = None
    """Release year (for sorting and display)."""

    # Ratings & popularity
    vote_average: float | None = None  # 0-10 scale
    """Average user or critic rating (0-10 scale, provider-specific)."""
    vote_count: int | None = None
    """Number of votes or ratings (provider-specific)."""
    popularity: float | None = None
    """Popularity score (provider-specific, may be missing or arbitrary scale)."""

    # Images
    artwork: list[ArtworkImage] = Field(default_factory=list)
    """List of artwork images (posters, backdrops, etc.) from all providers."""

    # Movie & TV show specific
    runtime: int | None = None  # minutes
    """Runtime in minutes (for movies, episodes, or tracks)."""
    genres: list[str] = Field(default_factory=list)
    """List of genres (provider-specific, normalized where possible)."""
    production_companies: list[str] = Field(default_factory=list)
    """List of production companies or labels (provider-specific)."""

    # People
    cast: list[PersonInfo] = Field(default_factory=list)
    """List of cast members (actors, artists, etc.)."""
    crew: list[PersonInfo] = Field(default_factory=list)
    """List of crew members (directors, producers, etc.)."""

    # TV specific
    number_of_seasons: int | None = None
    """Number of seasons (for TV shows, if available)."""
    number_of_episodes: int | None = None
    """Number of episodes (for TV shows, if available)."""
    seasons: list[int] = Field(default_factory=list)
    """List of season numbers (for TV shows, if available)."""
    episodes: list[TVEpisode] = Field(default_factory=list)
    """List of TVEpisode objects (for TV shows, if available)."""
    episode_run_time: int | None = None  # average runtime in minutes
    """Average episode runtime in minutes (for TV shows, if available)."""

    # TV season specific
    season_number: int | None = None
    """Season number (for TV seasons or episodes, if available)."""

    # TV episode specific
    episode_number: int | None = None
    """Episode number (for TV episodes, if available)."""

    # Music specific
    artists: list[str] = Field(default_factory=list)
    """List of artist names (for music albums/tracks, if available)."""
    album: str | None = None
    """Album name (for music tracks, if available)."""
    track_number: int | None = None
    """Track number (for music tracks, if available)."""
    disc_number: int | None = None
    """Disc number (for multi-disc albums, if available)."""
    duration_ms: int | None = None  # milliseconds
    """Duration in milliseconds (for music tracks, if available)."""

    # Additional provider-specific data
    extra: dict[str, Any] = Field(default_factory=dict)
    """Additional provider-specific data (for extensibility and debugging)."""
