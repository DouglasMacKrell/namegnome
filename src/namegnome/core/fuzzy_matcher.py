"""Fuzzy episode matcher for NameGnome.

Uses rapidfuzz to match episode titles to filename segments.
"""

import re
from collections import Counter
from typing import List, Tuple

from rapidfuzz import fuzz


def match_episodes(
    filename: str,
    episode_titles: List[str],
    threshold: int = 75,
    claimed_indices: set[int] = None,
) -> List[Tuple[str, float]]:
    """Fuzzy match episode titles to a filename using multiple metrics and rare word overlap.
    Prefer matches where all rare/unique words from the canonical title are present in the filename.
    Exclude claimed episodes from matching.
    Args:
        filename: The filename to match against.
        episode_titles: List of official episode titles.
        threshold: Minimum score (0-100) to consider a match.
        claimed_indices: Set of indices of already-claimed episodes (optional).
    Returns:
        List of (title, score) tuples for unclaimed episodes.
    """
    if claimed_indices is None:
        claimed_indices = set()
    word_counter = Counter()
    title_tokens = []
    for title in episode_titles:
        tokens = re.findall(r"\w+", title.lower())
        title_tokens.append(tokens)
        word_counter.update(tokens)
    def get_rare_words(tokens):
        return [w for w in tokens if word_counter[w] == 1 and len(w) > 2]
    filename_tokens = set(re.findall(r"\w+", filename.lower()))
    results = []
    # Substring-based unique-word anchoring: if any word in the filename is a unique substring in any episode title, always match that episode
    filename_words = set(re.findall(r"\w+", filename.lower()))
    substring_unique_matches = []
    for idx, (title, tokens) in enumerate(zip(episode_titles, title_tokens)):
        if idx in claimed_indices:
            continue
        for fname_word in filename_words:
            # Check if fname_word is a substring of any token in the title
            matches = [t for t in tokens if fname_word in t]
            if matches:
                # Is this substring unique across all titles?
                count = 0
                for other_tokens in title_tokens:
                    if any(fname_word in t for t in other_tokens):
                        count += 1
                if count == 1:
                    substring_unique_matches.append((title, 100.0, idx))
                    break
    if substring_unique_matches:
        substring_unique_matches.sort(key=lambda x: x[2])  # Prefer lowest index (lowest episode number)
        return [(title, score) for title, score, idx in substring_unique_matches]
    # Aggressive unique-word anchoring: if any rare/unique word from a title is present in the filename and that episode is unclaimed, always match it regardless of fuzzy score
    unique_word_matches = []
    for idx, (title, tokens) in enumerate(zip(episode_titles, title_tokens)):
        if idx in claimed_indices:
            continue
        score = fuzz.token_set_ratio(filename, title)
        sort_score = fuzz.token_sort_ratio(filename, title)
        partial_score = fuzz.partial_ratio(filename, title)
        best_score = max(score, sort_score, partial_score)
        rare_words = set(get_rare_words(tokens))
        rare_overlap = rare_words.issubset(filename_tokens) if rare_words else False
        if rare_overlap and best_score >= (threshold - 20):
            results.append((title, best_score + 15))
            continue
        if best_score >= threshold:
            results.append((title, best_score))
            continue
        if rare_words and rare_words & filename_tokens:
            unique_word_matches.append((title, best_score, idx))
    if unique_word_matches:
        # Always return unique-word matches as top priority
        unique_word_matches.sort(key=lambda x: x[2])  # Prefer lowest index (lowest episode number)
        return [(title, score) for title, score, idx in unique_word_matches]
    results.sort(key=lambda x: x[1], reverse=True)
    return results
