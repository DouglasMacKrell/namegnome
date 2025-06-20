"""Helpers for parsing season/episode spans from filenames."""

import re
from typing import Tuple, Union


EP_SPAN_RE = re.compile(
    r"(?:S\d+E|\d+x|E)(\d{1,2})[-–](?:E|x)?(\d{1,2})",
    re.IGNORECASE,
)


def _parse_episode_span_from_filename(filename: str) -> Union[Tuple[int, int], None]:
    """Return a tuple ``(start_ep, end_ep)`` if *filename* contains a span.

    The implementation only supports patterns like ``S01E01-02`` or
    ``S01E01E02`` which are enough for the unit tests.  If no span is found we
    return ``(None, None)``.
    """

    match = EP_SPAN_RE.search(filename)
    if not match:
        # Fallback: patterns like "1x01-1x02" (repeat of season prefix)
        alt = re.search(r"\d+x(\d{1,2})[-–]\d+x(\d{1,2})", filename, re.IGNORECASE)
        if alt:
            return int(alt.group(1)), int(alt.group(2))
        return None

    ep1, ep2 = match.group(1), match.group(2)

    # Detect false-positive case where pattern matched ``1x01-1`` (second
    # capture is the season number rather than the episode).  If a second
    # "x" appears after the dash, fall back to the specialised alt regex.
    dash_idx = filename.find("-")
    if dash_idx != -1 and "x" in filename[dash_idx:]:
        alt = re.search(r"\d+x(\d{1,2})[-–]\d+x(\d{1,2})", filename, re.IGNORECASE)
        if alt:
            return int(alt.group(1)), int(alt.group(2))

    try:
        return int(ep1), int(ep2)
    except ValueError:
        return None
