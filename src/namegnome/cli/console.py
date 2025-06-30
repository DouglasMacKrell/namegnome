"""Console utilities & context manager for CLI commands.

This module centralises Rich configuration for CLI commands:

* Pretty traceback installation with show_locals enabled.
* A ``ConsoleManager`` context manager yielding a pre-configured :class:`rich.console.Console`.
* Opt-out via the ``--no-rich`` flag (sets env var ``NAMEGNOME_NO_RICH``) or
  the environment variable being set externally.
* Helper :class:`FilenameColumn`` for progress bars.

It is intentionally lightweight so that it can be imported early by CLI
entry-points without triggering heavy Rich initialisation when disabled.
"""

from __future__ import annotations

import os
from contextlib import AbstractContextManager
from typing import Any, Dict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.traceback import install as install_rich_traceback
import rich

__all__ = [
    "console",
    "ConsoleManager",
    "FilenameColumn",
    "create_default_progress",
]

# ENV VAR used to disable rich output entirely (useful for piping or testing)
_ENV_DISABLE_RICH = "NAMEGNOME_NO_RICH"

# Provide a *global* console instance for modules that still import
# ``namegnome.cli.console.console`` directly. This maintains backward
# compatibility while we migrate callers towards :class:`ConsoleManager`.
console: Console = Console()


class ConsoleManager(AbstractContextManager):
    """Context manager that yields a configured Rich :class:`Console`.

    Parameters
    ----------
    record:
        Forwarded to :class:`rich.console.Console`. When *True*, Rich records
        all output so it can be retrieved later via ``console.export_text``. We
        expose it because many tests rely on rich recording for snapshotting.
    force_use:
        When *True* / *False* this overrides autodetection and forces rich
        enabled/disabled. When *None*, autodetect via ``NAMEGNOME_NO_RICH``.
    console_kwargs:
        Additional keyword arguments forwarded verbatim to the Console.
    """

    def __init__(
        self,
        *,
        record: bool = False,
        force_use: bool | None = None,
        **console_kwargs: Any,
    ) -> None:  # noqa: D401
        self._record = record
        self._force_use = force_use
        self._console_kwargs: Dict[str, Any] = console_kwargs
        self.console: Console | None = None

    # ---------------------------------------------------------------------
    # Context-manager protocol
    # ---------------------------------------------------------------------
    def __enter__(self) -> Console:  # noqa: D401 – unconcerned about docstring tense
        # Determine whether rich output is enabled. CLI flag sets env var so we
        # only need to inspect environment.
        if self._force_use is not None:
            rich_enabled = self._force_use
        else:
            rich_enabled = os.getenv(_ENV_DISABLE_RICH, "0").lower() not in {
                "1",
                "true",
                "yes",
            }

        # colour_system=None disables colour. Let Rich pick sensible default if
        # enabled; otherwise explicitly set colour_system=None so that colour
        # codes are suppressed in plain output.
        if rich_enabled:
            self.console = Console(record=self._record, **self._console_kwargs)
        else:
            # Disable colour & emoji, otherwise output may contain escape codes.
            self.console = Console(
                record=self._record,
                color_system=None,
                force_terminal=False,
                **self._console_kwargs,
            )

        # Install pretty traceback so that any exception raised inside the
        # context is printed using rich formatting automatically.
        install_rich_traceback(show_locals=True, console=self.console)

        return self.console

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore[override]
        # Flush console and print exception with rich formatting when one
        # occurred. This makes sure that even handled exceptions (e.g. via
        # pytest.raises) are visible in the recorded output — which is useful
        # for unit testing.
        if self.console is not None:
            if exc_type is not None:
                # Show exception using rich formatting; rely on sys.exc_info().
                self.console.print_exception()  # type: ignore[arg-type]

            self.console.file.flush()  # type: ignore[attr-defined]
        # Propagate exceptions – we do *not* swallow them.
        return False


# -------------------------------------------------------------------------
# Progress utilities
# -------------------------------------------------------------------------
class FilenameColumn(TextColumn):
    """Render just the basename of the current filename field in task fields."""

    def __init__(self) -> None:
        super().__init__("{task.fields[filename]}")


def create_default_progress() -> Progress:  # noqa: D401
    """Return a standardised :class:`~rich.progress.Progress` instance.

    Columns:
    1. Spinner emoji column
    2. Elapsed time
    3. Current filename (custom column)
    """

    return Progress(
        SpinnerColumn(),
        TimeElapsedColumn(),
        FilenameColumn(),
        console=rich.get_console(),
    )
