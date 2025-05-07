"""CLI commands for namegnome."""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install as install_traceback

from namegnome.cli.renderer import render_diff
from namegnome.core.planner import create_rename_plan
from namegnome.core.scanner import scan_directory
from namegnome.fs import store_plan, store_run_metadata
from namegnome.models.core import MediaType
from namegnome.rules.plex import PlexRuleSet
from namegnome.utils.json import DateTimeEncoder

# Install rich traceback handler
install_traceback(show_locals=True)

app = typer.Typer()
console = Console()


class ExitCode(int, Enum):
    """Exit codes for CLI commands."""

    SUCCESS = 0
    ERROR = 1
    MANUAL_NEEDED = 2


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


# Root path parameter
ROOT_PATH = Annotated[
    Path,
    typer.Argument(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Root directory to scan for media files",
    ),
]

# Media type option
MEDIA_TYPE = Annotated[
    list[str],
    typer.Option(
        "--media-type",
        "-t",
        case_sensitive=False,
        help="Media types to scan for (tv, movie, music). "
        "At least one type must be specified.",
    ),
]

# Platform option
PLATFORM = Annotated[
    str,
    typer.Option(
        "--platform",
        "-p",
        case_sensitive=False,
        help="Target platform (e.g., plex, jellyfin, emby)",
    ),
]

# Other options with annotations
SHOW_NAME = Annotated[
    Optional[str],
    typer.Option(
        "--show-name",
        help="Explicit show name for TV files",
    ),
]

MOVIE_YEAR = Annotated[
    Optional[int],
    typer.Option(
        "--movie-year",
        help="Explicit year for movie files",
    ),
]

ANTHOLOGY = Annotated[
    bool,
    typer.Option(
        "--anthology",
        help="Whether the TV show is an anthology series",
    ),
]

ADJUST_EPISODES = Annotated[
    bool,
    typer.Option(
        "--adjust-episodes",
        help="Adjust episode numbering for incorrectly numbered files",
    ),
]

VERIFY = Annotated[
    bool,
    typer.Option(
        "--verify",
        help="Verify file integrity with checksums",
    ),
]

JSON_OUTPUT = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Output results in JSON format",
    ),
]

LLM_MODEL = Annotated[
    Optional[str],
    typer.Option(
        "--llm-model",
        help="LLM model to use for fuzzy matching",
    ),
]

NO_COLOR = Annotated[
    bool,
    typer.Option(
        "--no-color",
        help="Disable colored output",
    ),
]

STRICT_DIRECTORY_STRUCTURE = Annotated[
    bool,
    typer.Option(
        "--strict-directory-structure",
        help="Enforce platform directory structure",
    ),
]


@dataclass
class ScanCommandOptions:
    """Options for the scan command."""

    root: Path
    media_type: List[str] = field(default_factory=list)
    platform: str = "plex"
    show_name: Optional[str] = None
    movie_year: Optional[int] = None
    anthology: bool = False
    adjust_episodes: bool = False
    verify: bool = False
    json_output: bool = False
    llm_model: Optional[str] = None
    no_color: bool = False
    strict_directory_structure: bool = True


@app.command()
def scan(  # noqa: PLR0913
    # Use Typer's parameters but delegate implementation to ScanCommandOptions
    root: ROOT_PATH,
    media_type: MEDIA_TYPE = [],
    platform: PLATFORM = "plex",
    show_name: SHOW_NAME = None,
    movie_year: MOVIE_YEAR = None,
    anthology: ANTHOLOGY = False,
    adjust_episodes: ADJUST_EPISODES = False,
    verify: VERIFY = False,
    json_output: JSON_OUTPUT = False,
    llm_model: LLM_MODEL = None,
    no_color: NO_COLOR = False,
    strict_directory_structure: STRICT_DIRECTORY_STRUCTURE = True,
) -> int:
    """Scan a directory for media files and generate a rename plan."""
    # Convert media_type to list to fix type issue
    media_type_list = list(media_type)

    # Use CLI parameters to create options object
    return _scan_impl(
        ScanCommandOptions(
            root=root,
            media_type=media_type_list,
            platform=platform,
            show_name=show_name,
            movie_year=movie_year,
            anthology=anthology,
            adjust_episodes=adjust_episodes,
            verify=verify,
            json_output=json_output,
            llm_model=llm_model,
            no_color=no_color,
            strict_directory_structure=strict_directory_structure,
        )
    )


def _scan_impl(options: ScanCommandOptions) -> int:
    """Implementation of the scan command."""
    # Create console with appropriate color settings
    console = Console(no_color=options.no_color)

    # Check if at least one media type is specified
    if not options.media_type:
        console.print("[red]Error: At least one media type must be specified[/red]")
        return ExitCode.ERROR

    # Convert string media types to MediaType enum values
    try:
        media_types = [validate_media_type(mt) for mt in options.media_type]
    except typer.BadParameter as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return ExitCode.ERROR

    # Generate plan ID based on current timestamp
    plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Store command arguments for the metadata file
    cmd_args = {
        "root": str(options.root),
        "media_type": options.media_type,
        "platform": options.platform,
        "show_name": options.show_name,
        "movie_year": options.movie_year,
        "anthology": options.anthology,
        "adjust_episodes": options.adjust_episodes,
        "verify": options.verify,
        "json_output": options.json_output,
        "llm_model": options.llm_model,
        "no_color": options.no_color,
        "strict_directory_structure": options.strict_directory_structure,
    }

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
                scan_result = scan_directory(
                    options.root, media_types, verify_hash=options.verify
                )
            except (FileNotFoundError, PermissionError, ValueError) as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                return ExitCode.ERROR

            # Generate rename plan
            progress.update(
                progress.task_ids[0], description="Generating rename plan..."
            )

            # Determine which rule set to use based on platform
            # For now, we only have PlexRuleSet, but this can be extended
            # to support other platforms in the future
            rule_set = PlexRuleSet()  # TODO: Make this configurable based on platform

            plan = create_rename_plan(
                scan_result=scan_result,
                rule_set=rule_set,
                plan_id=plan_id,
                platform=options.platform,
                show_name=options.show_name,
                movie_year=options.movie_year,
                anthology=options.anthology,
                adjust_episodes=options.adjust_episodes,
                verify=options.verify,
                llm_model=options.llm_model,
                strict_directory_structure=options.strict_directory_structure,
            )

            # Store the plan and metadata
            if scan_result.total_files > 0:
                progress.update(
                    progress.task_ids[0], description="Storing rename plan..."
                )
                plan_path = store_plan(plan)
                metadata_path = store_run_metadata(plan_id, cmd_args)

                # Log paths for debugging
                console.log(f"Plan stored at: {plan_path}")
                console.log(f"Metadata stored at: {metadata_path}")

        # Output results
        if options.json_output:
            json_str = json.dumps(plan.model_dump(), cls=DateTimeEncoder, indent=2)
            sys.stdout.write(json_str + "\n")
        else:
            render_diff(plan, console=console)

            # Check if any items require manual confirmation
            manual_items = [item for item in plan.items if item.manual]
            if manual_items:
                console.print(
                    f"\n[bold yellow]Warning:[/bold yellow] {len(manual_items)} "
                    f"item(s) require manual confirmation. "
                    f"Use --force to override or fix these issues manually."
                )
                return ExitCode.MANUAL_NEEDED

    except Exception as e:
        console.print(f"[red]Error: An unexpected error occurred: {str(e)}[/red]")
        console.print_exception()
        return ExitCode.ERROR

    return ExitCode.SUCCESS


@app.command()
def version() -> None:
    """Show the version of namegnome."""
    from namegnome.__about__ import __version__

    console.print(f"NameGnome version: [bold]{__version__}[/bold]")


def main() -> None:
    """Main entry point for the CLI."""
    app()
