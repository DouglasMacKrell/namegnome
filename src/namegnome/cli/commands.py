"""CLI commands for namegnome.

This module implements all user-facing CLI commands for NameGnome, including scan,
version, and future apply/undo commands.
- Uses Typer for declarative CLI structure and option parsing.
- All output is routed through Rich Console for consistent, styled UX.
- Follows CLI UX guidelines from PLANNING.md: clear help, colorized output,
  progress bars, and robust error handling.

Design:
- Typer app and Console are instantiated at module level for reuse across
  commands.
- Annotated is used for CLI argument/option definitions to provide type safety
  and rich help text.
- ScanCommandOptions dataclass is used to group and validate scan command
  options.
- Exit codes are defined as an Enum for clarity and maintainability.

See README.md and PLANNING.md for CLI usage and design rationale.
"""

import json
import sys
import uuid
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
from namegnome.core.scanner import ScanOptions, scan_directory
from namegnome.models.core import MediaType
from namegnome.models.scan import ScanOptions as ModelScanOptions
from namegnome.rules.base import RuleSetConfig
from namegnome.rules.plex import PlexRuleSet
from namegnome.utils.json import DateTimeEncoder
from namegnome.utils.plan_store import save_plan

# Install rich traceback handler
install_traceback(show_locals=True)

# Reason: Typer app and Console are instantiated at module level for reuse and to
# ensure global options (like --no-color) are respected across all commands.
app = typer.Typer()
console = Console()


# Reason: ExitCode enum provides clear, maintainable exit codes for all CLI
# commands, matching project conventions.
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
) -> None:
    """Scan a directory for media files and generate a rename plan."""
    media_type_list = list(media_type)
    if not media_type_list:
        console.print("[red]At least one media type must be specified.[/red]")
        raise typer.Exit(ExitCode.ERROR)
    if not root.exists():
        console.print(f"[red]Error: Directory does not exist: {root}[/red]")
        raise typer.Exit(ExitCode.ERROR)
    try:
        # Convert string media types to MediaType enum values
        try:
            validated_media_types = [validate_media_type(mt) for mt in media_type_list]
        except typer.BadParameter as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(ExitCode.ERROR)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Scanning directory...", total=None)
            scan_options = ScanOptions(
                recursive=True,
                include_hidden=False,
                verify_hash=verify,
                platform=platform,
            )
            scan_result = scan_directory(
                root, validated_media_types, options=scan_options
            )
            if len(scan_result.files) == 0:
                console.print("[yellow]No media files found.[/yellow]")
                raise typer.Exit(ExitCode.SUCCESS)
            progress.update(
                progress.task_ids[0], description="Generating rename plan..."
            )
            rule_set = PlexRuleSet()  # TODO: Make this configurable based on platform
            with console.status("[cyan]Creating rename plan...", spinner="dots"):
                config = RuleSetConfig(
                    show_name=show_name,
                    movie_year=movie_year,
                    anthology=anthology,
                    adjust_episodes=adjust_episodes,
                    verify=verify,
                    llm_model=llm_model,
                    strict_directory_structure=strict_directory_structure,
                )
                plan = create_rename_plan(
                    scan_result=scan_result,
                    rule_set=rule_set,
                    plan_id=str(uuid.uuid4()),
                    platform=platform,
                    config=config,
                )
            progress.update(progress.task_ids[0], description="Storing rename plan...")
            model_scan_options = _convert_to_model_options(
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
                ),
                validated_media_types,
                scan_options,
            )
            console.log("Saving plan...")
            plan_id = save_plan(plan, model_scan_options, extra_args={"verify": verify})
            console.log(f"Plan stored with ID: {plan_id}")
        if json_output:
            json_str = json.dumps(plan.model_dump(), cls=DateTimeEncoder, indent=2)
            sys.stdout.write(json_str + "\n")
        else:
            render_diff(plan, console=console)
            manual_items = [item for item in plan.items if item.manual]
            if manual_items:
                console.print(
                    f"\n[bold yellow]Warning:[/bold yellow] {len(manual_items)} "
                    f"item(s) require manual confirmation. "
                    f"Use --force to override or fix these issues manually."
                )
                raise typer.Exit(ExitCode.MANUAL_NEEDED)
    except Exception as e:
        console.print(f"[red]Error: An unexpected error occurred: {str(e)}[/red]")
        console.print_exception()
        raise typer.Exit(ExitCode.ERROR)


def _scan_impl(options: ScanCommandOptions) -> int:
    """Implementation of the scan command."""
    # Create console with appropriate color settings
    console = Console(no_color=options.no_color)

    result: int = ExitCode.SUCCESS

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
                # Create ScanOptions for scan_directory
                scan_options = ScanOptions(
                    recursive=True,
                    include_hidden=False,
                    verify_hash=options.verify,
                    platform=options.platform,
                )
                scan_result = scan_directory(
                    options.root, media_types, options=scan_options
                )
                # Early exit if no files found
                if len(scan_result.files) == 0:
                    console.print("[yellow]No media files found.[/yellow]")
                    result = ExitCode.SUCCESS
                    plan = None
                else:
                    # Generate rename plan
                    progress.update(
                        progress.task_ids[0],
                        description="Generating rename plan...",
                    )
                    rule_set = (
                        PlexRuleSet()
                    )  # TODO: Make this configurable based on platform
                    with console.status(
                        "[cyan]Creating rename plan...", spinner="dots"
                    ):
                        config = RuleSetConfig(
                            show_name=options.show_name,
                            movie_year=options.movie_year,
                            anthology=options.anthology,
                            adjust_episodes=options.adjust_episodes,
                            verify=options.verify,
                            llm_model=options.llm_model,
                            strict_directory_structure=options.strict_directory_structure,
                        )
                        plan = create_rename_plan(
                            scan_result=scan_result,
                            rule_set=rule_set,
                            plan_id=str(uuid.uuid4()),
                            platform=options.platform,
                            config=config,
                        )
                    # Store the plan and metadata
                    progress.update(
                        progress.task_ids[0], description="Storing rename plan..."
                    )
                    model_scan_options = _convert_to_model_options(
                        options, media_types, scan_options
                    )
                    console.log("Saving plan...")
                    plan_id = save_plan(
                        plan, model_scan_options, extra_args={"verify": options.verify}
                    )
                    console.log(f"Plan stored with ID: {plan_id}")
            except (FileNotFoundError, PermissionError, ValueError) as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                result = ExitCode.ERROR
                plan = None

        # Output results if plan exists
        if result == ExitCode.SUCCESS and plan is not None:
            if options.json_output:
                json_str = json.dumps(plan.model_dump(), cls=DateTimeEncoder, indent=2)
                sys.stdout.write(json_str + "\n")
            else:
                render_diff(plan, console=console)
                manual_items = [item for item in plan.items if item.manual]
                if manual_items:
                    console.print(
                        f"\n[bold yellow]Warning:[/bold yellow] {len(manual_items)} "
                        f"item(s) require manual confirmation. "
                        f"Use --force to override or fix these issues manually."
                    )
                    result = ExitCode.MANUAL_NEEDED
    except Exception as e:
        console.print(f"[red]Error: An unexpected error occurred: {str(e)}[/red]")
        console.print_exception()
        result = ExitCode.ERROR

    return result


@app.command()
def version() -> None:
    """Show the version of namegnome."""
    from namegnome.__about__ import __version__

    console.print(f"NameGnome version: [bold]{__version__}[/bold]")


def main() -> None:
    """Main entry point for the CLI."""
    app()


def _convert_to_model_options(
    options: ScanCommandOptions, media_types: List[MediaType], scan_options: ScanOptions
) -> ModelScanOptions:
    """Convert our ScanOptions to the model version for saving.

    Args:
        options: CLI command options
        media_types: List of media types detected
        scan_options: Core scanner options

    Returns:
        Model version of scan options for storage
    """
    return ModelScanOptions(
        root=options.root,
        media_types=media_types,
        platform=options.platform,
        verify_hash=options.verify,
        recursive=scan_options.recursive,
        include_hidden=scan_options.include_hidden,
        show_name=options.show_name,
        movie_year=options.movie_year,
        anthology=options.anthology,
        adjust_episodes=options.adjust_episodes,
        json_output=options.json_output,
        llm_model=options.llm_model,
        no_color=options.no_color,
        strict_directory_structure=options.strict_directory_structure,
        target_extensions=scan_options.target_extensions,
    )


# TODO: NGN-203 - Add CLI commands for 'apply' and 'undo' once those engines are
# implemented.
