"""Tests for pure prompt-building helpers in prompt_orchestrator.

These hit lines not previously executed, improving coverage without touching
external LLM calls.
"""

from namegnome.llm import prompt_orchestrator as po


def test_build_anthology_prompt_contains_parts():
    prompt = po.build_anthology_prompt(
        show_name="Foo Show",
        season_number=1,
        files=["Foo-S01E01.mkv"],
        context="Map this file to episodes.",
        episode_list="[]",
    )
    assert "Foo Show" in prompt and "S01" in prompt and "Map this file" in prompt


def test_build_title_guess_prompt():
    prompt = po.build_title_guess_prompt(filename="Foo.mkv", context="Context")
    assert "Foo.mkv" in prompt and "Context" in prompt


def test_build_id_hint_prompt():
    prompt = po.build_id_hint_prompt(
        filename="Foo.mkv", show_name="Foo Show", year=2020, context="Ctx"
    )
    assert "Foo Show" in prompt and "2020" in prompt and "Foo.mkv" in prompt


def test_normalize_title_with_llm_fallback(monkeypatch):
    # Patch generate to raise so that fallback path is taken
    async def fake_generate(model, prompt, stream=False):  # noqa: D401
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(po.ollama_client, "generate", fake_generate)
    title = po.normalize_title_with_llm("Str Segment", ["Official Title"])
    # With exception, original segment is returned unchanged
    assert title == "Str Segment" 