"""Hot-spot tests for high-level LLM helpers in *prompt_orchestrator*.

These tests monkey-patch *ollama_client.generate* so that no network call is
performed. They cover both the happy path (valid JSON returned) and common
fallback/error paths when the LLM output is malformed or an exception occurs.
"""

from __future__ import annotations

from typing import Any

import pytest

from namegnome.llm import ollama_client as oc
from namegnome.llm import prompt_orchestrator as po


@pytest.fixture(autouse=True)
def _patch_generate(monkeypatch):
    """Replace *ollama_client.generate* with a deterministic async stub."""

    async def _fake_generate(model: str, prompt: str, stream: bool = True) -> str:  # noqa: D401, ANN001
        # Route the response based on a simple heuristic of the prompt content
        if "Generate a list of plausible filename variants" in prompt:
            return '["Foo", "Foo (alt)"]'
        if "Return the single official episode title" in prompt:
            return '"Canonical Foo"'
        if "Extract all episode titles" in prompt:
            return '[{"title": "Foo", "confidence": 0.95}]'
        # Default case – return invalid JSON to exercise fallback branches
        return "Not JSON"

    monkeypatch.setattr(oc, "generate", _fake_generate, raising=True)


def test_llm_generate_variants_parses_json():
    variants = po.llm_generate_variants("Foo")
    assert variants == ["Foo", "Foo (alt)"]


def test_normalize_title_with_llm_strips_quotes():
    title = po.normalize_title_with_llm("foo_segment", ["Canonical Foo"])
    assert title == "Canonical Foo"


def test_extract_episode_titles_from_filename():
    res = po.extract_episode_titles_from_filename("Foo.mkv", ["Foo"])
    assert res and res[0]["title"] == "Foo"


def test_llm_generate_variants_fallback_on_error(monkeypatch):
    """If *generate* raises, the function should gracefully fall back."""

    async def _raise(*args: Any, **kwargs: Any):  # noqa: D401, ANN001
        raise RuntimeError("network down")

    monkeypatch.setattr(oc, "generate", _raise, raising=True)
    assert po.llm_generate_variants("Foo") == ["Foo"]


@pytest.mark.asyncio
async def test_run_async_nested_loop(monkeypatch):  # noqa: D401
    """Verify that *_run_async* handles already-running event loops."""

    # Re-use the helper from cmd._run_async via a running loop
    from namegnome.cli import commands as cmd

    async def _coro():  # noqa: D401
        return 99

    # Simulate running loop by calling inside another coroutine
    async def _wrapper():  # noqa: D401
        return cmd._run_async(_coro())

    assert await _wrapper() == 99
