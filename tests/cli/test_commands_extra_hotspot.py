"""Additional tests for helper functions in *namegnome.cli.commands* that were
previously under-covered.

These tests focus on pure helpers and avoid network or Typer invocation so they
stay lightweight and deterministic.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, List

import pytest

from namegnome.cli import commands as cmd
from namegnome.metadata.settings import MissingAPIKeyError
from namegnome.models.core import MediaFile, MediaType, ScanResult


class _DummySettings:
    """Stub version of the metadata *Settings* model with predictable values."""

    def model_dump(self) -> dict[str, Any]:  # type: ignore[override]
        return {
            "TMDB_API_KEY": "ABCD1234SECRET",  # secret-looking value to check masking
            "SOME_OTHER": "value",  # normal value printed verbatim
            "EMPTY": None,  # shows as <unset>
        }


@pytest.fixture()
def capture_console(monkeypatch):
    """Capture output routed through *cmd.console.print* in a list of strings."""

    printed: List[str] = []

    def _fake_print(msg: object, *args: object, **kwargs: object) -> None:  # noqa: D401
        printed.append(str(msg))

    monkeypatch.setattr(cmd.console, "print", _fake_print, raising=True)
    return printed


def test_print_settings_masks_and_formats(capture_console):
    """`_print_settings` should mask secrets and format other values."""

    cmd._print_settings(_DummySettings())
    output = "\n".join(capture_console)

    # Secret keys are partially masked
    assert "TMDB_API_KEY" in output and "ABCD..." in output and "SECRET" not in output

    # Normal keys show the full value
    assert "SOME_OTHER" in output and "value" in output

    # None values are represented as <unset>
    assert "EMPTY" in output and "<unset>" in output


def test_handle_settings_error_missing_key(capture_console):
    """`_handle_settings_error` should surface *MissingAPIKeyError* clearly."""

    err = MissingAPIKeyError("TMDB_API_KEY")
    cmd._handle_settings_error(err)

    combined = "\n".join(capture_console)
    assert "Missing required API key" in combined and "TMDB_API_KEY" in combined


def test_run_async_executes_coroutine():
    """`_run_async` synchronously executes and returns coroutine results."""

    async def _coro():  # noqa: D401
        return 42

    assert cmd._run_async(_coro()) == 42


def test_download_artwork_for_movies_creates_poster(tmp_path, monkeypatch):
    """Ensure `_download_artwork_for_movies` creates a poster file even when the
    network-bound fetch helper is stubbed.
    """

    async def _fake_fetch(meta, artwork_dir: Path):  # noqa: D401, ANN001
        artwork_dir.mkdir(parents=True, exist_ok=True)
        (artwork_dir / "poster.jpg").write_bytes(b"IMG")
        return None

    monkeypatch.setattr(cmd, "fetch_fanart_poster", _fake_fetch, raising=True)

    movie_path = tmp_path / "movie.mp4"
    movie_path.write_bytes(b"data")

    media_file = MediaFile(
        path=movie_path.resolve(),
        size=movie_path.stat().st_size,
        media_type=MediaType.MOVIE,
        modified_date=_dt.datetime.now(),
    )

    scan_result = ScanResult(
        files=[media_file],
        root_dir=tmp_path,
        media_types=[MediaType.MOVIE],
        platform="plex",
    )

    cmd._download_artwork_for_movies(scan_result, tmp_path)

    poster = tmp_path / ".namegnome" / "artwork" / "12345" / "poster.jpg"
    assert poster.exists() and poster.read_bytes() 