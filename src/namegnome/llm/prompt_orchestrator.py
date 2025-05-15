"""Prompt orchestrator for LLM workflows in NameGnome.

Provides functions to build prompts for anthology splitting, title guessing,
and ID hinting using Jinja2 templates.
"""

from namegnome.prompts.prompt_loader import render_prompt


def build_anthology_prompt(
    *, show_name: str, season_number: int, files: list[str], context: str
) -> str:
    """Build the anthology episode splitter prompt.

    Args:
        show_name: The name of the show.
        season_number: The season number.
        files: List of filenames.
        context: Additional context string.

    Returns:
        Rendered prompt string.
    """
    return render_prompt(
        "anthology.j2",
        show_name=show_name,
        season_number=season_number,
        files=files,
        context=context,
    )


def build_title_guess_prompt(*, filename: str, context: str) -> str:
    """Build the title guess prompt.

    Args:
        filename: The filename to guess the title for.
        context: Additional context string.

    Returns:
        Rendered prompt string.
    """
    return render_prompt(
        "title_guess.j2",
        filename=filename,
        context=context,
    )


def build_id_hint_prompt(
    *, filename: str, show_name: str, year: int, context: str
) -> str:
    """Build the ID hint prompt.

    Args:
        filename: The filename to hint the ID for.
        show_name: The name of the show.
        year: The year of the show.
        context: Additional context string.

    Returns:
        Rendered prompt string.
    """
    return render_prompt(
        "id_hint.j2",
        filename=filename,
        show_name=show_name,
        year=year,
        context=context,
    )
