"""Tests for channel CLI commands."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from src.presentation.cli.backoffice.commands.channels import channels

channels_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.channels"
)


def test_list_channels_outputs_table() -> None:
    """`channels list` should render human-readable table output."""
    runner = CliRunner()
    db_stub = object()
    channels_payload = [
        {
            "id": "507f1f77bcf86cd799439011",
            "channel": "tech_news",
            "title": "Tech News",
            "tags": ["analytics"],
            "active": True,
            "subscribed_at": "2025-11-09T10:00:00Z",
        }
    ]

    with patch.object(
        channels_module, "get_db", new=AsyncMock(return_value=db_stub)
    ), patch.object(
        channels_module, "_fetch_channels", new=AsyncMock(return_value=channels_payload)
    ):
        result = runner.invoke(channels, ["list", "--user-id", "42"])

    assert result.exit_code == 0
    assert "tech_news" in result.output


def test_list_channels_outputs_json() -> None:
    """`channels list --json` should return JSON array."""
    runner = CliRunner()

    with patch.object(channels_module, "get_db", new=AsyncMock()), patch.object(
        channels_module,
        "_fetch_channels",
        new=AsyncMock(return_value=[{"channel": "tech", "id": "123"}]),
    ):
        result = runner.invoke(channels, ["list", "--user-id", "42", "--json"])

    assert result.exit_code == 0
    assert '"channel": "tech"' in result.output


def test_add_channel_success() -> None:
    """`channels add` should call subscription tool and print result."""
    runner = CliRunner()

    with patch.object(
        channels_module,
        "mcp_add_channel",
        new=AsyncMock(return_value={"status": "subscribed", "channel_id": "123"}),
    ):
        result = runner.invoke(
            channels, ["add", "--user-id", "42", "--channel", "tech_news"]
        )

    assert result.exit_code == 0
    assert "123" in result.output


def test_add_channel_failure_returns_error() -> None:
    """`channels add` should raise ClickException on subscription failure."""
    runner = CliRunner()

    with patch.object(
        channels_module,
        "mcp_add_channel",
        new=AsyncMock(
            return_value={
                "status": "error",
                "message": "validation failed",
            }
        ),
    ):
        result = runner.invoke(
            channels, ["add", "--user-id", "42", "--channel", "tech_news"]
        )

    assert result.exit_code == 1
    assert "validation failed" in result.output


def test_remove_channel_success() -> None:
    """`channels remove` should mark subscription inactive."""
    runner = CliRunner()

    with patch.object(
        channels_module,
        "mcp_delete_channel",
        new=AsyncMock(return_value={"status": "deleted", "channel_id": "123"}),
    ):
        result = runner.invoke(
            channels,
            ["remove", "--user-id", "42", "--channel-id", "507f1f77bcf86cd799439011"],
        )

    assert result.exit_code == 0
    assert "deleted" in result.output


def test_remove_channel_not_found_sets_error() -> None:
    """`channels remove` should exit with an error when channel not found."""
    runner = CliRunner()

    with patch.object(
        channels_module,
        "mcp_delete_channel",
        new=AsyncMock(return_value={"status": "not_found", "channel_id": "missing"}),
    ):
        result = runner.invoke(
            channels,
            ["remove", "--user-id", "42", "--channel-id", "missing"],
        )

    assert result.exit_code == 1
    assert "Channel not found" in result.output

