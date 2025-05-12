"""Apply engine for rename plans.

This module provides functionality to execute a RenamePlan transactionally
with automatic rollback.
- Moves files according to the plan, verifies hashes if requested, and updates
  item statuses.
- On failure, rolls back all successful moves.
- See TASK.md Sprint 1.2 for requirements and test cases.
"""

import time as time_mod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from namegnome.fs.operations import atomic_move
from namegnome.models.core import PlanStatus
from namegnome.models.plan import RenamePlan, RenamePlanItem


@dataclass
class ApplyResult:
    """Result of applying a rename plan."""

    success: bool
    failures: List[RenamePlanItem] = field(default_factory=list)
    duration: float = 0.0
    moved: int = 0
    skipped: int = 0
    failed: int = 0


def apply_plan(
    plan: RenamePlan, verify_hash: bool = False, skip_identical: bool = False
) -> ApplyResult:
    """Apply a rename plan transactionally, verifying hashes if requested.

    Args:
        plan: The RenamePlan to execute.
        verify_hash: Whether to verify file hashes after move.
        skip_identical: Whether to skip moves if destination exists and hashes match.

    Returns:
        ApplyResult: Result of the apply operation.
    """
    start = time_mod.time()
    moved = 0
    skipped = 0
    failed = 0
    failures = []
    rollback_stack: List[Tuple[Path, Path]] = []
    error_occurred = False
    for item in plan.items:
        try:
            # Skip identical logic
            if skip_identical and item.destination.exists() and item.media_file.hash:
                from namegnome.utils.hash import sha256sum

                dst_hash = sha256sum(item.destination)
                if dst_hash == item.media_file.hash:
                    item.status = PlanStatus.SKIPPED
                    skipped += 1
                    continue
            atomic_move(item.source, item.destination)
            rollback_stack.append((item.source, item.destination))
            # Verify hash if requested
            if verify_hash and item.media_file.hash:
                from namegnome.utils.hash import sha256sum

                dst_hash = sha256sum(item.destination)
                if dst_hash != item.media_file.hash:
                    item.status = PlanStatus.FAILED
                    failed += 1
                    failures.append(item)
                    error_occurred = True
                    break
            item.status = PlanStatus.MOVED
            moved += 1
        except Exception:
            item.status = PlanStatus.FAILED
            failed += 1
            failures.append(item)
            error_occurred = True
            break
    # Rollback if error occurred
    if error_occurred and rollback_stack:
        for src, dst in reversed(rollback_stack):
            try:
                atomic_move(dst, src)
            except Exception:
                pass  # If rollback fails, continue
    duration = time_mod.time() - start
    success = failed == 0
    return ApplyResult(
        success=success,
        failures=failures,
        duration=duration,
        moved=moved,
        skipped=skipped,
        failed=failed,
    )


__all__ = ["apply_plan", "ApplyResult", "atomic_move"]
