"""Tests for utils modules that currently have low coverage (config, debug)."""

import importlib
from pathlib import Path


from namegnome.utils import config as cfg
from namegnome.utils import debug as dbg


def test_get_set_default_llm_model(tmp_path, monkeypatch):
    """Ensure we can set and retrieve the default LLM model via the TOML config."""
    fake_home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Reload the module so that CONFIG_DIR/FILE are recalculated with patched home
    importlib.reload(cfg)

    # Initial read when file is absent
    assert cfg.get_default_llm_model() == "llama3:8b"

    # Write a new default model
    cfg.set_default_llm_model("gpt-4o")
    assert cfg.get_default_llm_model() == "gpt-4o"

    # Config file should exist in the fake home directory
    assert cfg.CONFIG_FILE.exists()


def test_debug_prints_when_env_var_set(capfd, monkeypatch):
    """When NAMEGNOME_DEBUG==1, debug() should print to stdout."""
    monkeypatch.setenv("NAMEGNOME_DEBUG", "1")
    importlib.reload(dbg)  # Apply env var change

    dbg.debug("hello world")
    captured = capfd.readouterr()
    assert "hello world" in captured.out

    # info/warn/error should not raise and utilise the logger
    dbg.info("info msg")
    dbg.warn("warn msg")
    dbg.error("error msg")
