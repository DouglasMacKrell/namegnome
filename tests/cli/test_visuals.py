import pytest
from rich.console import Console

from namegnome.cli.utils.ascii_art import (
    print_title,
    print_gnome_status,
    GNOME_EMOJI_MAP,
)
from namegnome.cli.console import gnome_status, ConsoleManager, create_default_progress


@pytest.fixture()
def rich_console():
    """Return a Rich console with recording enabled for snapshot tests."""
    return Console(record=True, width=120)


def _strip_text(console: Console) -> str:
    """Return plain text from recorded console output."""
    return console.export_text().strip()


def test_print_title_snapshot(rich_console):  # noqa: D401
    print_title(rich_console)
    output = _strip_text(rich_console)
    # Ensure banner and project name present
    assert "NameGnome" in output
    # The ASCII art contains underscore characters – spot-check one
    assert "_   _" in output


@pytest.mark.parametrize("gnome", list(GNOME_EMOJI_MAP.keys()))
def test_print_gnome_status_variants(rich_console, gnome):  # noqa: D401
    print_gnome_status(gnome, console=rich_console)
    output = _strip_text(rich_console)
    # Each gnome panel should include its capitalised title and description line
    assert gnome.capitalize() in output
    # Check main description message appears (second element of tuple)
    _, message, _ = GNOME_EMOJI_MAP[gnome]
    assert message in output


def test_gnome_status_context_manager():  # noqa: D401
    with ConsoleManager(record=True) as console:
        with gnome_status(console):
            console.print("inside")
        text = console.export_text()

    # Expect working, inside message, and happy gnome
    assert "Renaming files" in text  # working gnome description
    assert "inside" in text
    assert "All set" in text  # happy gnome description


def test_progress_includes_filename_column():  # noqa: D401
    progress = create_default_progress()
    column_types = [type(col).__name__ for col in progress.columns]
    # Ensure our custom and expected default columns are present
    assert "FilenameColumn" in column_types
    assert "TimeElapsedColumn" in column_types
    # There should now be at least 5 columns (spinner, desc, percent, elapsed, filename)
    assert len(column_types) >= 5
    # Spinner is still first
    assert column_types[0] == "SpinnerColumn"
