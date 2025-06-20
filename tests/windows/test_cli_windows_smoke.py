import os
from click.testing import CliRunner

import pytest

# Skip on real Windows – we only need this on non-Windows hosts to smoke-test
# for Windows-specific regressions during development/CI runs on Linux/macOS.
pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="redundant on native Windows runner"
)


def test_cli_runs_under_simulated_windows(monkeypatch, tmp_path):
    """Smoke-test: ensure the Typer CLI can be invoked when os.name == 'nt'.

    Click uses different internal code paths on Windows that broke when Typer
    removed the ``.name``/``.main`` attributes (see #CI dependency resolution
    issue).  By monkeypatching ``os.name`` we trigger that branch on every
    platform so the failure is caught locally and by pre-commit before hitting
    the real Windows CI runner.
    """

    monkeypatch.setattr(os, "name", "nt", raising=False)

    # WindowsPath.home() needs %USERPROFILE% env var; instead, point it to
    # our pytest tmp dir so pathlib doesn't crash when Typer imports
    # modules that call Path.home().
    from pathlib import Path

    monkeypatch.setattr(Path, "home", lambda: tmp_path)  # type: ignore[arg-type]

    # Import lazily after the patch so Typer sees the modified os.name at
    # import-time (that is when Click helpers run).
    from namegnome.cli import commands as cmd  # pylint: disable=import-error

    runner = CliRunner()
    # Use minimal invocation that previously crashed deep inside Click.
    result = runner.invoke(cmd.app, ["--help"])  # noqa: S603 – user input

    # Exit code 0 and some output indicates the CLI didn't crash.
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output
