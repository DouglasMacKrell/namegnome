"""Emoji-based status gnome utilities for NameGnome CLI.

Provides helpers to print status gnomes using Unicode emoji and Rich panels.
"""

from typing import Literal, Optional

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

GnomeType = Literal["working", "happy", "error", "confused", "sad"]

GNOME_PANEL_WIDTH = 54  # Increased width for all status gnome panels

GNOME_EMOJI_MAP = {
    # Working: magic, pickaxe, tools, construction horses, folder
    "working": (
        "           ⚡️✨⚡️\n🧙‍♂️⛏️  ⚒️  🛠️  🚧  📁  🚧   ",
        "NameGnome: Renaming files...",
        "bold yellow",
    ),
    "happy": (
        "🧙‍♂️  👍  🎉   ",
        "NameGnome: All set!",
        "bold green",
    ),
    "error": (
        "🧙‍♂️  💔  ❌   ",
        "NameGnome: Something went wrong!",
        "bold red",
    ),
    "confused": (
        "🧙‍♂️  🤔  📁  ❓   ",
        "NameGnome: What is this file?!",
        "bold magenta",
    ),
}

panel_left_pad = "    "  # 4 spaces for left indent


def print_gnome_status(
    gnome: GnomeType,
    console: Optional[Console] = None,
    style: Optional[str] = None,
) -> None:
    if console is None:
        console = Console()
    # Treat 'sad' as alias for 'error'
    if gnome == "sad":
        gnome = "error"
    emoji, message, default_style = GNOME_EMOJI_MAP.get(
        gnome, ("🧙‍♂️", "NameGnome", "bold")
    )
    style = style or default_style
    # Pad both lines to fixed width for all gnomes, with manual left indent
    if message:
        lines = [
            f"{panel_left_pad}{emoji}".ljust(GNOME_PANEL_WIDTH),
            f"{panel_left_pad}{message}".ljust(GNOME_PANEL_WIDTH),
        ]
    else:
        lines = [f"{panel_left_pad}{emoji}".ljust(GNOME_PANEL_WIDTH)]
    panel_content = "\n".join(lines)
    console.print(
        Panel(
            Align.left(panel_content),
            title=gnome.capitalize(),
            width=GNOME_PANEL_WIDTH,
            box=box.SQUARE,
            style=style,
            padding=(1, 0),  # No horizontal padding
        )
    )


# Alias for CLI usage
print_gnome = print_gnome_status


def print_title(console: Optional[Console] = None) -> None:
    if console is None:
        console = Console()
    ascii_title_lines = [
        "    _   _                          _____   ",
        r"   | \ | |                        |  __ \   ",
        r"   |  \| |  __ _  _ __ ___    ___ | |  \/ _ __    "
        "___   _ __ ___    ___   ",  # E501 wrapped
        r"   | . ` | / _` || '_ ` _ \  / _ \| | __ | '_ \  / _ \ | '_ ` _ \  / _ \   ",
        r"   | |\  || (_| || | | | | ||  __/| |_\ \| | | || (_) || | | | | ||  __/   ",
        r"   \_| \_/ \__,_||_| |_| |_| \___| \____/|_| |_| \___/ |_| |_| |_| \___|   ",
    ]  # E501 wrapped
    # Gnome art as raw strings
    gnome_art = [
        r"                                   __ ",
        r"                                .-'  | ",
        r"                               /   <\| ",
        r"                              /     \' ",
        r"                              |_.- o-o ",
        r"                              / C  -._)\  | ",
        r"                             /',   \__/ |_|-7 ",
        r"                            |   `-,_,__,'___| ",
        r"                            (,,)====[_]=| ",
        r"                             '.   ____/ ",
        r"                              | -|-|_ ",
        r"                              |____)_) ",
        r"                                       ",
    ]  # E501 wrapped
    # Determine panel width
    width = max(len(line) for line in ascii_title_lines)
    # Combine all lines, preserving all spacing
    combined = ascii_title_lines + ["", *gnome_art]
    panel_content = "\n".join(combined)
    console.print(
        Panel(
            panel_content,
            title="NameGnome",
            width=width + 2,  # +2 for border padding
            box=box.SQUARE,
            style="cyan",
            padding=(0, 0),
        )
    )
