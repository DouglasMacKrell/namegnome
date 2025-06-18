"""Tests for namegnome.core.fuzzy_matcher.match_episodes.

Focused on the three main matching pathways: unique-substring anchoring, rare-word overlap, and exclusion via claimed_indices.
"""

from namegnome.core.fuzzy_matcher import match_episodes

EPISODE_TITLES = [
    "Pups Save the Train",
    "Big Head Awakens",
    "The Spy Who Came In With A Cold",
]


def test_unique_substring_match():
    """A word unique to a single title should force a 100-score match."""
    filename = "Danger Mouse - Big Head Awakens.mkv"
    matches = match_episodes(filename, EPISODE_TITLES)
    # First (and only) match should be the correct title with a high score
    assert matches and matches[0][0] == "Big Head Awakens"
    assert matches[0][1] >= 90  # close to perfect


def test_claimed_indices_excluded():
    """If the best match has already been claimed, no match should be returned."""
    filename = "Danger Mouse - Big Head Awakens.mkv"
    # Mark index 1 ("Big Head Awakens") as already claimed
    matches = match_episodes(filename, EPISODE_TITLES, claimed_indices={1})
    # With the unique best match excluded, the function should yield no candidates
    assert matches == []


def test_rare_word_overlap():
    """Rare/unique words appearing in the filename should boost the score and return a match."""
    filename = "The-Cold-Adventures.mkv"  # contains rare word "Cold"
    matches = match_episodes(filename, EPISODE_TITLES, threshold=50)
    # Expect the episode containing the rare word "Cold" to be matched
    assert matches and matches[0][0] == "The Spy Who Came In With A Cold"


# A title list designed to exercise the unique_word_matches fallback branch
RARE_TITLES = [
    "Humdinger Horde Havoc",  # Unique word "Humdinger"
    "Generic Adventure",
]


def test_unique_word_fallback_matches_low_fuzzy():
    """When a rare word is present but fuzzy score is below threshold, the fallback branch should still match."""
    filename = "Mighty Humdinger Chaos.mkv"
    # Use a high threshold so that the fuzzy score is *not* high enough, forcing the unique-word fallback
    matches = match_episodes(filename, RARE_TITLES, threshold=90)
    assert matches and matches[0][0] == "Humdinger Horde Havoc" 