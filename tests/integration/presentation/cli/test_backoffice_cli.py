"""Integration-style tests for the backoffice CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from src.presentation.cli.backoffice.main import cli


def test_backoffice_cli_digest_help_lists_export_command() -> None:
    """Ensure digest group exposes the export subcommand."""
    runner = CliRunner()
    result = runner.invoke(cli, ["digest", "--help"])

    assert result.exit_code == 0
    assert "export" in result.output
    assert "run" in result.output


def test_backoffice_cli_channels_help_is_available() -> None:
    """Ensure channels group remains discoverable."""
    runner = CliRunner()
    result = runner.invoke(cli, ["channels", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
