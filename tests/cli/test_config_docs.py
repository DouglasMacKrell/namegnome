from click.testing import CliRunner

from namegnome.cli.commands import app


def test_config_docs_command_runs() -> None:
    """`namegnome config docs` should exit 0 and render a Rich table."""
    runner = CliRunner()
    result = runner.invoke(app, ["config", "docs"])
    assert result.exit_code == 0
    # Table title should be in plain text output
    assert "Configuration Settings" in result.output
