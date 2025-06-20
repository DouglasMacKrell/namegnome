from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from namegnome.models.core import MediaFile, ScanResult
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.rules.base import RuleSet, RuleSetConfig


@dataclass
class TVRenamePlanBuildContext:
    """
    TV-specific context for building a rename plan, grouping all required arguments.
    """

    scan_result: ScanResult
    rule_set: RuleSet
    plan_id: str
    platform: str
    config: Optional[RuleSetConfig] = None
    progress_callback: Optional[Callable[[str], None]] = None


@dataclass
class TVPlanContext:
    """
    TV-specific context object holding plan and destination tracking for rename planning.
    """

    plan: RenamePlan
    destinations: dict[Path, RenamePlanItem]
    case_insensitive_destinations: dict[str, RenamePlanItem]


@dataclass
class AnthologyContext:  # noqa: D101 – holds per-show context during anthology planning
    media_file: MediaFile
    ctx: TVRenamePlanBuildContext
    plan_ctx: TVPlanContext
    show: str
    season: int | None
    year: int | None
    episode_list: list
    episode_list_cache: dict
    key: tuple[str, int | None, int | None]


class _PlaceholderAnthologyPlanItemContext: ...


# Revised: fully-typed dataclass so mypy recognises attributes populated by
# tv_planner logic. These contexts are lightweight value objects that carry
# commonly-accessed fields during planning helper calls. Only the attributes
# actually used by the planner are included for now; feel free to extend as
# new data is required.


@dataclass
class AnthologyPlanItemContext:  # noqa: D101 – docstring inherited from module
    media_file: MediaFile
    rule_set: RuleSet
    config: Optional[RuleSetConfig]
    ctx: TVRenamePlanBuildContext
    season: int | None
    episode_list: list
    orig_stem: str


# Core per-item context (non-anthology) -------------------------------------------------


@dataclass
class PlanItemContext:  # noqa: D101 – docstring inherited from module
    media_file: MediaFile
    rule_set: RuleSet
    config: Optional[RuleSetConfig]
    ctx: TVRenamePlanBuildContext
    unique_episodes: list
    unique_titles: list
    season: int | None
    episode_list: list
    orig_stem: str


# Backward-compatibility alias until all tests and callers migrate
PlanContext = TVPlanContext

# (Placeholder renamed to avoid duplicate definition)
_DeprecatedAnthologyPlanItemContext = _PlaceholderAnthologyPlanItemContext
