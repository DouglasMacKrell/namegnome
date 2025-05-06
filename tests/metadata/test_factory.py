"""Tests for the metadata factory and registry."""

from typing import Any

from namegnome.metadata import (
    get_metadata_client,
    list_available_clients,
    register_client,
)
from namegnome.metadata.clients import MetadataClient, StubTMDBClient, StubTVDBClient


class TestMetadataFactory:
    """Tests for the metadata client factory and registry."""

    def test_list_available_clients(self) -> None:
        """Test that we can list available clients."""
        clients = list_available_clients()
        assert "tmdb" in clients
        assert "tvdb" in clients

    def test_get_metadata_client_tmdb(self) -> None:
        """Test getting a TMDB client."""
        client = get_metadata_client("tmdb")
        assert client is not None
        assert isinstance(client, StubTMDBClient)
        assert client.provider_name == "tmdb"

    def test_get_metadata_client_tvdb(self) -> None:
        """Test getting a TVDB client."""
        client = get_metadata_client("tvdb")
        assert client is not None
        assert isinstance(client, StubTVDBClient)
        assert client.provider_name == "tvdb"

    def test_get_nonexistent_client(self) -> None:
        """Test getting a client that doesn't exist."""
        client = get_metadata_client("nonexistent")
        assert client is None

    def test_register_new_client(self) -> None:
        """Test registering a new client type."""

        # Create a mock client class
        class MockClient(MetadataClient):
            @property
            def provider_name(self) -> str:
                return "mock"

            async def search_movie(
                self, title: str, year: int | None = None
            ) -> list[dict[str, Any]]:
                return []

            async def search_tv(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
                return []

            async def get_movie_details(self, movie_id: str) -> dict[str, Any]:
                return {}

            async def get_tv_details(self, show_id: str) -> dict[str, Any]:
                return {}

            async def get_tv_season(self, show_id: str, season_number: int) -> dict[str, Any]:
                return {}

            async def get_tv_episode(
                self, show_id: str, season_number: int, episode_number: int
            ) -> dict[str, Any]:
                return {}

        # Register the mock client
        register_client("mock", MockClient)

        # Verify it's in the registry
        clients = list_available_clients()
        assert "mock" in clients

        # Get an instance
        client = get_metadata_client("mock")
        assert client is not None
        assert isinstance(client, MockClient)
        assert client.provider_name == "mock"
