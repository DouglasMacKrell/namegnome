"""Tests for the prompt loader in NameGnome."""

from pathlib import Path

import jinja2
import pytest

from namegnome.prompts.prompt_loader import render_prompt


def test_render_prompt_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful rendering of a Jinja2 template."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    template_path = prompts_dir / "test_template.j2"
    template_path.write_text("Hello, {{ name }}!")
    monkeypatch.setattr("namegnome.prompts.prompt_loader.PROMPTS_DIR", prompts_dir)
    result = render_prompt("test_template.j2", name="World")
    assert result == "Hello, World!"


def test_render_prompt_missing_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test rendering with a missing required variable raises UndefinedError."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    template_path = prompts_dir / "test_template.j2"
    template_path.write_text("Hello, {{ name }}!")
    monkeypatch.setattr("namegnome.prompts.prompt_loader.PROMPTS_DIR", prompts_dir)
    with pytest.raises(jinja2.exceptions.UndefinedError):
        render_prompt("test_template.j2")
