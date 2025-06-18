"""Stub for TV segment splitter."""
import re


def _detect_delimiter(text: str, delimiters: list[str]) -> str | None:
    """Return the first delimiter from *delimiters* that appears in *text*.

    The helper is intentionally simple: we do not attempt sophisticated token
    detection – just a substring scan in the order the delimiters are passed
    in.  This is sufficient for the unit-tests which only expect the function
    to recognise common anthology delimiters such as " and " or " & ".
    """
    for delim in delimiters:
        if delim in text:
            return delim
    return None


def _find_candidate_splits(tokens, episode_titles, episode_list):
    """
    Find valid splits between episode titles in a tokenized filename.
    Minimal implementation: only pass the first failing test.
    """
    # Join tokens to string and check for each episode title as a substring
    joined = " ".join(tokens)
    splits = []
    for title in episode_titles:
        if title in joined:
            splits.append(title)
    return splits


def _split_segments(title: str) -> list[str]:
    """Split a title into segments based on common delimiters."""
    if not title:
        return []
    # First, split on common explicit delimiters: "and", "&", two+ spaces
    segments = re.split(r"\s+and\s+|\s*&\s*|  +", title, flags=re.IGNORECASE)
    segments = [s.strip(" -_") for s in segments if s.strip(" -_")]

    # If that produced more than one segment we're done.
    if len(segments) > 1:
        return segments

    # Heuristic fallback: if the first word appears again later in the string,
    # treat the second occurrence as the boundary between segments.
    tokens = title.split()
    if tokens:
        first = tokens[0]
        try:
            idx = tokens.index(first, 1)
            seg1 = " ".join(tokens[:idx]).strip(" -_")
            seg2 = " ".join(tokens[idx:]).strip(" -_")
            if seg1 and seg2:
                return [seg1, seg2]
        except ValueError:
            pass

    # Fallback: return the original title as a single segment
    return segments or [title.strip()]
