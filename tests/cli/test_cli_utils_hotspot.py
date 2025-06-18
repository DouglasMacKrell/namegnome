"""Unit tests for small helper functions in namegnome.cli.commands."""

import asyncio
from datetime import datetime
from pathlib import Path

import pytest

from namegnome.cli import commands as cmd
from namegnome.models.core import MediaType
from namegnome.models.scan import ScanOptions as ModelScanOptions


class DummyOptions(cmd.ScanCommandOptions):
    """ScanCommandOptions with minimal viable defaults for tests."""

    def __init__(self, root: Path):
        super().__init__(root=root)


@pytest.mark.asyncio
async def test_run_async_with_running_loop(monkeypatch):
    """_run_async should detect existing loop and schedule coroutine."""

    async def coro():  # noqa: D401
        return 42

    # Simulate running loop by calling from within one
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: cmd._run_async(coro())
    )
    assert result == 42


def test_convert_to_model_options(tmp_path):
    opts = DummyOptions(root=tmp_path)
    media_types = [MediaType.TV]
    scan_opts = ModelScanOptions(root=tmp_path, media_types=media_types)

    model_opts = cmd._convert_to_model_options(opts, media_types, scan_opts)
    assert model_opts.root == tmp_path
    assert model_opts.platform == "plex"
    assert model_opts.media_types == media_types 