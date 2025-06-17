"""TV-specific RuleSetConfig for TV planning and matching logic."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TVRuleSetConfig:
    show_name: Optional[str] = None
    season: Optional[int] = None
    anthology: bool = False
    adjust_episodes: bool = False
    verify: bool = False
    llm_model: Optional[str] = None
    strict_directory_structure: bool = True
