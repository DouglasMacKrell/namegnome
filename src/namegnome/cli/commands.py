"""CLI commands for namegnome."""

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install as install_traceback

from namegnome.cli.renderer import render_diff
from namegnome.core.planner import create_rename_plan
from namegnome.core.scanner import scan_directory
from namegnome.models.core import MediaType
from namegnome.rules.plex import PlexRuleSet
from namegnome.utils.json import DateTimeEncoder

# Install rich traceback handler
install_traceback(show_locals=True)

app = typer.Typer()
console = Console()


def validate_media_type(value: str) -> MediaType:
    """Validate and convert a string to a MediaType.

    Args:
        value: The string value to convert.

    Returns:
        The corresponding MediaType enum value.

    Raises:
        typer.BadParameter: If the value is not a valid media type.
    """
    try:
        return MediaType(value.lower())
    except ValueError:
        valid_types = [t.value for t in MediaType if t != MediaType.UNKNOWN]
        raise typer.BadParameter(
            f"Invalid media type. Must be one of: {', '.join(valid_types)}"
        )


def scan_command(
    root: Path,
    media_type: list[str] = [],
    platform: str = "plex",
    show_name: str | None = None,
    movie_year: int | None = None,
    anthology: bool = False,
    adjust_episodes: bool = False,
    verify: bool = False,
    json_output: bool = False,
    llm_model: str | None = None,
    no_color: bool = False,
    strict_directory_structure: bool = True,
) -> int:
    """Scan a directory for media files and generate a rename plan."""
    # Create console with appropriate color settings
    console = Console(no_color=no_color)

    # Check if at least one media type is specified
    if not media_type:
        console.print("[red]Error: At least one media type must be specified[/red]")
        return 1

    # Convert string media types to MediaType enum values
    try:
        media_types = [validate_media_type(mt) for mt in media_type]
    except typer.BadParameter as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

    try:
        # Create a progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Scan directory
            progress.add_task("Scanning directory...", total=None)
            try:
                scan_result = scan_directory(root, media_types)
            except (FileNotFoundError, PermissionError, ValueError) as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                return 1

            # Generate rename plan
            progress.update(
                progress.task_ids[0], description="Generating rename plan..."
            )
            rule_set = PlexRuleSet()  # TODO: Make this configurable based on platform
            plan = create_rename_plan(
                scan_result=scan_result,
                rule_set=rule_set,
                plan_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
                platform=platform,
                show_name=show_name,
                movie_year=movie_year,
                anthology=anthology,
                adjust_episodes=adjust_episodes,
                verify=verify,
                llm_model=llm_model,
                strict_directory_structure=strict_directory_structure,
            )

        # Output results
        if json_output:
            print(json.dumps(plan.model_dump(), cls=DateTimeEncoder, indent=2))
        else:
            render_diff(plan, console=console)

    except Exception as e:
        console.print(f"[red]Error: An unexpected error occurred: {str(e)}[/red]")
        return 1

    return 0


def main() -> None:
    """Main entry point for the CLI."""
    app.command()(scan_command)
    app()
