"""Rich diff renderer for rename plans."""

from rich.console import Console
from rich.style import Style
from rich.table import Table

from namegnome.models.core import PlanStatus, RenamePlan


def render_diff(plan: RenamePlan, console: Console | None = None) -> None:
    """Render a rename plan as a rich diff table.

    Args:
        plan: The rename plan to render.
        console: Optional console instance to use for output.
    """
    if console is None:
        console = Console()

    if console.no_color:
        # Plain text output for no-color mode
        print("Rename Plan")
        print()
        print(
            "Status         Source                     Destination                Reason"
        )
        print("-" * 80)
        for item in plan.items:
            print(
                f"{item.status.value:<12} {str(item.source):<25} "
                f"{str(item.destination) if item.destination else '':<25} "
                f"{item.reason or ''}"
            )
        print("-" * 80)
        total_items = len(plan.items)
        conflicts = sum(1 for item in plan.items if item.status == PlanStatus.CONFLICT)
        print(f"Total: {total_items} | Conflicts: {conflicts}")
        return

    # Create the table for color mode
    table = Table(
        title="Rename Plan",
        show_lines=True,
        box=None,
        header_style=Style(bold=True),
        title_style=Style(italic=True),
        caption_style=Style(dim=True, italic=True),
        expand=True,
    )
    table.add_column("Status")
    table.add_column("Source")
    table.add_column("Destination")
    table.add_column("Reason")

    # Add rows for each item
    for item in plan.items:
        # Determine status color
        status_color = {
            PlanStatus.PENDING: "\033[1;33m",  # Bright yellow
            PlanStatus.MOVED: "\033[1;32m",  # Bright green
            PlanStatus.SKIPPED: "\033[1;34m",  # Bright blue
            PlanStatus.CONFLICT: "\033[1;31m",  # Bright red
            PlanStatus.FAILED: "\033[1;31m",  # Bright red
            PlanStatus.MANUAL: "\033[1;91m",  # Bright red
        }.get(item.status, "\033[1;37m")  # Bright white

        # Add the row
        status_text = f"{status_color}{item.status.value}\033[0m"
        source_text = str(item.source)
        destination_text = str(item.destination) if item.destination else ""
        reason_text = item.reason or ""

        table.add_row(
            status_text,
            source_text,
            destination_text,
            reason_text,
        )

    # Add summary
    total_items = len(plan.items)
    conflicts = sum(1 for item in plan.items if item.status == PlanStatus.CONFLICT)
    table.caption = f"Total: {total_items} | Conflicts: {conflicts}"

    # Print the table
    console.print(table, soft_wrap=True)
