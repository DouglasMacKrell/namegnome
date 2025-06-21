import asyncio
from pathlib import Path

import pytest

from namegnome.metadata.cache import cache


class _DummyProvider:
    call_count: int = 0

    @cache(ttl=1)
    async def get_data(self, key: str) -> dict:  # noqa: D401 – simple stub
        self.__class__.call_count += 1
        return {"key": key, "value": f"result-{self.call_count}"}


@pytest.mark.asyncio
async def test_cache_stores_and_expires(tmp_path: Path, monkeypatch) -> None:
    """Verify in-process cache returns same value until TTL expires."""

    monkeypatch.setattr(
        "namegnome.metadata.cache.CACHE_DB_PATH", str(tmp_path / "reg_cache.db")
    )

    provider = _DummyProvider()

    r1 = await provider.get_data("foo")
    r2 = await provider.get_data("foo")
    assert r1 == r2
    assert provider.call_count == 1

    await asyncio.sleep(1.1)

    r3 = await provider.get_data("foo")
    assert provider.call_count == 2
    assert r3 != r1
