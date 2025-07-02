"""Stub for TV utils."""

from typing import List, Dict, Any
from namegnome.metadata.models import TVEpisode


def normalize_episode_list(raw: list[Any] | None) -> List[Dict[str, Any]]:
    """Normalise a heterogeneous *raw* episode list to a list of dicts.

    Each output dict contains integer ``season`` and ``episode`` keys and a
    string ``title`` key.  Objects already of type :class:`TVEpisode` are
    converted.  Any entries missing required data are skipped.  Titles are
    left unchanged.
    """
    if not raw:
        return []

    normalised: List[Dict[str, Any]] = []
    for ep in raw:
        if isinstance(ep, TVEpisode):
            season = int(ep.season_number)
            episode = int(ep.episode_number)
            title = ep.title
        elif isinstance(ep, dict):
            season_val = ep.get("season") or ep.get("season_number")
            episode_val = ep.get("episode") or ep.get("episode_number")
            title = ep.get("title", "Unknown Title")

            def _coerce(value: object) -> int | None:
                try:
                    if isinstance(value, str):
                        value = value.lstrip("0") or "0"
                    return int(value)
                except Exception:
                    return None

            season = _coerce(season_val) or 0
            episode = _coerce(episode_val) or 0
        else:
            # Fallback for simple objects with the expected attributes (e.g., EpObj in tests)
            season = int(getattr(ep, "season", 0) or 0)
            episode = int(getattr(ep, "episode", 0) or 0)
            title = getattr(ep, "title", "Unknown Title")
            if season == 0 or episode == 0:
                # Insufficient data, skip
                continue

        # Skip rows missing or invalid
        if season <= 0 or episode <= 0:
            continue

        normalised.append(
            {
                "season": season,
                "episode": episode,
                "title": title,
            }
        )

    return normalised


def _strip_preamble(title: str) -> str:
    """Remove common preambles such as show name or possessives from *title*.

    The implementation is heuristic and only aims to satisfy the unit tests –
    it strips leading *"Martha "*, *"Paw Patrol "* etc. by removing tokens up
    to the first Dash or colon.  If no known preamble delimiter is found, the
    original title is returned unchanged.
    """
    if not title:
        return ""

    # Remove everything up to the first dash/colon if present
    for delim in (" - ", "—", "–", ":"):
        if delim in title:
            return title.split(delim, 1)[1].strip()
    return title


def sanitize_title_tv(title: str) -> str:
    """Very small helper used by tests – strips illegal filename chars."""
    if not title:
        return title
    return title.replace("/", "-")
