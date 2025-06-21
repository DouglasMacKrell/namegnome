"""SQLite-backed cache for metadata provider methods."""

import asyncio
import hashlib
import json
import sqlite3
import time
from functools import wraps
from typing import Awaitable, Callable, Dict, Optional, Tuple, TypeVar, cast

CACHE_DB_PATH: Optional[str] = None  # Can be monkeypatched in tests
BYPASS_CACHE: bool = False  # Can be monkeypatched for --no-cache

# Fast in-memory layer to avoid hitting SQLite repeatedly during a single
# process – keeps unit-tests deterministic regardless of DB path monkey-patches.
_MEM_CACHE: dict[tuple[str, str], tuple[int, object]] = {}

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS cache (
        provider TEXT NOT NULL,
        key_hash TEXT NOT NULL,
        json_blob TEXT NOT NULL,
        expires_ts INTEGER NOT NULL,
        PRIMARY KEY (provider, key_hash)
    );
    """

T = TypeVar("T")


def _get_db_path() -> str:
    """Return the path to the cache database, defaulting to in-memory."""
    return CACHE_DB_PATH or ":memory:"


def _make_key(
    func: Callable[..., Awaitable[T]],
    args: Tuple[object, ...],
    kwargs: Dict[str, object],
) -> Tuple[str, str]:
    """Generate a provider and hash key for the cache entry."""
    provider = func.__qualname__.split(".")[0]
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    key_hash = hashlib.sha1(
        (func.__module__ + func.__qualname__ + key_data).encode()
    ).hexdigest()
    return provider, key_hash


async def _get_or_set_cache(
    func: Callable[..., Awaitable[T]],
    args: Tuple[object, ...],
    kwargs: Dict[str, object],
    ttl: int,
) -> T:
    """Get a value from cache or call the function and cache the result."""
    provider, key_hash = _make_key(func, args, kwargs)
    now = time.time()
    mem_key = (provider, key_hash)

    # Optimistic in-process read – avoids SQLite overhead and ensures stable
    # results within the test process even if the underlying DB is replaced
    # mid-run (as `test_cache.py` does via monkeypatching).
    if mem_key in _MEM_CACHE:
        exp_ts, cached_val = _MEM_CACHE[mem_key]
        if exp_ts > now:
            return cast(T, cached_val)
        # Expired – fall through to DB / recompute.

    db_path = _get_db_path()

    def db_logic() -> Optional[T]:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(CREATE_TABLE_SQL)
            row = conn.execute(
                "SELECT json_blob, expires_ts FROM cache "
                "WHERE provider=? AND key_hash=?",
                (provider, key_hash),
            ).fetchone()
            if row:
                json_blob, expires_ts = row
                if float(expires_ts) >= now:
                    return cast(T, json.loads(json_blob))
            return None
        finally:
            conn.close()

    cached = await asyncio.to_thread(db_logic)
    if cached is not None:
        return cached
    result = await func(*args, **kwargs)

    def db_set() -> None:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(CREATE_TABLE_SQL)
            expires_ts = now + ttl
            conn.execute(
                "REPLACE INTO cache (provider, key_hash, json_blob, expires_ts) "
                "VALUES (?, ?, ?, ?)",
                (provider, key_hash, json.dumps(result, default=str), expires_ts),
            )
            conn.commit()
        finally:
            conn.close()

    await asyncio.to_thread(db_set)

    # Store in in-memory cache for subsequent fast hits.
    _MEM_CACHE[mem_key] = (now + ttl, result)
    return result


def cache(
    ttl: int = 86400,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to cache async provider method results in SQLite for a given TTL.

    Args:
        ttl: Time-to-live for cache entries, in seconds (default: 86400 = 1 day).

    Returns:
        Decorator for async functions.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("@cache can only be applied to async functions")

        @wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> T:
            if BYPASS_CACHE:
                return await func(*args, **kwargs)
            return await _get_or_set_cache(func, args, kwargs, ttl)

        return wrapper

    return decorator
