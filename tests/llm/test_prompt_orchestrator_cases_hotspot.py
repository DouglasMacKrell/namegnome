"""Tests that exercise individual _parse_llm_case_* helpers in prompt_orchestrator."""

from namegnome.llm import prompt_orchestrator as po
import namegnome.utils.config as cfg


def test_parse_llm_case_list_of_strings():
    data = ["A", "B"]
    assert po._parse_llm_case_list_of_strings(data) == ["A", "B"]
    assert po._parse_llm_case_list_of_strings({}) == []


def test_parse_llm_case_dicts_with_title():
    data = [{"title": "Foo"}, {"title": "Bar"}]
    assert po._parse_llm_case_dicts_with_title(data) == ["Foo", "Bar"]
    assert po._parse_llm_case_dicts_with_title([{"name": "Baz"}]) == []


def test_parse_llm_case_list_of_sets():
    data = [{"dummy"}, {"A", "B"}]
    assert sorted(po._parse_llm_case_list_of_sets(data)) == ["A", "B", "dummy"]
    assert po._parse_llm_case_list_of_sets(["A"]) == []


def test_parse_llm_case_single_set():
    data = {"Zed", "Alpha"}
    assert sorted(po._parse_llm_case_single_set(data)) == ["Alpha", "Zed"]
    assert po._parse_llm_case_single_set(["not", "a", "set"]) == []


def test_parse_llm_case_mixed_list():
    data = [
        "Solo",
        {"title": "DictTitle"},
        {"Nested", "Set"},
    ]
    result = po._parse_llm_case_mixed_list(data)
    assert "Solo" in result and "DictTitle" in result and "Nested" in result and "Set" in result

    # Should return [] when nothing matches
    assert po._parse_llm_case_mixed_list([42, {}]) == []


def test_llm_generate_variants_and_disambiguate(monkeypatch):
    """Exercise variant generation and disambiguation helpers with a stubbed LLM."""

    async def fake_generate(model, prompt, stream=False):  # noqa: D401
        # Return JSON depending on prompt content to keep it simple
        if "Generate a list" in prompt:
            return '["Foo","Foo Variant"]'
        else:
            return '["Foo"]'

    # Patch both the LLM call and default model to avoid touching user config
    monkeypatch.setattr(po.ollama_client, "generate", fake_generate)
    monkeypatch.setattr(cfg, "get_default_llm_model", lambda: "dummy", raising=False)

    variants = po.llm_generate_variants("Foo")
    assert "Foo" in variants and "Foo Variant" in variants

    chosen = po.llm_disambiguate_candidates("foo_file.mkv", ["Foo", "Bar"])
    assert chosen == ["Foo"] 