"""Episode Fetcher: Converts raw API responses into a refined episode list for matching."""
from typing import List, Dict, Any

def fetch_episode_list(show: str, season: int, year: int = None, provider: str = None) -> List[Dict[str, Any]]:
    """
    Minimal stub: Returns an empty list. In the real implementation, this would fetch and normalize episode data from a provider API.
    Args:
        show: The show name.
        season: The season number.
        year: Optional year for disambiguation.
        provider: Optional provider name (e.g., 'tvdb', 'tmdb').
    Returns:
        A list of dicts, each representing an episode (with at least 'season', 'episode', 'title').
    """
    return []
