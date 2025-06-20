"""Unit tests for namegnome.core.tv.matching._find_best_episode_match."""

from namegnome.core.tv.matching import _find_best_episode_match

EPISODES = [
    {"title": "Pups Save A Train", "episode": 1},
    {"title": "Pups Save The Sea Turtles", "episode": 2},
]


def test_exact_match_returns_100():
    seg = "Pups Save A Train"
    title, score, ep = _find_best_episode_match(seg, EPISODES)
    assert title == "Pups Save A Train"
    assert score == 100.0
    assert ep == EPISODES[0]


def test_fuzzy_match_returns_best_match():
    seg = "pups save train"  # missing articles
    title, score, ep = _find_best_episode_match(seg, EPISODES)
    assert title == "Pups Save A Train"
    assert score > 60  # fuzzy ratio should be decent
    assert ep == EPISODES[0]
