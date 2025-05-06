"""Metadata API client implementations and models.

This package provides a standard interface for accessing various
metadata providers like TMDB, TVDB, MusicBrainz, etc.
"""

from typing import Any

from namegnome.metadata.clients.base import MetadataClient
from namegnome.metadata.clients.tmdb import StubTMDBClient
from namegnome.metadata.clients.tvdb import StubTVDBClient
from namegnome.metadata.models import (
    ArtworkImage,
    ExternalIDs,
    MediaMetadata,
    MediaMetadataType,
    PersonInfo,
    TVEpisode,
)

__all__ = [
    "get_metadata_client",
    "list_available_clients",
    "register_client",
    "MediaMetadata",
    "MediaMetadataType",
    "ExternalIDs",
    "ArtworkImage",
    "PersonInfo",
    "TVEpisode",
]

# Registry of metadata client implementations
_CLIENT_REGISTRY: dict[str, type[MetadataClient]] = {}


def register_client(name: str, client_class: type[MetadataClient]) -> None:
    """Register a metadata client implementation.

    Args:
        name: The name of the client (e.g., 'tmdb', 'tvdb').
        client_class: The class that implements the MetadataClient interface.
    """
    _CLIENT_REGISTRY[name.lower()] = client_class


def get_metadata_client(name: str, **kwargs: Any) -> MetadataClient | None:
    """Get a metadata client by name.

    Args:
        name: The name of the metadata provider (e.g., 'tmdb', 'tvdb').
        **kwargs: Additional arguments to pass to the client constructor.

    Returns:
        An instance of the requested metadata client, or None if not found.
    """
    client_class = _CLIENT_REGISTRY.get(name.lower())
    if client_class:
        return client_class(**kwargs)
    return None


def list_available_clients() -> list[str]:
    """Get a list of registered metadata client names.

    Returns:
        A list of available client names.
    """
    return list(_CLIENT_REGISTRY.keys())


# Register the stub clients
register_client("tmdb", StubTMDBClient)
register_client("tvdb", StubTVDBClient)
