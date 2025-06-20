# mypy: disable-error-code=no-any-return
# See https://github.com/python/mypy/issues/5697 for context on this false positive.

"""Prompt orchestrator for LLM workflows in NameGnome.

Provides functions to build prompts for anthology splitting, title guessing,
and ID hinting using Jinja2 templates.
"""

import ast
import asyncio
import json
import re
import typing
from typing import Any, Coroutine, Optional, TypedDict

from namegnome.llm import ollama_client
from namegnome.models.core import MediaFile
from namegnome.prompts.prompt_loader import render_prompt
from namegnome.utils.json import DateTimeEncoder


class AnthologySegment(TypedDict, total=False):
    """Represents a segment of an anthology episode.

    Includes title, episode, and optional confidence fields.
    """

    title: str
    episode: str
    confidence: float


def build_anthology_prompt(
    *,
    show_name: str,
    season_number: int,
    files: list[str],
    context: str,
    episode_list: str = "",
) -> str:
    """Build the anthology episode splitter prompt.

    Args:
        show_name: The name of the show.
        season_number: The season number.
        files: List of filenames.
        context: Additional context string.
        episode_list: JSON string of official episodes (optional).

    Returns:
        Rendered prompt string.
    """
    return render_prompt(
        "anthology.j2",
        show_name=show_name,
        season_number=season_number,
        files=files,
        context=context,
        episode_list=episode_list,  # Always defined
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


def sanitize_llm_output(raw: str) -> str:
    """Sanitize LLM output to make it more parseable as JSON or Python."""
    # Remove comments (// or #) and C-style / multi-line comments
    raw = re.sub(r"//.*", "", raw)  # Single-line // comments
    raw = re.sub(r"#.*", "", raw)  # Single-line # comments
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)  # /* multi-line */ comments
    raw = re.sub(
        r"<!--.*?-->", "", raw, flags=re.DOTALL
    )  # <!-- HTML-style --> comments
    # Replace unquoted episode values (e.g., S01E02) with quoted strings
    raw = re.sub(
        r"([\"']episode[\"']\s*:\s*)(S\d+E\d+(\.\d+)?)([\,\s}])", r'\1"\2"\4', raw
    )
    # Replace null with None for Python, or vice versa for JSON
    raw = raw.replace("null", "None")
    # Remove only trailing commas before } or ]
    raw = re.sub(r",([\s]*[\}\]])", r"\1", raw)
    # Remove any trailing commas at the end of the list
    raw = re.sub(r",\s*\]", "]", raw)
    return raw


def parse_llm_segments(response: str) -> list[dict[str, Any]]:
    """Try to parse LLM output as JSON, then Python, then sanitized."""
    import json

    try:
        return json.loads(response)
    except Exception:
        try:
            return ast.literal_eval(response)
        except Exception:
            # Try sanitizing and parsing again
            sanitized = sanitize_llm_output(response)
            try:
                return json.loads(sanitized)
            except Exception:
                try:
                    return ast.literal_eval(sanitized)
                except Exception as e:
                    raise TypeError(
                        f"LLM did not return a valid list of dicts as segments: {e}\n"
                        f"Response: {response}"
                    )


def split_anthology(
    media_file: MediaFile,
    show_name: str,
    season_number: int,
    model: Optional[str] = None,
    episode_list: Optional[list[dict[str, object]]] = None,
) -> dict[str, object]:
    """Call the LLM to map anthology file to episode numbers.

    Uses the new mapping prompt.

    Args:
        media_file: The MediaFile to split.
        show_name: The robustly extracted show name.
        season_number: The robustly extracted season number.
        model: Optional LLM model name.
        episode_list: Optional list of official episodes (dicts or TVEpisode) to
            include in the prompt.

    Returns:
        Dict with keys:
            'episode_numbers': list of episode numbers (as strings) for this file
            'episode_list': the official episode list (if available)
    """
    files = [str(media_file.path.name)]
    context = "Map this file to its constituent episode numbers."
    episodes_json = ""
    if episode_list:
        import json as _json

        def ep_to_dict(ep: dict[str, object]) -> dict[str, object]:
            if hasattr(ep, "dict"):
                return ep.dict()
            elif hasattr(ep, "model_dump"):
                return ep.model_dump()
            return dict(ep)

        episodes_json = _json.dumps(
            [ep_to_dict(ep) for ep in episode_list],
            ensure_ascii=False,
            cls=DateTimeEncoder,
        )
        context += f"\nOfficial episode list for this season (JSON): {episodes_json}"
    prompt = build_anthology_prompt(
        show_name=show_name,
        season_number=season_number,
        files=files,
        context=context,
        episode_list=episodes_json,  # Always pass, even if empty
    )
    if model is None:
        from namegnome.utils.config import get_default_llm_model

        model = get_default_llm_model()
    try:
        response = asyncio.run(
            typing.cast(
                Coroutine[object, object, str],
                ollama_client.generate(model, prompt, stream=False),
            )
        )
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}")
    try:
        mapping = json.loads(response)
    except Exception:
        mapping = {}
    filename = str(media_file.path.name)
    episode_numbers = mapping.get(filename, [])
    # Always return as strings for consistency
    episode_numbers = [str(e) for e in episode_numbers]
    return {"episode_numbers": episode_numbers, "episode_list": episode_list}


def build_title_extraction_prompt(filename: str, episode_titles: list[str]) -> str:
    """Build a prompt to extract likely episode titles from a filename."""
    titles_json = json.dumps(episode_titles, ensure_ascii=False, cls=DateTimeEncoder)
    return (
        f"You are given a filename and a list of official episode titles for a TV "
        f"show season.\nFilename: {filename}\nOfficial episode titles: {titles_json}\n"
        "Extract all episode titles from the list that are likely present in the "
        "filename.\nFor each, return the title and a confidence score (0-1).\n"
        'Output a JSON list of objects: [{"title": ..., "confidence": ...}]\n'
        "Do not include any explanation."
    )


def extract_episode_titles_from_filename(
    filename: str,
    episode_titles: list[str],
    model: Optional[str] = None,
) -> list[dict[str, object]]:
    """Use the LLM to extract likely episode titles from a filename, with confidence."""
    prompt = build_title_extraction_prompt(filename, episode_titles)
    if model is None:
        from namegnome.utils.config import get_default_llm_model

        model = get_default_llm_model()
    try:
        response = asyncio.run(
            typing.cast(
                Coroutine[object, object, str],
                ollama_client.generate(model, prompt, stream=False),
            )
        )
    except Exception:
        return []
    try:
        result = json.loads(response)
    except Exception:
        result = []
    return result


def normalize_title_with_llm(
    segment: str, episode_titles: list[str], model: Optional[str] = None
) -> str:
    """Normalize a filename segment to the closest official episode title.

    Uses the LLM to match the segment to the best title.

    Args:
        segment: The filename segment to normalize.
        episode_titles: List of official episode titles for context.
        model: Optional LLM model name.

    Returns:
        Normalized string (official episode title or best guess).
    """
    prompt = (
        f"You are given a filename segment and a list of official episode titles for "
        f"a TV show.\nFilename segment: {segment}\n"
        f"Official episode titles: "
        f"{json.dumps(episode_titles, ensure_ascii=False, cls=DateTimeEncoder)}\n"
        "Return the single official episode title from the list that best matches the "
        "filename segment. If none are a good match, return your best guess. Output "
        "only the title as a string, no explanation."
    )
    if model is None:
        from namegnome.utils.config import get_default_llm_model

        model = get_default_llm_model()
    try:
        response = asyncio.run(
            typing.cast(
                Coroutine[object, object, str],
                ollama_client.generate(model, prompt, stream=False),
            )
        )
    except Exception:
        return segment
    try:
        result = response.strip()
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1]
        return result
    except Exception:
        return segment


def llm_generate_variants(title: str, model: Optional[str] = None) -> list[str]:
    """Use the LLM to generate possible filename variants for an episode title.

    Args:
        title: The episode title.
        model: Optional LLM model name.

    Returns:
        List of variant strings.
    """
    prompt = (
        f"You are given an official TV episode title.\nTitle: {title}\n"
        "Generate a list of plausible filename variants for this title. "
        "Variants should include common ways the title might appear in a filename, "
        "such as removing punctuation, replacing 'and' with '&', abbreviations, "
        "or omitting articles. Output a JSON list of strings. Do not include any "
        "explanation."
    )
    if model is None:
        from namegnome.utils.config import get_default_llm_model

        model = get_default_llm_model()
    try:
        response = asyncio.run(
            typing.cast(
                Coroutine[object, object, str],
                ollama_client.generate(model, prompt, stream=False),
            )
        )
    except Exception:
        return [title]
    try:
        variants = json.loads(response)
        if not isinstance(variants, list):
            raise ValueError("LLM did not return a list")
        return [str(v) for v in variants if isinstance(v, str)]
    except Exception:
        return [title]


def _parse_llm_case_list_of_strings(parsed: object) -> list[str]:
    if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
        return parsed
    return []


def _parse_llm_case_dicts_with_title(parsed: object) -> list[str]:
    if isinstance(parsed, list) and all(
        isinstance(x, dict) and "title" in x for x in parsed
    ):
        return [x["title"] for x in parsed if "title" in x]
    return []


def _parse_llm_case_list_of_sets(parsed: object) -> list[str]:
    if isinstance(parsed, list) and all(isinstance(x, set) for x in parsed):
        return [item for s in parsed for item in s if isinstance(item, str)]
    return []


def _parse_llm_case_single_set(parsed: object) -> list[str]:
    if isinstance(parsed, set):
        return [item for item in parsed if isinstance(item, str)]
    return []


def _parse_llm_case_mixed_list(parsed: object) -> list[str]:
    if isinstance(parsed, list):
        flat = []
        for x in parsed:
            if isinstance(x, str):
                flat.append(x)
            elif isinstance(x, dict) and "title" in x:
                flat.append(x["title"])
            elif isinstance(x, set):
                flat.extend([item for item in x if isinstance(item, str)])
        if flat:
            return flat
    return []


def _parse_llm_disambiguate_response(response: str, candidates: list[str]) -> list[str]:
    """Helper to parse LLM disambiguate response into a list of titles.

    Tries several parsing strategies for robustness.
    """
    try:
        parsed = None
        try:
            parsed = json.loads(response)
        except Exception:
            parsed = ast.literal_eval(response)
        for case_fn in [
            _parse_llm_case_list_of_strings,
            _parse_llm_case_dicts_with_title,
            _parse_llm_case_list_of_sets,
            _parse_llm_case_single_set,
            _parse_llm_case_mixed_list,
        ]:
            result = case_fn(parsed)
            if result:
                return result
    except Exception:
        pass
    return candidates[:1] if candidates else []


def llm_disambiguate_candidates(
    filename: str, candidates: list[str], model: Optional[str] = None
) -> list[str]:
    """Disambiguate which candidate episode titles are present in the filename.

    Uses the LLM to select the correct titles from the candidates.

    Args:
        filename: The filename to check.
        candidates: List of candidate episode titles.
        model: Optional LLM model name.

    Returns:
        List of selected titles.
    """
    prompt = (
        f"You are given a filename and a list of candidate episode titles for a TV "
        f"show.\nFilename: {filename}\n"
        f"Candidate episode titles: "
        f"{json.dumps(candidates, ensure_ascii=False, cls=DateTimeEncoder)}\n"
        "Select all episode titles from the list that are present in the filename. "
        "Output a JSON list of the selected titles. Do not include any explanation."
    )
    if model is None:
        from namegnome.utils.config import get_default_llm_model

        model = get_default_llm_model()
    try:
        response = asyncio.run(
            typing.cast(
                Coroutine[Any, Any, str],
                ollama_client.generate(model, prompt, stream=False),
            )
        )
        return _parse_llm_disambiguate_response(response, candidates)
    except Exception:
        return candidates[:1] if candidates else []
