# Progress Bars & Logging: CLI UX in NameGnome

This document details the design, philosophy, and implementation of progress
bars, logging, and user feedback in NameGnome. These features ensure that all
operations are transparent, auditable, and user-friendly, whether run
interactively or in CI.

## Philosophy

- **Visibility:** Users should always know what the tool is doing, how long it
  will take, and whether it succeeded.
- **Auditability:** All operations are logged, with structured output for
  troubleshooting and compliance.
- **Consistency:** The same feedback is provided across CLI commands and
  Python APIs.
- **Accessibility:** Output degrades gracefully for non-TTY/CI environments
  (e.g., `--no-color`).

## Rich Integration

NameGnome uses the [Rich](https://rich.readthedocs.io/) library for:
- Colorful tables and status spinners
- Progress bars with percentage, ETA, and per-file status
- Pretty tracebacks for error reporting

All user-visible output is routed through `rich.console.Console`.

## Progress Bars & Spinners

- **Progress bars** are shown during long-running operations (apply, undo,
  scan) with per-file updates.
- **Spinners** indicate status during network or LLM requests.
- **No-color mode** (`--no-color`) disables ANSI codes for logs/CI.

### Example: CLI Usage

```sh
namegnome apply <plan-id>
# Shows a progress bar for each file move

namegnome undo <plan-id>
# Shows a spinner for each restore operation
```

### Example: Python Usage

```python
from rich.console import Console
from rich.progress import Progress

console = Console()
with Progress() as progress:
    task = progress.add_task("Moving files...", total=10)
    for i in range(10):
        # ... move file ...
        progress.update(task, advance=1)
console.log("All files moved!")
```

## Structured Logging

- All operations are logged to the console and, where relevant, to log files
  (e.g., `runs/<id>.log`).
- Logs are structured (JSON lines) for easy parsing and troubleshooting.
- Errors and warnings are highlighted in red/yellow for visibility.

## CLI Feedback & Error Reporting

- All errors are reported with clear, actionable messages.
- Pretty tracebacks are enabled by default for debugging.
- Exit codes are set appropriately for CI/scripting.
- Summary tables and footers show counts of moved, skipped, failed, and manual
  items.

## Auditability

- Every operation (scan, apply, undo) is logged with timestamps and details.
- Plan files and logs provide a full audit trail for compliance and rollback.

## Design Rationale

- Rich is chosen for its cross-platform support, beautiful output, and
  extensibility.
- All output is E501-wrapped and follows Google-style docstring/comment
  standards.
- Logging is designed to be both human- and machine-readable.

## Testing & Guarantees

- 100% test coverage for CLI output, including:
  - Progress bar and spinner rendering
  - No-color mode
  - Error and warning messages
  - Log file creation and content
- Output is tested in both unit and integration tests (see
  [integration-testing.md](integration-testing.md)).

## See Also

- [apply-undo.md](apply-undo.md): How progress/logging integrates with apply/undo
- [README.md](../README.md): CLI usage and quick start
- [integration-testing.md](integration-testing.md): End-to-end test philosophy 