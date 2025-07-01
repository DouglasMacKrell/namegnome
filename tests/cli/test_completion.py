import re

from typer.testing import CliRunner

from namegnome.cli.commands import app


def _clean(txt: str) -> str:  # noqa: D103
    _ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return _ansi.sub("", txt)


def test_completion_command_bash():  # noqa: D103
    runner = CliRunner()
    result = runner.invoke(app, ["completion", "bash"])
    assert result.exit_code == 0, result.output
    out = _clean(result.output)
    assert "_NAMEGNOME_COMPLETE" in out or "namegnome" in out.lower()
