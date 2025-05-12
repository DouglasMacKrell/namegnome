"""This module provides functionality to revert a RenamePlan transactionally.

- Moves files back to their original locations, verifies hashes if requested,
  and updates statuses.
- See TASK.md Sprint 1.2 for requirements and test cases.
"""

import json
from pathlib import Path
from typing import Callable, Optional

from rich.console import Console

from namegnome.fs.operations import atomic_move
from namegnome.models.core import PlanStatus
from namegnome.models.plan import RenamePlan
from namegnome.utils.hash import sha256sum


def undo_plan(
    plan_path: Path, log_callback: Optional[Callable[[str], None]] = None
) -> None:
    """Undo a rename plan transactionally.

    Args:
        plan_path (Path): Path to the plan JSON file.
        log_callback (Optional[Callable[[str], None]]): Callback for logging.

    Raises:
        NotImplementedError: Stub for TDD.
    """
    console = Console()
    if log_callback is None:

        def log_callback(msg: str) -> None:
            pass

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)
    plan = RenamePlan.model_validate(plan_data)
    for item in plan.items:
        # Check if source already exists
        if item.source.exists():
            console.log(
                f"[red]Cannot restore: source file already exists: {item.source}[/red]"
            )
            raise SystemExit(1)
        # Check if destination exists
        if not item.destination.exists():
            console.log(
                f"[red]Cannot restore: destination file does not exist: "
                f"{item.destination}[/red]"
            )
            raise SystemExit(1)
        log_callback(f"Restoring {item.destination} -> {item.source}")
        # Move file from destination back to source
        atomic_move(item.destination, item.source)
        # Verify hash matches original
        if item.media_file.hash:
            restored_hash = sha256sum(item.source)
            if restored_hash != item.media_file.hash:
                item.status = PlanStatus.FAILED
            else:
                item.status = PlanStatus.MOVED
