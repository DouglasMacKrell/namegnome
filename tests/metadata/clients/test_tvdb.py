"""Tests for the TVDBClient metadata provider.

Covers expected, edge, and failure cases for series search, episode listing, pagination, and token refresh.
"""

import pytest
import respx

from namegnome.metadata.clients.tvdb import TVDBClient


@pytest.mark.asyncio
class TestTVDBClient:
    """Tests for TVDBClient covering expected, edge, and failure cases."""

    async def test_search_series_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: search returns correct MediaMetadata for a known TV show title."""
        # Stub TVDB login response
        login_response = {"token": "dummy-jwt-token"}
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json=login_response)
        )

        # Stub TVDB series search response
        series_response = {
            "data": [
                {
                    "id": 12345,
                    "seriesName": "Parks and Recreation",
                    "overview": "A mockumentary sitcom about Pawnee, Indiana.",
                    "firstAired": "2009-04-09",
                    "network": "NBC",
                }
            ]
        }
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "Parks and Recreation"},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=series_response))

        # Stub TVDB episodes response (first page)
        episodes_response = {
            "links": {"next": 2, "last": 2},
            "data": [
                {
                    "id": 1001,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 1,
                    "episodeName": "Pilot",
                    "firstAired": "2009-04-09",
                    "overview": "Leslie Knope tries to turn a pit into a park.",
                }
            ],
        }
        respx_mock.get(
            "https://api.thetvdb.com/series/12345/episodes",
            params={"page": 1},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_response))

        # Stub TVDB episodes response (second page, empty)
        episodes_response_page2 = {"links": {"next": None, "last": 2}, "data": []}
        respx_mock.get(
            "https://api.thetvdb.com/series/12345/episodes",
            params={"page": 2},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_response_page2))

        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        results = await client.search("Parks and Recreation")
        assert len(results) == 1
        show = results[0]
        assert show.title == "Parks and Recreation"
        assert show.provider == "tvdb"
        assert show.provider_id == "12345"
        assert show.year == 2009
        assert show.episodes[0].title == "Pilot"
        assert show.episodes[0].season_number == 1
        assert show.episodes[0].episode_number == 1
        assert (show.episodes[0].overview or "").startswith("Leslie Knope")

    async def test_search_series_no_results(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Edge: search returns empty list when TVDB returns no results."""
        login_response = {"token": "dummy-jwt-token"}
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json=login_response)
        )
        series_response = {"data": []}
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "Nonexistent Show"},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=series_response))
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        results = await client.search("Nonexistent Show")
        assert results == []

    async def test_search_series_unauthorized(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: search raises HTTPStatusError on 401 Unauthorized from TVDB login."""
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(401, json={"Error": "Invalid API key."})
        )
        monkeypatch.setenv("TVDB_API_KEY", "bad-key")
        client = TVDBClient()
        with pytest.raises(Exception):
            await client.search("Any Show")

    async def test_search_series_pagination(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: search aggregates episodes from multiple paginated responses."""
        login_response = {"token": "dummy-jwt-token"}
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json=login_response)
        )
        series_response = {
            "data": [
                {
                    "id": 54321,
                    "seriesName": "Test Show",
                    "overview": "A test show for pagination.",
                    "firstAired": "2020-01-01",
                    "network": "TestNet",
                }
            ]
        }
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "Test Show"},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=series_response))
        # Page 1: one episode, next=2
        episodes_page1 = {
            "links": {"next": 2, "last": 2},
            "data": [
                {
                    "id": 2001,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 1,
                    "episodeName": "Ep1",
                    "firstAired": "2020-01-01",
                    "overview": "First episode.",
                }
            ],
        }
        respx_mock.get(
            "https://api.thetvdb.com/series/54321/episodes",
            params={"page": 1},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_page1))
        # Page 2: one episode, no next
        episodes_page2 = {
            "links": {"next": None, "last": 2},
            "data": [
                {
                    "id": 2002,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 2,
                    "episodeName": "Ep2",
                    "firstAired": "2020-01-08",
                    "overview": "Second episode.",
                }
            ],
        }
        respx_mock.get(
            "https://api.thetvdb.com/series/54321/episodes",
            params={"page": 2},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_page2))
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        results = await client.search("Test Show")
        assert len(results) == 1
        show = results[0]
        assert show.title == "Test Show"
        assert len(show.episodes) == 2
        assert show.episodes[0].title == "Ep1"
        assert show.episodes[1].title == "Ep2"

    async def test_search_series_token_refresh(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: client retries login and fetches episodes if token expires during fetch."""
        # First login
        respx_mock.post("https://api.thetvdb.com/login").mock(
            side_effect=[
                respx.MockResponse(200, json={"token": "token1"}),
                respx.MockResponse(200, json={"token": "token2"}),
            ]
        )
        # Series search
        series_response = {
            "data": [
                {
                    "id": 99999,
                    "seriesName": "Refresh Show",
                    "overview": "A show for token refresh.",
                    "firstAired": "2021-01-01",
                    "network": "RefreshNet",
                }
            ]
        }
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "Refresh Show"},
            headers={"Authorization": "Bearer token1"},
        ).mock(return_value=respx.MockResponse(200, json=series_response))
        # First episode fetch: 401 Unauthorized
        respx_mock.get(
            "https://api.thetvdb.com/series/99999/episodes",
            params={"page": 1},
            headers={"Authorization": "Bearer token1"},
        ).mock(return_value=respx.MockResponse(401, json={"Error": "Token expired."}))
        # Retry episode fetch with new token: success
        episodes_response = {
            "links": {"next": None, "last": 1},
            "data": [
                {
                    "id": 3001,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 1,
                    "episodeName": "Refreshed Ep",
                    "firstAired": "2021-01-01",
                    "overview": "Token refresh episode.",
                }
            ],
        }
        respx_mock.get(
            "https://api.thetvdb.com/series/99999/episodes",
            params={"page": 1},
            headers={"Authorization": "Bearer token2"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_response))
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        results = await client.search("Refresh Show")
        assert len(results) == 1
        show = results[0]
        assert show.title == "Refresh Show"
        assert len(show.episodes) == 1
        assert show.episodes[0].title == "Refreshed Ep"

    async def test_details_expected(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Expected: details returns correct MediaMetadata for a known series ID."""
        # Login
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json={"token": "tokenX"})
        )
        # Series details
        series_id = 88888
        details_response = {
            "data": {
                "id": series_id,
                "seriesName": "Details Show",
                "overview": "A show for details().",
                "firstAired": "2019-01-01",
                "network": "DetailsNet",
            }
        }
        respx_mock.get(
            f"https://api.thetvdb.com/series/{series_id}",
            headers={"Authorization": "Bearer tokenX"},
        ).mock(return_value=respx.MockResponse(200, json=details_response))
        # Episodes (single page)
        episodes_response = {
            "links": {"next": None, "last": 1},
            "data": [
                {
                    "id": 4001,
                    "airedSeason": 1,
                    "airedEpisodeNumber": 1,
                    "episodeName": "Details Ep1",
                    "firstAired": "2019-01-01",
                    "overview": "First details episode.",
                }
            ],
        }
        respx_mock.get(
            f"https://api.thetvdb.com/series/{series_id}/episodes",
            params={"page": 1},
            headers={"Authorization": "Bearer tokenX"},
        ).mock(return_value=respx.MockResponse(200, json=episodes_response))
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        meta = await client.details(str(series_id))
        assert meta.title == "Details Show"
        assert meta.provider == "tvdb"
        assert meta.provider_id == str(series_id)
        assert len(meta.episodes) == 1
        assert meta.episodes[0].title == "Details Ep1"

    async def test_search_series_not_found(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: search returns empty list on 404 Not Found from TVDB series search."""
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json={"token": "dummy-jwt-token"})
        )
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "Missing Show"},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(return_value=respx.MockResponse(404, json={"Error": "Not found"}))
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        results = await client.search("Missing Show")
        assert results == []

    async def test_search_series_rate_limit(
        self, respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failure: search raises HTTPStatusError on 429 Rate Limit from TVDB series search."""
        respx_mock.post("https://api.thetvdb.com/login").mock(
            return_value=respx.MockResponse(200, json={"token": "dummy-jwt-token"})
        )
        respx_mock.get(
            "https://api.thetvdb.com/search/series",
            params={"name": "RateLimit Show"},
            headers={"Authorization": "Bearer dummy-jwt-token"},
        ).mock(
            return_value=respx.MockResponse(429, json={"Error": "Too Many Requests"})
        )
        monkeypatch.setenv("TVDB_API_KEY", "dummy-key")
        client = TVDBClient()
        with pytest.raises(Exception):
            await client.search("RateLimit Show")
