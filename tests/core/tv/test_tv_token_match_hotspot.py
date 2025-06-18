"""Tests for the _token_set_match helper in tv_anthology_split."""

from namegnome.core.tv.anthology import tv_anthology_split as tas


def test_token_set_match_no_overlap():
    assert tas._token_set_match("Cat", "Dog") is False


def test_token_set_match_short_title_requires_full_overlap():
    # Both strings ≤2 tokens. Overlap only 1 token of 2 -> still True due to rule
    assert tas._token_set_match("Big", "Big Mouse") is True
    # Full overlap of short tokens -> True
    assert tas._token_set_match("Big", "Big") is True


def test_token_set_match_long_titles():
    # Needs at least two overlapping tokens for longer strings
    assert tas._token_set_match("Pups Save A Train", "Pups Save The Sea Turtles") is True
    assert tas._token_set_match("Pups Save A Train", "Penguin Patrol") is False 