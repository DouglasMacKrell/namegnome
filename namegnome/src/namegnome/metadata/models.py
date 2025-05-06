"""Data models for media metadata."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class MediaMetadataType(str, Enum):
    """Types of media supported by the metadata API."""

    MOVIE = "movie"
    TV_SHOW = "tv_show"
    TV_SEASON = "tv_season"
    TV_EPISODE = "tv_episode"
    MUSIC_ARTIST = "music_artist"
    MUSIC_ALBUM = "music_album"
    MUSIC_TRACK = "music_track"


class ExternalIDs(BaseModel):
    """External IDs for a media item across different services."""

    imdb_id: str | None = None
    tmdb_id: str | None = None
    tvdb_id: str | None = None
    musicbrainz_id: str | None = None
    theaudiodb_id: str | None = None


class ArtworkImage(BaseModel):
    """Represents artwork for a media item."""

    url: HttpUrl
    aspect_ratio: float | None = None
    width: int | None = None
    height: int | None = None
    type: str = "poster"  # poster, backdrop, logo, etc.
    provider: str  # The source of this image (tmdb, tvdb, fanart, etc.)


class PersonInfo(BaseModel):
    """Information about a person involved in a media item."""

    name: str
    id: str | None = None
    role: str | None = None  # actor, director, etc.
    character: str | None = None
    order: int | None = None
    profile_url: HttpUrl | None = None


class TVEpisode(BaseModel):
    """Information about a TV episode."""

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

    This converts provider-specific metadata into a standardized format
    that can be used throughout the application regardless of the source.
    """

    # Common fields for all media types
    title: str
    media_type: MediaMetadataType
    original_title: str | None = None
    overview: str | None = None
    provider: str  # The source of this metadata (tmdb, tvdb, etc.)
    provider_id: str  # The ID in the provider's system

    # IDs in external systems
    external_ids: ExternalIDs = Field(default_factory=ExternalIDs)

    # Release info
    release_date: date | None = None
    year: int | None = None

    # Ratings & popularity
    vote_average: float | None = None  # 0-10 scale
    vote_count: int | None = None
    popularity: float | None = None

    # Images
    artwork: list[ArtworkImage] = Field(default_factory=list)

    # Movie & TV show specific
    runtime: int | None = None  # minutes
    genres: list[str] = Field(default_factory=list)
    production_companies: list[str] = Field(default_factory=list)

    # People
    cast: list[PersonInfo] = Field(default_factory=list)
    crew: list[PersonInfo] = Field(default_factory=list)

    # TV specific
    number_of_seasons: int | None = None
    number_of_episodes: int | None = None
    seasons: list[int] = Field(default_factory=list)
    episodes: list[TVEpisode] = Field(default_factory=list)
    episode_run_time: int | None = None  # average runtime in minutes

    # TV season specific
    season_number: int | None = None

    # TV episode specific
    episode_number: int | None = None

    # Music specific
    artists: list[str] = Field(default_factory=list)
    album: str | None = None
    track_number: int | None = None
    disc_number: int | None = None
    duration_ms: int | None = None  # milliseconds

    # Additional provider-specific data
    extra: dict[str, Any] = Field(default_factory=dict)
