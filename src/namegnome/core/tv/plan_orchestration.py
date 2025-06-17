"""TV Plan Orchestration: Entry point and conflict detection for TV rename planning.

This module provides the TV-specific entry point for building a rename plan from a scan result,
and robust conflict detection for planned destinations.
"""
from pathlib import Path
from namegnome.models.plan import RenamePlan, RenamePlanItem
from namegnome.core.tv.tv_plan_context import TVRenamePlanBuildContext, PlanContext


def create_tv_rename_plan(ctx: TVRenamePlanBuildContext, episode_list_cache: dict = None) -> RenamePlan:
    """
    Minimal stub: TV-specific entry point for building a rename plan from a scan result.
    Returns an empty RenamePlan for now (expand with real logic in next steps).
    """
    return RenamePlan(
        id=ctx.plan_id,
        items=[],
        platform=ctx.platform,
        root_dir=ctx.scan_result.root_dir,
    )


def add_plan_item_with_conflict_detection(item: RenamePlanItem, ctx: PlanContext, target_path: Path) -> None:
    """
    Minimal stub: Adds a plan item to the plan, checking for destination conflicts.
    If the target path is already planned, marks the item as manual/conflict.
    """
    key = target_path
    key_ci = str(target_path).lower()
    if key in ctx.destinations or key_ci in ctx.case_insensitive_destinations:
        item.manual = True
        item.manual_reason = "Destination conflict detected."
    ctx.plan.items.append(item)
    ctx.destinations[key] = item
    ctx.case_insensitive_destinations[key_ci] = item
