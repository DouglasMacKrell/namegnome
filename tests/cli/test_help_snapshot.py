import re

import pytest
from typer.testing import CliRunner

from namegnome.cli.commands import app

# Map of test name -> CLI args list -> expected substrings to appear in help
CASES: dict[str, tuple[list[str], list[str]]] = {
    "root": (
        [],
        [
            "Usage:",
            "scan",
            "undo",
            "version",
            "config",
            "llm",
        ],
    ),
    "scan": (
        ["scan", "--help"],
        [
            "Usage:",
            "--media-type",
            "--platform",
            "Root directory",
            "--help",
        ],
    ),
    "undo": (
        ["undo", "--help"],
        [
            "Usage:",
            "plan_id",
            "--yes",
            "--help",
        ],
    ),
}

_ansi = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _clean(txt: str) -> str:
    """Strip ANSI codes and collapse whitespace."""
    return re.sub(r"\s+", " ", _ansi.sub("", txt)).strip()


@pytest.mark.parametrize("case", CASES.keys())
def test_help_contains_keywords(case: str) -> None:  # noqa: D103
    args, keywords = CASES[case]
    runner = CliRunner()
    run_args = args or ["--help"]
    result = runner.invoke(app, run_args)
    assert result.exit_code == 0, result.output

    output = _clean(result.output)
    missing: list[str] = [kw for kw in keywords if kw not in output]
    assert not missing, f"Help output missing expected keywords: {missing}"
