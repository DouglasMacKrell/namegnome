"""Tests for the TVDB metadata client."""

from pathlib import Path
from typing import cast

import pytest

from namegnome.metadata import get_metadata_client
from namegnome.metadata.clients.tvdb import StubTVDBClient
from namegnome.metadata.models import MediaMetadataType


class TestStubTVDBClient:
    """Tests for the StubTVDBClient."""

    @pytest.fixture
    def client(self) -> StubTVDBClient:
        """Create a StubTVDBClient for testing."""
        return cast(StubTVDBClient, get_metadata_client("tvdb"))

    @pytest.fixture
    def ensure_fixture_dir(self) -> None:
        """Ensure the fixture directory exists."""
        fixture_dir = Path(__file__).parents[2] / "fixtures" / "stubs" / "tvdb"
        fixture_dir.mkdir(parents=True, exist_ok=True)

    @pytest.mark.asyncio
    async def test_search_movie_empty(self, client: StubTVDBClient) -> None:
        """Test searching for a movie returns empty list (TV-focused client)."""
        results = await client.search_movie("Any Movie")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_tv_no_fixture(self, client: StubTVDBClient) -> None:
        """Test searching for a TV show when fixture doesn't exist."""
        results = await client.search_tv("Nonexistent Show")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_tv_details(
        self, client: StubTVDBClient, ensure_fixture_dir: None
    ) -> None:
        """Test getting TV show details."""
        # This should use the generic fixture we created
        try:
            show_data = await client.get_tv_details("81189")
            assert show_data["data"]["name"] == "Breaking Bad"
            assert show_data["data"]["id"] == 81189
            assert show_data["data"]["firstAired"] == "2008-01-20"
        except FileNotFoundError:
            pytest.skip("Fixture file not found")

    def test_map_to_media_metadata_tv_show(
        self, client: StubTVDBClient, ensure_fixture_dir: None
    ) -> None:
        """Test mapping TVDB TV show data to MediaMetadata."""
        # Use the generic fixture data
        fixture_path = (
            Path(__file__).parents[2]
            / "fixtures"
            / "stubs"
            / "tvdb"
            / "tv_details.json"
        )

        # Skip if fixture doesn't exist (CI/pipeline)
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        # Get raw TV show data
        import json

        with open(fixture_path, encoding="utf-8") as f:
            tv_data = json.load(f)["data"]

        # Map to MediaMetadata
        metadata = client.map_to_media_metadata(tv_data, MediaMetadataType.TV_SHOW)

        # Verify mapping
        assert metadata.title == "Breaking Bad"
        assert metadata.media_type == MediaMetadataType.TV_SHOW
        assert metadata.provider == "tvdb"
        assert metadata.provider_id == "81189"
        assert metadata.external_ids.tvdb_id == "81189"
        assert metadata.external_ids.imdb_id == "tt0903747"
        assert metadata.year == 2008
        assert metadata.number_of_seasons == 5  # Should not include season 0 (specials)
        assert "Drama" in metadata.genres
        assert "Crime" in metadata.genres
        assert "Thriller" in metadata.genres

    def test_map_to_media_metadata_tv_episode(self, client: StubTVDBClient) -> None:
        """Test mapping TVDB TV episode data to MediaMetadata."""
        # Create a minimal TV episode data structure
        episode_data = {
            "id": 12345,
            "name": "Pilot",
            "overview": (
                "High school chemistry teacher Walter White's life is suddenly"
                " transformed by a dire medical diagnosis."
            ),
            "number": 1,
            "seasonNumber": 1,
            "aired": "2008-01-20",
            "runtime": 58,
            "absoluteNumber": 1,
            "series": {"name": "Breaking Bad"},
        }

        # Map to MediaMetadata
        metadata = client.map_to_media_metadata(
            episode_data, MediaMetadataType.TV_EPISODE
        )

        # Verify mapping
        assert metadata.title == "Breaking Bad - Pilot"
        assert metadata.media_type == MediaMetadataType.TV_EPISODE
        assert metadata.provider == "tvdb"
        assert metadata.provider_id == "12345"
        assert metadata.season_number == 1
        assert metadata.episode_number == 1
        assert len(metadata.episodes) == 1

        # Check episode details
        episode = metadata.episodes[0]
        assert episode.title == "Pilot"
        assert episode.season_number == 1
        assert episode.episode_number == 1
        assert episode.absolute_number == 1
        assert episode.runtime == 58
