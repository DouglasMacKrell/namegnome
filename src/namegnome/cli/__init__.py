"""Command-line interface for namegnome.

This package provides the Typer app and global console for all CLI commands and
user-facing output.

- app: The Typer application object, used by all CLI entrypoints and subcommands.
- console: Rich Console instance for consistent, styled output and logging.
- All CLI modules import app and console from this package to use rich for output,
  show pretty tracebacks, and provide a single CLI entrypoint for all commands.

Follows CLI UX guidelines from PLANNING.md: always use rich for output, show
pretty tracebacks, and provide a single CLI entrypoint for all commands.
"""

from collections.abc import Callable
from typing import Any, TypeVar

import typer
from rich.console import Console
from rich.traceback import install

# Install rich traceback handler for all CLI commands
install(show_locals=True)

# Reason: Global console object ensures all output is styled and consistent across
# commands (see PLANNING.md CLI UX guidelines).
console = Console()

# Reason: Importing app and console here allows all CLI modules and commands to avoid
# re-instantiation and ensure global options work as expected.
app = typer.Typer(
    name="namegnome",
    help="A tool to analyze, rename and reorganize media files for media servers.",
    add_completion=True,
)

F = TypeVar("F", bound=Callable[..., Any])


@app.callback()
def callback(
    ctx: typer.Context,  # noqa: D401 – Typer requires ctx param first
    no_rich: bool = typer.Option(
        False,
        "--no-rich",
        help=(
            "Disable Rich coloured output, spinners and progress bars. "
            "Can also be set with the NAMEGNOME_NO_RICH environment variable."
        ),
    ),
) -> None:
    """Top-level CLI callback adding global options.

    The *--no-rich* flag allows users to disable Rich output entirely. We
    implement it by setting the ``NAMEGNOME_NO_RICH`` environment variable so
    that downstream utilities (e.g. :pyclass:`~namegnome.cli.console.ConsoleManager`)
    can respond uniformly whether the flag is passed or the variable is set
    externally.
    """

    if no_rich:
        # Defer import to avoid cycles.
        import os

        os.environ["NAMEGNOME_NO_RICH"] = "1"


@app.command()
def version() -> None:
    """Show the version of namegnome."""
    from namegnome.__about__ import __version__

    console.print(f"NameGnome version: [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
