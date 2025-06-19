"""Lightweight tests that exercise JSON sanitisation and parsing helpers in
namegnome.llm.prompt_orchestrator.

These tests avoid calling the actual LLM; they target pure helper functions
with deterministic behaviour.
"""

import pytest

from namegnome.llm import prompt_orchestrator as po


def test_sanitize_llm_output_quotes_episode():
    raw = '[{"episode": S01E01, "title": "Foo"},]'
    cleaned = po.sanitize_llm_output(raw)
    # Episode value should now be quoted and trailing comma removed
    assert '"episode"' in cleaned and '"S01E01"' in cleaned
    assert cleaned.strip().endswith("]")


def test_parse_llm_segments_handles_single_quotes():
    response = "[{'title': 'Foo', 'episode': 'S01E01'}]"
    parsed = po.parse_llm_segments(response)
    assert isinstance(parsed, list) and parsed[0]["title"] == "Foo"


def test_parse_llm_segments_raises_on_bad_input():
    with pytest.raises(TypeError):
        po.parse_llm_segments("Not a list of dicts")


def test_parse_llm_disambiguate_response():
    candidates = ["Title A", "Title B"]
    response = '["Title B"]'
    result = po._parse_llm_disambiguate_response(response, candidates)
    assert result == ["Title B"]
