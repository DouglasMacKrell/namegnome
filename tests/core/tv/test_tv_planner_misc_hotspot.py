"""Miscellaneous hotspot tests for tv_planner and core.planner helpers.

These tests do not need heavy fixtures – they exercise pure functions that
still have large uncovered regions.
"""

from types import SimpleNamespace
from pathlib import Path
from datetime import datetime

from namegnome.core import tv_planner as tvp
from namegnome.core.planner import _extract_unique_verbs_phrases
from namegnome.core.tv.utils import sanitize_title_tv
from namegnome.models.core import MediaFile, MediaType


# ---------------------------------------------------------------------------
# _extract_unique_verbs_phrases (core.planner)
# ---------------------------------------------------------------------------

def test_extract_unique_verbs_phrases():
    title = "The Pups Save The Day"
    verbs = _extract_unique_verbs_phrases(title)
    # Stop-words like "the" should be gone; keywords retained (min length 3)
    assert "the" not in verbs
    assert {"pups", "save"}.issubset(verbs)


# ---------------------------------------------------------------------------
# _anthology_single_segment_fallback (tv_planner)
# ---------------------------------------------------------------------------

def test_anthology_single_segment_fallback_match():
    segment = "Pups Save A Train"
    episode_titles = [segment, "Big Head Awakens"]
    sanitized_titles = [sanitize_title_tv(t) for t in episode_titles]
    episode_list = [
        {"title": segment, "episode": 1},
        {"title": "Big Head Awakens", "episode": 2},
    ]

    matched_eps, matched_titles = tvp._anthology_single_segment_fallback(  # type: ignore[attr-defined]
        segment,
        episode_titles,
        sanitized_titles,
        episode_list,
    )

    # Should return the single matching entry
    assert len(matched_eps) == 1 and len(matched_titles) == 1
    assert matched_titles[0] == segment
    assert matched_eps[0]["episode"] == 1


# ---------------------------------------------------------------------------
# _handle_normal_matching (tv_planner)
# ---------------------------------------------------------------------------

def test_handle_normal_matching_updates_media_file(tmp_path):
    # Prepare dummy media file and context
    fname = "Show - Big Head Awakens.mkv"
    fpath = tmp_path / fname
    fpath.touch()

    # Use a simple namespace to avoid pydantic field restrictions
    mfile = SimpleNamespace(path=fpath, media_type=MediaType.TV)

    episode_list = [
        {"title": "Big Head Awakens", "episode": 7},
        {"title": "Other", "episode": 8},
    ]

    # Dummy ctx/plan_ctx – function under test ignores them internally
    dummy_ctx = SimpleNamespace(progress_callback=None)
    dummy_plan_ctx = SimpleNamespace()

    found = tvp._handle_normal_matching(  # type: ignore[attr-defined]
        mfile,
        dummy_ctx,  # type: ignore[arg-type]
        dummy_plan_ctx,  # type: ignore[arg-type]
        episode_list,
        False,
    )

    assert found is True
    assert getattr(mfile, "episode", None) == 7
    assert "big head awakens" in getattr(mfile, "episode_title", "").lower()


# ---------------------------------------------------------------------------
# _extract_shared_moniker (tv_planner)
# ---------------------------------------------------------------------------

def test_extract_shared_moniker():
    title = "Mighty Pups, Charged Up: Pups Stop a Humdinger Horde"
    assert tvp._extract_shared_moniker(title) == "Mighty Pups, Charged Up"

    # No shared moniker → None
    assert tvp._extract_shared_moniker("Generic Episode Title") is None 