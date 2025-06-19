"""Parser module for extracting episode information from filenames."""

from typing import Tuple, Optional

from namegnome.models.core import MediaFile
from namegnome.rules.base import RuleSetConfig


def _extract_show_season_year(
    media_file: MediaFile,
    config: RuleSetConfig,
) -> Tuple[str | None, Optional[int], Optional[int]]:
    """
    Extract the show name (with year removed), season, and year from a MediaFile and RuleSetConfig.
    Returns (show, season, year) tuple.
    """
    from namegnome.core.tv_planner import (
        _extract_show_name,
        _extract_season,
        _extract_show_name_and_year,
    )

    show_name = _extract_show_name(media_file, config)
    season = _extract_season(media_file, config)
    show, year = _extract_show_name_and_year(show_name or "")
    return show, season, year
