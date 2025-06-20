"""Stub for TV plan helpers."""

from typing import List, Tuple
from difflib import SequenceMatcher

from namegnome.metadata.models import TVEpisode


def _tokenise(text: str) -> List[str]:
    """Very small tokenizer that lowercases and splits on whitespace."""
    return text.lower().replace("&", " and ").split()


def _find_best_episode_match(
    segment: str, episode_list: List[TVEpisode]
) -> Tuple[str | None, float, TVEpisode | None]:
    """Return the title from *episode_list* that best matches *segment*.

    The function is intentionally simple: we compute a SequenceMatcher ratio
    between the segment and each episode title (case-insensitive) and return
    the highest scoring episode along with the score.  If nothing scores above
    0.5 we return ``None``.
    """

    best_score: float = 0.0
    best_episode: TVEpisode | None = None
    best_title: str | None = None

    for ep in episode_list:
        score = SequenceMatcher(None, segment.lower(), ep.title.lower()).ratio() * 100
        if score > best_score:
            best_score = score
            best_episode = ep
            best_title = ep.title

    if best_score < 50:
        return None, best_score, None
    return best_title, best_score, best_episode


def contains_multiple_episode_keywords(segment: str, episode_titles: List[str]) -> bool:
    """Return *True* if *segment* contains *two or more* distinct episode titles.

    The check is case-insensitive and based on simple substring matching.
    """

    cnt = 0
    lower_seg = segment.lower()
    for title in episode_titles:
        if title.lower() in lower_seg:
            cnt += 1
        if cnt >= 2:
            return True
    return False
