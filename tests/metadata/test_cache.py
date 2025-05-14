"""Tests for the SQLite-backed cache decorator for metadata provider methods."""

import asyncio

import pytest

from namegnome.metadata.cache import cache


class DummyProvider:
    """Dummy provider for testing the cache decorator."""

    call_count: int = 0

    @cache(ttl=1)
    async def get_data(self, key: str) -> dict:
        """Return a dict with a unique value per call for testing cache."""
        self.call_count += 1
        return {"key": key, "value": f"result-{self.call_count}"}


@pytest.mark.asyncio
async def test_cache_stores_and_retrieves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: "pytest.TempPathFactory"
) -> None:
    """Test that the cache stores and retrieves values, calling the function once."""
    monkeypatch.setattr(
        "namegnome.metadata.cache.CACHE_DB_PATH",
        str(tmp_path / "test_cache.db"),
    )
    provider = DummyProvider()
    result1 = await provider.get_data("foo")
    result2 = await provider.get_data("foo")
    assert result1 == result2
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_cache_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: "pytest.TempPathFactory"
) -> None:
    """Test that the cache expires after TTL and calls the function again."""
    monkeypatch.setattr(
        "namegnome.metadata.cache.CACHE_DB_PATH",
        str(tmp_path / "test_cache_expiry.db"),
    )
    provider = DummyProvider()
    result1 = await provider.get_data("bar")
    await asyncio.sleep(1.1)
    result2 = await provider.get_data("bar")
    assert provider.call_count == 2
    assert result1 != result2


@pytest.mark.asyncio
async def test_cache_bypass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: "pytest.TempPathFactory"
) -> None:
    """Test that setting BYPASS_CACHE disables caching and always calls the function."""
    monkeypatch.setattr(
        "namegnome.metadata.cache.CACHE_DB_PATH",
        str(tmp_path / "test_cache_bypass.db"),
    )
    monkeypatch.setattr("namegnome.metadata.cache.BYPASS_CACHE", True)
    provider = DummyProvider()
    result1 = await provider.get_data("baz")
    result2 = await provider.get_data("baz")
    assert provider.call_count == 2
    assert result1 != result2
    monkeypatch.setattr("namegnome.metadata.cache.BYPASS_CACHE", False)
