"""Fuzzy episode matcher for NameGnome.

Uses rapidfuzz to match episode titles to filename segments.
"""

import re
from collections import Counter
from typing import List, Tuple

from rapidfuzz import fuzz


def calculate_show_confidence(input_name: str, canonical_name: str) -> float:
    """Calculate confidence score for show name matching.

    This function provides confidence scoring based on:
    - Exact string matching
    - Case-insensitive matching
    - Token-based similarity
    - Handling of common variations (like "The" prefix)

    Args:
        input_name: Show name extracted from filename
        canonical_name: Official show name from metadata provider

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if not input_name or not canonical_name:
        return 0.0

    # Normalize both names for comparison
    input_norm = input_name.strip().lower()
    canonical_norm = canonical_name.strip().lower()

    # Perfect match gets highest confidence
    if input_norm == canonical_norm:
        return 1.0

    # Case-insensitive exact match
    if input_name.strip().lower() == canonical_name.strip().lower():
        return 0.98

    # Handle "The" prefix variations
    input_no_the = re.sub(r"^the\s+", "", input_norm)
    canonical_no_the = re.sub(r"^the\s+", "", canonical_norm)

    if input_no_the == canonical_no_the:
        return 0.95

    if input_norm == canonical_no_the or input_no_the == canonical_norm:
        return 0.90

    # Analyze words for better matching
    input_words = set(re.findall(r"\w+", input_norm))
    canonical_words = set(re.findall(r"\w+", canonical_norm))

    # Use rapidfuzz for fuzzy matching
    token_set_score = fuzz.token_set_ratio(input_norm, canonical_norm) / 100.0
    token_sort_score = fuzz.token_sort_ratio(input_norm, canonical_norm) / 100.0
    partial_score = fuzz.partial_ratio(input_norm, canonical_norm) / 100.0

    # Be conservative about token_set when input is much smaller than canonical
    # token_set gives high scores for subset matches, which we don't want for single words
    if len(input_words) < len(canonical_words):
        # Penalize token_set score based on word count ratio
        word_ratio = len(input_words) / len(canonical_words)
        token_set_score = (
            token_set_score * word_ratio * 0.8
        )  # Extra penalty for subset matching

    # Start with the best conservative fuzzy score
    best_fuzzy_score = max(token_sort_score, token_set_score)

    # Only use partial score if input is substantial (avoid high scores for short substrings)
    if (
        len(input_norm) >= len(canonical_norm) * 0.6
    ):  # Input should be at least 60% the length
        best_fuzzy_score = max(best_fuzzy_score, partial_score)
    else:
        # For short inputs, heavily penalize partial ratio to avoid substring false positives
        penalized_partial = partial_score * (len(input_norm) / len(canonical_norm))
        best_fuzzy_score = max(best_fuzzy_score, penalized_partial)

    # Word overlap boost - but be conservative
    if input_words and canonical_words:
        word_overlap = len(input_words & canonical_words) / len(canonical_words)
        # Only boost if we have multiple words AND substantial overlap, or perfect single word match with multiple canonical words
        if len(input_words) > 1 and word_overlap > 0.5:
            # Multiple word input with good overlap
            best_fuzzy_score = max(best_fuzzy_score, word_overlap * 0.85)
        elif len(input_words) == 1 and len(canonical_words) > 1 and word_overlap == 1.0:
            # Single perfect word match - don't boost too much for subset matching
            best_fuzzy_score = max(
                best_fuzzy_score, 0.4
            )  # Cap at 40% for single word matches
        elif word_overlap == 0.0:
            # No word overlap at all - heavily penalize
            best_fuzzy_score = best_fuzzy_score * 0.3  # Reduce by 70% for zero overlap

    # Special handling for perfect word match but different order
    if (
        input_words
        and canonical_words
        and len(input_words) == len(canonical_words)
        and input_words == canonical_words
        and input_norm != canonical_norm
    ):
        # Same words, different order - cap at 0.6 per test requirement
        best_fuzzy_score = min(best_fuzzy_score, 0.6)

    # Additional penalty for very different lengths with poor fuzzy scores
    length_ratio = min(len(input_norm), len(canonical_norm)) / max(
        len(input_norm), len(canonical_norm)
    )
    if best_fuzzy_score < 0.5 and length_ratio < 0.6:
        best_fuzzy_score = (
            best_fuzzy_score * 0.5
        )  # Additional penalty for very different lengths

    # Ensure reasonable bounds
    best_fuzzy_score = max(0.0, min(1.0, best_fuzzy_score))

    # Handle year variations (e.g., "Danger Mouse 2015" vs "Danger Mouse")
    year_pattern = r"\s*\d{4}\s*"
    input_no_year = re.sub(year_pattern, " ", input_norm).strip()
    canonical_no_year = re.sub(year_pattern, " ", canonical_norm).strip()

    if (
        input_no_year == canonical_no_year
        and abs(len(input_norm) - len(canonical_norm)) <= 6
    ):
        return max(best_fuzzy_score, 0.85)

    return best_fuzzy_score


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
        substring_unique_matches.sort(
            key=lambda x: x[2]
        )  # Prefer lowest index (lowest episode number)
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
        unique_word_matches.sort(
            key=lambda x: x[2]
        )  # Prefer lowest index (lowest episode number)
        return [(title, score) for title, score, idx in unique_word_matches]
    results.sort(key=lambda x: x[1], reverse=True)
    return results
