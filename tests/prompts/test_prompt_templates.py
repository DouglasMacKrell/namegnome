"""Tests for Jinja2 prompt templates in NameGnome."""

import jinja2
import pytest

from namegnome.prompts.prompt_loader import render_prompt


def test_anthology_template_success() -> None:
    """Test successful rendering of anthology.j2 template."""
    result = render_prompt(
        "anthology.j2",
        show_name="Test Show",
        season_number=1,
        files=["ep1.mkv", "ep2.mkv"],
        context="Anthology context",
    )
    assert "Test Show" in result
    assert "ep1.mkv" in result
    assert "Anthology context" in result


def test_anthology_template_missing_var() -> None:
    """Test missing required variable in anthology.j2 raises UndefinedError."""
    with pytest.raises(jinja2.exceptions.UndefinedError):
        render_prompt(
            "anthology.j2",
            show_name="Test Show",
            season_number=1,
            files=["ep1.mkv"],
        )


def test_title_guess_template_success() -> None:
    """Test successful rendering of title_guess.j2 template."""
    result = render_prompt(
        "title_guess.j2",
        filename="moviefile.mkv",
        context="Guess context",
    )
    assert "moviefile.mkv" in result
    assert "Guess context" in result


def test_title_guess_template_missing_var() -> None:
    """Test missing required variable in title_guess.j2 raises UndefinedError."""
    with pytest.raises(jinja2.exceptions.UndefinedError):
        render_prompt(
            "title_guess.j2",
            filename="moviefile.mkv",
        )


def test_id_hint_template_success() -> None:
    """Test successful rendering of id_hint.j2 template."""
    result = render_prompt(
        "id_hint.j2",
        filename="showfile.mkv",
        show_name="Show Name",
        year=2020,
        context="ID context",
    )
    assert "showfile.mkv" in result
    assert "Show Name" in result
    assert "2020" in result
    assert "ID context" in result


def test_id_hint_template_missing_var() -> None:
    """Test missing required variable in id_hint.j2 raises UndefinedError."""
    with pytest.raises(jinja2.exceptions.UndefinedError):
        render_prompt(
            "id_hint.j2",
            filename="showfile.mkv",
            show_name="Show Name",
        )
