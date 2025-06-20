"""Stub for TV matching logic."""

from difflib import SequenceMatcher


def _find_best_episode_match(segment, episode_list):
    """
    Find the best matching episode title for a segment using SequenceMatcher.
    Supports both TVEpisode models and dicts for compatibility.
    """
    segment_lower = segment.lower().strip()
    for ep in episode_list:
        if hasattr(ep, "title"):
            title = ep.title
        elif isinstance(ep, dict):
            title = ep.get("title")
        else:
            continue
        if title and segment_lower == title.lower().strip():
            return title, 100.0, ep
    # Fallback to fuzzy match
    best = None
    best_ratio = 0.0
    best_ep = None
    for ep in episode_list:
        if hasattr(ep, "title"):
            title = ep.title
        elif isinstance(ep, dict):
            title = ep.get("title")
        else:
            continue
        ratio = SequenceMatcher(None, segment_lower, title.lower().strip()).ratio()
        if ratio > best_ratio:
            best = title
            best_ratio = ratio
            best_ep = ep
    if best and best_ratio >= 0.6:
        return best, best_ratio * 100, best_ep
    return None, 0, None
