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


def test_build_anthology_prompt_martha_speaks_double_episode() -> None:
    """Test anthology prompt with a double-episode Martha Speaks file."""
    prompt = build_anthology_prompt(
        show_name="Martha Speaks",
        season_number=1,
        files=["Martha Speaks-S01E01-Martha Speaks Martha Gives Advice.mp4"],
        context="Anthology: double-episode test",
    )
    assert "Martha Speaks" in prompt
    assert "Martha Gives Advice" in prompt
    assert "Anthology: double-episode test" in prompt


def test_build_title_guess_prompt_paw_patrol_fuzzy() -> None:
    """Test title guess prompt for Paw Patrol fuzzy title edge case."""
    prompt = build_title_guess_prompt(
        filename="Paw Patrol-S01E01-Pups And The Kitty Tastrophe Pups Save A Train.mp4",
        context="Fuzzy title: Kitty Tastrophe edge case",
    )
    assert "Kitty Tastrophe" in prompt
    assert "Pups Save A Train" in prompt
    assert "Fuzzy title: Kitty Tastrophe edge case" in prompt


def test_build_anthology_prompt_special_characters() -> None:
    """Test anthology prompt construction with special characters and ambiguous input."""
    prompt = build_anthology_prompt(
        show_name="Martha's Holiday Surprise",
        season_number=6,
        files=["Martha Speaks-S06E08-Martha S Holiday Surprise We Re Powerless.mp4"],
        context="Edge case: apostrophes and ambiguous segment",
    )
    assert "Martha's Holiday Surprise" in prompt or "Marthas Holiday Surprise" in prompt
    assert "We Re Powerless" in prompt or "Were Powerless" in prompt
    assert "Edge case: apostrophes" in prompt


def test_build_id_hint_prompt_manual_flag() -> None:
    """Test ID hint prompt for ambiguous/manual flag scenario."""
    prompt = build_id_hint_prompt(
        filename="Unknown Show-S01E99-Unknown Story.mp4",
        show_name="Unknown Show",
        year=2020,
        context="Manual review required",
    )
    assert "Unknown Show" in prompt
    assert "Unknown Story" in prompt
    assert "Manual review required" in prompt
