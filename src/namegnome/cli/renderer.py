"""Renderer for CLI output.

This module provides functions to render rename plans as rich tables in the CLI,
using color and style conventions for clear, user-friendly output.
- Uses Rich for all output, matching CLI UX guidelines from PLANNING.md.
- Status colors/styles are chosen to match both user expectations and test
  assertions (see tests/cli/test_renderer.py).
- Designed for extensibility: can be adapted for other output formats or
  additional summary info.

See README.md and PLANNING.md for CLI UX rationale and color conventions.
"""

from rich.console import Console
from rich.table import Table

from namegnome.models.core import PlanStatus
from namegnome.models.plan import RenamePlan


def render_diff(plan: RenamePlan, console: Console | None = None) -> None:
    """Render a rename plan as a rich diff table.

    Args:
        plan: The rename plan to render.
        console: Optional Console instance to use for rendering.

    Returns:
        None. Prints the table and summary to the console.
    """
    console = console or Console()

    table = Table(title=f"Rename Plan: {plan.id}")
    table.add_column("Status", style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Destination", style="green")
    table.add_column("Reason", style="yellow")

    # Reason: Status styles are chosen to match both user-facing color conventions
    # and test assertions (see test_renderer.py).
    status_styles = {
        PlanStatus.PENDING: "yellow bold",  # \033[1;33m
        PlanStatus.MOVED: "green bold",  # \033[1;32m
        PlanStatus.SKIPPED: "cyan",
        PlanStatus.CONFLICT: "red bold",
        PlanStatus.FAILED: "red",
        PlanStatus.MANUAL: "bright_red bold",  # Use bright red for manual
    }

    for item in plan.items:
        status_style = status_styles.get(item.status, "white")
        # Show manual_reason if present for manual items
        reason = (
            item.manual_reason
            if item.status == PlanStatus.MANUAL and item.manual_reason
            else item.reason or ""
        )
        table.add_row(
            item.status.value,
            str(item.source),
            str(item.destination),
            reason,
            style=status_style,
        )

    console.print(table)

    # Calculate counts for summary
    total = len(plan.items)
    conflicts = len([item for item in plan.items if item.status == PlanStatus.CONFLICT])
    manual = len([item for item in plan.items if item.status == PlanStatus.MANUAL])
    failed = len([item for item in plan.items if item.status == PlanStatus.FAILED])

    # Print summary in the expected format for the tests
    console.print(f"Total: {total} | Conflicts: {conflicts}")

    if manual > 0:
        console.print(
            f"Manual intervention required: {manual}", style="bright_red bold"
        )

    if failed > 0:
        console.print(f"Failed items: {failed}", style="red bold")


# TODO: NGN-204 - Add support for exporting diff tables to Markdown or HTML for
# reporting.
