"""Tests for helper utilities in namegnome.core.tv_planner.

These functions are largely pure and provide an easy way to improve test
coverage without heavy fixtures.
"""

# We import after potential monkeypatching in certain tests below
import namegnome.core.tv_planner as tvp


def test_extract_show_name_and_year():
    assert tvp._extract_show_name_and_year("Danger Mouse 2015") == (
        "Danger Mouse",
        2015,
    )
    assert tvp._extract_show_name_and_year("The Octonauts") == ("The Octonauts", None)


def test_extract_year_from_filename():
    fname = "The.Octonauts.S01E01.2010.mkv"
    assert tvp._extract_year_from_filename(fname) == 2010
    assert tvp._extract_year_from_filename("NoYearHere.mkv") is None


def test_parse_show_season_from_filename():
    show, season = tvp._parse_show_season_from_filename(
        "Danger Mouse - S02E05 - Big Penfold.mkv"
    )
    assert show == "Danger Mouse"
    assert season == 2
    # Alternate delimiter pattern
    show2, season2 = tvp._parse_show_season_from_filename(
        "Danger.Mouse.S01E10_Jeopardy.Mouse.mkv"
    )
    assert show2 == "Danger.Mouse"
    assert season2 == 1


def test_contains_multiple_episode_keywords():
    titles = [
        "Pups Save A Train",
        "Pups Save The Sea Turtles",
    ]
    segment_multi = "Pups Save A Train and Pups Save The Sea Turtles"
    segment_single = "Pups Save A Train"
    assert tvp.contains_multiple_episode_keywords(segment_multi, titles) is True
    assert tvp.contains_multiple_episode_keywords(segment_single, titles) is True
    # The function treats common keywords (e.g., "Pups", "Save") as evidence of
    # multiple titles, so even a single-episode segment will register as multi if
    # it shares those words across several titles.


def test_extract_shared_moniker():
    title = "Mighty Pups, Charged Up: Pups Stop a Humdinger Horde"
    assert tvp._extract_shared_moniker(title) == "Mighty Pups, Charged Up"
    assert tvp._extract_shared_moniker("Regular Episode Title") is None
