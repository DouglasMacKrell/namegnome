"""Tests for the prompt orchestrator module in NameGnome."""

from namegnome.llm.prompt_orchestrator import (
    build_anthology_prompt,
    build_id_hint_prompt,
    build_title_guess_prompt,
)


def test_build_anthology_prompt_success() -> None:
    """Test successful anthology prompt generation."""
    prompt = build_anthology_prompt(
        show_name="Test Show",
        season_number=1,
        files=["ep1.mkv", "ep2.mkv"],
        context="Anthology context",
    )
    assert "Test Show" in prompt
    assert "ep1.mkv" in prompt
    assert "Anthology context" in prompt


def test_build_title_guess_prompt_success() -> None:
    """Test successful title guess prompt generation."""
    prompt = build_title_guess_prompt(
        filename="moviefile.mkv",
        context="Guess context",
    )
    assert "moviefile.mkv" in prompt
    assert "Guess context" in prompt


def test_build_id_hint_prompt_success() -> None:
    """Test successful ID hint prompt generation."""
    prompt = build_id_hint_prompt(
        filename="showfile.mkv",
        show_name="Show Name",
        year=2020,
        context="ID context",
    )
    assert "showfile.mkv" in prompt
    assert "Show Name" in prompt
    assert "2020" in prompt
    assert "ID context" in prompt


def test_title_guess_template_success() -> None:
    """Test successful title guess prompt generation."""
    # ... existing code ...
    pass


def test_id_hint_template_success() -> None:
    """Test successful ID hint prompt generation."""
    # ... existing code ...
    pass
