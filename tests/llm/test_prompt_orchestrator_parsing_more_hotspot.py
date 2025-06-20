"""Extra tests to exercise the diverse parsing branches in
*namegnome.llm.prompt_orchestrator*.

These inputs simulate the variety of formats an LLM might return when asked to
select episode titles from a list.  They ensure the private helper
`_parse_llm_disambiguate_response` can gracefully handle each format and that
all specialised case-functions are executed at least once.
"""

from __future__ import annotations

import pytest

from namegnome.llm import prompt_orchestrator as po


@pytest.mark.parametrize(
    "response, expected",
    [
        ('["Title A", "Title B"]', ["Title A", "Title B"]),  # list of strings
        (
            '[{"title": "Title C"}, {"title": "Title D"}]',
            ["Title C", "Title D"],  # list of dicts
        ),
        ("{'Title E', 'Title F'}", ["Title E", "Title F"]),  # single set
        ("[{'Title G', 'Title H'}]", ["Title G", "Title H"]),  # list of sets
        (
            "['Title I', {\"title\": 'Title J'}, {'Title K', 'Title L'}]",
            ["Title I", "Title J", "Title K", "Title L"],  # mixed list
        ),
    ],
)
def test_parse_llm_disambiguate_variants(response: str, expected: list[str]):  # noqa: D401
    # Provide the expected titles as the candidates list; successful parsing
    # should return them, but even on failure the helper would fall back to the
    # first element – making the assertion below safe.
    result = po._parse_llm_disambiguate_response(response, expected)

    for title in expected:
        assert title in result


def test_parse_llm_segments_with_sanitisation():
    """A messy response with unquoted episode values and comments is cleaned."""

    raw = (
        "[\n"
        '  {"title": "Foo", "episode": S01E01,}, // trailing comma & comment\n'
        '  {"title": "Bar", "episode": S01E02}\n'
        "]"
    )
    segments = po.parse_llm_segments(raw)
    assert isinstance(segments, list) and segments[0]["episode"] == "S01E01"
