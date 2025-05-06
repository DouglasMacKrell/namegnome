"""Client implementations for various metadata providers."""

from namegnome.metadata.clients.base import MetadataClient
from namegnome.metadata.clients.tmdb import StubTMDBClient
from namegnome.metadata.clients.tvdb import StubTVDBClient

__all__ = ["MetadataClient", "StubTMDBClient", "StubTVDBClient"]
