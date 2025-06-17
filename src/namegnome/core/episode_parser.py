"""Parser module for extracting episode information from filenames."""

def _extract_show_season_year(media_file, config):
    """
    Extract the show name (with year removed), season, and year from a MediaFile and RuleSetConfig.
    Returns (show, season, year) tuple.
    """
    from namegnome.core.tv_planner import _extract_show_name, _extract_season, _extract_show_name_and_year
    show_name = _extract_show_name(media_file, config)
    season = _extract_season(media_file, config)
    show, year = _extract_show_name_and_year(show_name)
    return show, season, year
