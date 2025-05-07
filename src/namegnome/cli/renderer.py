"""Rich diff renderer for rename plans."""

from rich.console import Console
from rich.table import Table

from namegnome.models.core import PlanStatus, RenamePlan


def render_diff(plan: RenamePlan, console: Console | None = None) -> None:
    """Render a rename plan as a rich diff table.

    Args:
        plan: The rename plan to render.
        console: Optional Console instance to use for rendering.
    """
    console = console or Console()

    table = Table(title=f"Rename Plan: {plan.id}")
    table.add_column("Status", style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Destination", style="green")
    table.add_column("Reason", style="yellow")

    # Map statuses to styles that match the expected ANSI color codes in tests
    status_styles = {
        PlanStatus.PENDING: "yellow bold",  # \033[1;33m
        PlanStatus.MOVED: "green",
        PlanStatus.SKIPPED: "yellow",
        PlanStatus.CONFLICT: "red bold",  # \033[1;31m
        PlanStatus.FAILED: "red bold",
        PlanStatus.MANUAL: "bright_red bold",  # \033[1;91m
    }

    for item in plan.items:
        status_style = status_styles.get(item.status, "white")
        table.add_row(
            item.status.value,
            str(item.source),
            str(item.destination),
            item.reason or "",
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
        console.print(f"Manual intervention required: {manual}", style="magenta")

    if failed > 0:
        console.print(f"Failed items: {failed}", style="red bold")
