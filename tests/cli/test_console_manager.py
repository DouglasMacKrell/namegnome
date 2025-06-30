from __future__ import annotations

from rich.console import Console

from namegnome.cli.console import ConsoleManager


def _get_output(capsys) -> str:
    """Helper to fetch captured stdout/stderr merged as a single string."""
    captured = capsys.readouterr()
    return (captured.out + captured.err).strip()


def test_console_manager_yields_console_and_spins():  # noqa: D103
    with ConsoleManager(record=True) as console:  # type: Console
        assert isinstance(console, Console)
        console.print("Start")
        with console.status("Processing..."):
            console.print("Working")
        console.print("Done")

        output = console.export_text()

    # We're not testing Rich control characters, just logical content.
    for expected in ("Start", "Working", "Done"):
        assert expected in output


def test_console_manager_pretty_traceback():  # noqa: D103
    with ConsoleManager(record=True) as console:
        try:
            1 / 0
        except ZeroDivisionError:
            # Use Rich helper to print the pretty traceback into the console.
            console.print_exception()

        output = console.export_text()

    # Rich pretty-traceback should contain exception class name.
    assert "ZeroDivisionError" in output
