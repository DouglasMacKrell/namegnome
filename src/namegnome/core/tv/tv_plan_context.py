from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from namegnome.models.core import ScanResult
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
class PlanContext:
    """
    TV-specific context object holding plan and destination tracking for rename planning.
    """
    plan: RenamePlan
    destinations: dict[Path, RenamePlanItem]
    case_insensitive_destinations: dict[str, RenamePlanItem]

class AnthologyContext:
    pass

class AnthologyPlanItemContext:
    pass

class PlanItemContext:
    pass 