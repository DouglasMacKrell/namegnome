"""Command-line interface for namegnome."""


import typer
from rich.console import Console
from rich.traceback import install

# Install rich traceback handler
install(show_locals=True)

# Create console for rich output
console = Console()

# Create the Typer app
app = typer.Typer(
    name="namegnome",
    help="A tool to analyze, rename and reorganize media files for media servers.",
    add_completion=True,
)


@app.callback()
def callback() -> None:
    """NameGnome - Media File Organizer and Renamer.

    Analyzes, renames and reorganizes media files for Plex, Jellyfin, Emby and other
    media servers.
    """
    pass


@app.command()
def version() -> None:
    """Show the version of namegnome."""
    from namegnome.__about__ import __version__

    console.print(f"NameGnome version: [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
