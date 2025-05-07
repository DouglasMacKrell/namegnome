"""Tests for the TMDB metadata client."""

from pathlib import Path
from typing import cast

import pytest
from namegnome.metadata import get_metadata_client
from namegnome.metadata.clients.tmdb import StubTMDBClient
from namegnome.metadata.models import MediaMetadataType


class TestStubTMDBClient:
    """Tests for the StubTMDBClient."""

    @pytest.fixture
    def client(self) -> StubTMDBClient:
        """Create a StubTMDBClient for testing."""
        return cast(StubTMDBClient, get_metadata_client("tmdb"))

    @pytest.fixture
    def ensure_fixture_dir(self) -> None:
        """Ensure the fixture directory exists."""
        fixture_dir = Path(__file__).parents[2] / "fixtures" / "stubs" / "tmdb"
        fixture_dir.mkdir(parents=True, exist_ok=True)

    @pytest.mark.asyncio
    async def test_search_movie_no_fixture(self, client: StubTMDBClient) -> None:
        """Test searching for a movie when the fixture doesn't exist."""
        # If the fixture doesn't exist, we should get an empty list
        results = await client.search_movie("Nonexistent Movie")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_movie_details(
        self, client: StubTMDBClient, ensure_fixture_dir: None
    ) -> None:
        """Test getting movie details."""
        # This should use the generic fixture we created
        try:
            movie_data = await client.get_movie_details("550")
            assert movie_data["title"] == "Fight Club"
            assert movie_data["id"] == 550
            assert movie_data["release_date"] == "1999-10-15"
        except FileNotFoundError:
            pytest.skip("Fixture file not found")

    def test_map_to_media_metadata_movie(
        self, client: StubTMDBClient, ensure_fixture_dir: None
    ) -> None:
        """Test mapping TMDB movie data to MediaMetadata."""
        # Use the generic fixture data
        fixture_path = (
            Path(__file__).parents[2]
            / "fixtures"
            / "stubs"
            / "tmdb"
            / "movie_details.json"
        )

        # Skip if fixture doesn't exist (CI/pipeline)
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        # Get raw movie data
        import json

        with open(fixture_path, encoding="utf-8") as f:
            movie_data = json.load(f)

        # Map to MediaMetadata
        metadata = client.map_to_media_metadata(movie_data, MediaMetadataType.MOVIE)

        # Verify mapping
        assert metadata.title == "Fight Club"
        assert metadata.media_type == MediaMetadataType.MOVIE
        assert metadata.provider == "tmdb"
        assert metadata.provider_id == "550"
        assert metadata.external_ids.tmdb_id == "550"
        assert metadata.external_ids.imdb_id == "tt0137523"
        assert metadata.year == 1999
        assert metadata.vote_average == 8.433
        assert metadata.runtime == 139
        assert "Drama" in metadata.genres

    def test_map_to_media_metadata_tv_show(self, client: StubTMDBClient) -> None:
        """Test mapping TMDB TV show data to MediaMetadata."""
        # Create a minimal TV show data structure
        tv_data = {
            "id": 1396,
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "first_air_date": "2008-01-20",
            "overview": (
                "A high school chemistry teacher diagnosed with inoperable lung cancer"
                " turns to manufacturing and selling methamphetamine in order to secure"
                " his family's future."
            ),
            "vote_average": 8.8,
            "vote_count": 12345,
            "poster_path": "/mY9Mni5b6KENYLs5uYmz8QsVwPq.jpg",
            "backdrop_path": "/hbgJAeSZVUvViyO7l5Pst3RgBnL.jpg",
            "number_of_seasons": 5,
            "number_of_episodes": 62,
            "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
            "seasons": [
                {"season_number": 1},
                {"season_number": 2},
                {"season_number": 3},
                {"season_number": 4},
                {"season_number": 5},
                {"season_number": 0},  # Specials
            ],
            "episode_run_time": [45, 47],
        }

        # Map to MediaMetadata
        metadata = client.map_to_media_metadata(tv_data, MediaMetadataType.TV_SHOW)

        # Verify mapping
        assert metadata.title == "Breaking Bad"
        assert metadata.media_type == MediaMetadataType.TV_SHOW
        assert metadata.provider == "tmdb"
        assert metadata.provider_id == "1396"
        assert metadata.external_ids.tmdb_id == "1396"
        assert metadata.year == 2008
        assert metadata.vote_average == 8.8
        assert metadata.number_of_seasons == 5
        assert metadata.number_of_episodes == 62
        assert len(metadata.seasons) == 5  # Should not include season 0 (specials)
        assert "Drama" in metadata.genres
        assert "Crime" in metadata.genres
