"""Tests for the TMDBClient metadata provider.

Covers expected, edge, and failure cases for movie and TV lookups.
"""

import pytest
import respx

from namegnome.metadata.clients.tmdb import TMDBClient
from namegnome.metadata.models import MediaMetadataType


@pytest.mark.asyncio
class TestTMDBClient:
    """Tests for TMDBClient covering expected, edge, and failure cases."""

    async def test_search_movie_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: search_movie returns correct MediaMetadata for a known movie title."""
        tmdb_response = {
            "results": [
                {
                    "id": 27205,  # pragma: allowlist secret
                    "title": "Inception",
                    "original_title": "Inception",
                    "overview": "A thief who steals corporate secrets...",
                    "release_date": "2010-07-15",
                    "vote_average": 8.3,
                    "vote_count": 32000,
                    "popularity": 60.0,
                    "poster_path": "/poster.jpg",
                    "genre_ids": [28, 878, 12],
                }
            ]
        }
        respx_mock.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": "Inception", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        respx_mock.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"query": "Inception", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json={"results": []}))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        results = await client.search("Inception")
        assert len(results) == 1
        movie = results[0]
        assert movie.title == "Inception"
        assert movie.provider == "tmdb"
        assert movie.provider_id == "27205"
        assert movie.year == 2010
        assert movie.vote_average == 8.3

    async def test_search_movie_no_results(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Edge: search_movie returns empty list when TMDB returns no results."""
        tmdb_response = {"results": []}
        respx_mock.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": "Nonexistent", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        respx_mock.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"query": "Nonexistent", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        results = await client.search("Nonexistent")
        assert results == []

    async def test_search_movie_unauthorized(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: search_movie raises HTTPStatusError on 401 Unauthorized."""
        respx_mock.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": "Inception", "api_key": "badkey"},
        ).mock(
            return_value=respx.MockResponse(
                401, json={"status_message": "Invalid API key."}
            )
        )
        respx_mock.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"query": "Inception", "api_key": "badkey"},
        ).mock(
            return_value=respx.MockResponse(
                401, json={"status_message": "Invalid API key."}
            )
        )
        monkeypatch.setenv("TMDB_API_KEY", "badkey")  # pragma: allowlist secret
        client = TMDBClient()
        with pytest.raises(Exception):
            await client.search("Inception")

    async def test_search_tv_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: search returns correct MediaMetadata for a known TV show title."""
        tmdb_response = {
            "results": [
                {
                    "id": 1396,  # pragma: allowlist secret
                    "name": "Breaking Bad",
                    "original_name": "Breaking Bad",
                    "overview": "A high school chemistry teacher...",
                    "first_air_date": "2008-01-20",
                    "vote_average": 8.9,
                    "vote_count": 12000,
                    "popularity": 80.0,
                    "poster_path": "/bbposter.jpg",
                    "genre_ids": [18, 80],
                }
            ]
        }
        respx_mock.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": "Breaking Bad", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json={"results": []}))
        respx_mock.get(
            "https://api.themoviedb.org/3/search/tv",
            params={"query": "Breaking Bad", "api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        results = await client.search("Breaking Bad")
        assert any(
            r.title == "Breaking Bad"
            and r.provider == "tmdb"
            and r.provider_id == "1396"
            for r in results
        )

    async def test_details_movie_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: details returns correct MediaMetadata for a known movie ID."""
        tmdb_response = {
            "id": 27205,
            "title": "Inception",
            "original_title": "Inception",
            "overview": "A thief who steals corporate secrets...",
            "release_date": "2010-07-15",
            "vote_average": 8.3,
            "vote_count": 32000,
            "popularity": 60.0,
            "poster_path": "/poster.jpg",
            "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Sci-Fi"}],
        }
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/27205",
            params={"api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        movie = await client.details("27205", MediaMetadataType.MOVIE)
        assert movie.title == "Inception"
        assert movie.provider == "tmdb"
        assert movie.provider_id == "27205"
        assert movie.year == 2010
        assert movie.vote_average == 8.3

    async def test_details_tv_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: details returns correct MediaMetadata for a known TV show ID."""
        tmdb_response = {
            "id": 1396,
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "overview": "A high school chemistry teacher...",
            "first_air_date": "2008-01-20",
            "vote_average": 8.9,
            "vote_count": 12000,
            "popularity": 80.0,
            "poster_path": "/bbposter.jpg",
            "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
        }
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/1396",
            params={"api_key": "dummy"},
        ).mock(
            return_value=respx.MockResponse(404, json={"status_message": "Not found"})
        )
        respx_mock.get(
            "https://api.themoviedb.org/3/tv/1396",
            params={"api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        show = await client.details("1396", MediaMetadataType.TV_SHOW)
        assert show.title == "Breaking Bad"
        assert show.provider == "tmdb"
        assert show.provider_id == "1396"
        assert show.year == 2008
        assert show.vote_average == 8.9

    async def test_details_not_found(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: details raises HTTPStatusError on 404 Not Found."""
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/999999",
            params={"api_key": "dummy"},
        ).mock(
            return_value=respx.MockResponse(404, json={"status_message": "Not found"})
        )
        respx_mock.get(
            "https://api.themoviedb.org/3/tv/999999",
            params={"api_key": "dummy"},
        ).mock(
            return_value=respx.MockResponse(404, json={"status_message": "Not found"})
        )
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        with pytest.raises(Exception):
            await client.details("999999", MediaMetadataType.MOVIE)

    async def test_details_unauthorized(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: details raises HTTPStatusError on 401 Unauthorized."""
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/27205",
            params={"api_key": "badkey"},
        ).mock(
            return_value=respx.MockResponse(
                401, json={"status_message": "Invalid API key."}
            )
        )
        respx_mock.get(
            "https://api.themoviedb.org/3/tv/27205",
            params={"api_key": "badkey"},
        ).mock(
            return_value=respx.MockResponse(
                401, json={"status_message": "Invalid API key."}
            )
        )
        monkeypatch.setenv("TMDB_API_KEY", "badkey")  # pragma: allowlist secret
        client = TMDBClient()
        with pytest.raises(Exception):
            await client.details("27205", MediaMetadataType.MOVIE)

    async def test_details_server_error(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: details raises HTTPStatusError on 500 Server Error."""
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/27205",
            params={"api_key": "dummy"},
        ).mock(
            return_value=respx.MockResponse(
                500, json={"status_message": "Server error"}
            )
        )
        respx_mock.get(
            "https://api.themoviedb.org/3/tv/27205",
            params={"api_key": "dummy"},
        ).mock(
            return_value=respx.MockResponse(
                500, json={"status_message": "Server error"}
            )
        )
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        with pytest.raises(Exception):
            await client.details("27205", MediaMetadataType.MOVIE)

    async def test_details_movie_artwork(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: details maps poster and backdrop URLs to artwork field."""
        tmdb_response = {
            "id": 27205,
            "title": "Inception",
            "original_title": "Inception",
            "overview": "A thief who steals corporate secrets...",
            "release_date": "2010-07-15",
            "vote_average": 8.3,
            "vote_count": 32000,
            "popularity": 60.0,
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Sci-Fi"}],
        }
        respx_mock.get(
            "https://api.themoviedb.org/3/movie/27205",
            params={"api_key": "dummy"},
        ).mock(return_value=respx.MockResponse(200, json=tmdb_response))
        monkeypatch.setenv("TMDB_API_KEY", "dummy")  # pragma: allowlist secret
        client = TMDBClient()
        movie = await client.details("27205", MediaMetadataType.MOVIE)
        poster_urls = [a.url for a in movie.artwork if a.type == "poster"]
        backdrop_urls = [a.url for a in movie.artwork if a.type == "backdrop"]
        assert any("w500" in str(url) for url in poster_urls)
        assert any("w780" in str(url) for url in backdrop_urls)
