"""Integration-style tests for the backoffice CLI entry point."""

from __future__ import annotations

<<<<<<< HEAD
=======
from collections.abc import Sequence

>>>>>>> origin/master
import importlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

digest_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.digest"
)
<<<<<<< HEAD
=======
channels_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.channels"
)
>>>>>>> origin/master
from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.value_objects.summary_result import SummaryResult
from src.presentation.cli.backoffice.main import cli


def _fake_digest(channel: str = "example_channel") -> ChannelDigest:
    """Create a deterministic digest payload for CLI tests."""
    return ChannelDigest(
        channel_username=channel,
        channel_title="Example Channel",
        summary=SummaryResult(
            text="Sample summary text.",
            sentences_count=2,
            method="direct",
            confidence=0.92,
            metadata={"words": 42},
        ),
        post_count=3,
        time_window_hours=24,
        tags=["news"],
        generated_at=datetime.now(timezone.utc),
    )


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


def test_digest_run_outputs_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running digest without channel uses GenerateChannelDigestUseCase."""
    digest = _fake_digest()

    async def fake_run_digest(
        user_id: int,
        channel: str | None,
        hours: int,
        content_format: str,
        as_json: bool,
    ) -> None:
        assert user_id == 101
        assert channel is None
        assert hours == 24
        assert content_format == "markdown"
        assert as_json is False
        print(f"{digest.channel_username}: {digest.summary.text}")

    monkeypatch.setattr(
        digest_module,
        "_run_digest",
        fake_run_digest,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["digest", "run", "--user-id", "101"])

    assert result.exit_code == 0
    assert digest.summary.text in result.output
    assert digest.channel_username in result.output


def test_digest_run_for_specific_channel_returns_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running digest with --channel uses the by-name use case and yields JSON."""
    digest = _fake_digest(channel="breaking_news")

    async def fake_run_digest(
        user_id: int,
        channel: str | None,
        hours: int,
        content_format: str,
        as_json: bool,
    ) -> None:
        assert user_id == 102
        assert channel == "breaking_news"
        assert hours == 24
        assert content_format == "markdown"
        assert as_json is True
        print(
            f'{{"channel": "{digest.channel_username}", '
            f'"summary": "{digest.summary.text}"}}'
        )

    monkeypatch.setattr(
        digest_module,
        "_run_digest",
        fake_run_digest,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["digest", "run", "--user-id", "102", "--channel", "breaking_news", "--json"],
    )

    assert result.exit_code == 0
    assert '"channel": "breaking_news"' in result.output
    assert '"Sample summary text."' in result.output


def test_digest_export_reports_destination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Digest export command should surface the destination path."""
    destination = tmp_path / "digest.pdf"

    async def fake_export(**_: object):
        return destination

    monkeypatch.setattr(
        digest_module,
        "export_digest_to_file",
        fake_export,
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "digest",
            "export",
            "--user-id",
            "77",
            "--channel",
            "updates",
            "--output",
            str(destination),
            "--format",
            "pdf",
            "--overwrite",
        ],
    )

    assert result.exit_code == 0
    assert f"Digest saved to {destination}" in result.output
<<<<<<< HEAD
=======


def test_channels_list_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels list command."""
    channels_data = [
        {
            "id": "507f1f77bcf86cd799439011",
            "channel": "@test_channel",
            "title": "Test Channel",
            "tags": ["news"],
            "active": True,
            "subscribed_at": datetime.now(timezone.utc),
        }
    ]

    async def fake_list_channels(user_id: int, limit: int, as_json: bool) -> None:
        assert user_id == 201
        assert limit == 10
        assert as_json is False
        if channels_data:
            print(f"Channel: {channels_data[0]['channel']}")

    monkeypatch.setattr(channels_module, "_list_channels", fake_list_channels)

    runner = CliRunner()
    result = runner.invoke(cli, ["channels", "list", "--user-id", "201", "--limit", "10"])

    assert result.exit_code == 0


def test_channels_list_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels list command with JSON output."""
    async def fake_list_channels(user_id: int, limit: int, as_json: bool) -> None:
        assert user_id == 202
        assert as_json is True
        print('[{"channel": "@test", "title": "Test"}]')

    monkeypatch.setattr(channels_module, "_list_channels", fake_list_channels)

    runner = CliRunner()
    result = runner.invoke(cli, ["channels", "list", "--user-id", "202", "--json"])

    assert result.exit_code == 0
    assert "@test" in result.output


def test_channels_add_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels add command."""
    result_data = {
        "status": "subscribed",
        "channel": "@new_channel",
        "channel_id": "507f1f77bcf86cd799439012",
        "message": "Channel subscribed successfully",
    }

    async def fake_add_channel(
        user_id: int, channel: str, tags: Sequence[str], as_json: bool
    ) -> None:
        assert user_id == 203
        assert channel == "@new_channel"
        assert list(tags) == ["tech", "news"]
        assert as_json is False
        print(f"Status: {result_data['status']}")

    monkeypatch.setattr(channels_module, "_add_channel", fake_add_channel)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "channels",
            "add",
            "--user-id",
            "203",
            "--channel",
            "@new_channel",
            "--tag",
            "tech",
            "--tag",
            "news",
        ],
    )

    assert result.exit_code == 0


def test_channels_add_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels add command with JSON output."""
    async def fake_add_channel(
        user_id: int, channel: str, tags: Sequence[str], as_json: bool
    ) -> None:
        assert as_json is True
        print('{"status": "subscribed", "channel": "@test"}')

    monkeypatch.setattr(channels_module, "_add_channel", fake_add_channel)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["channels", "add", "--user-id", "204", "--channel", "@test", "--json"]
    )

    assert result.exit_code == 0
    assert "subscribed" in result.output


def test_channels_remove_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels remove command."""
    async def fake_remove_channel(user_id: int, channel_id: str, as_json: bool) -> None:
        assert user_id == 205
        assert channel_id == "507f1f77bcf86cd799439013"
        assert as_json is False
        print("Channel removed.")

    monkeypatch.setattr(channels_module, "_remove_channel", fake_remove_channel)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "channels",
            "remove",
            "--user-id",
            "205",
            "--channel-id",
            "507f1f77bcf86cd799439013",
        ],
    )

    assert result.exit_code == 0


def test_channels_remove_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channels remove command with JSON output."""
    async def fake_remove_channel(user_id: int, channel_id: str, as_json: bool) -> None:
        assert as_json is True
        print('{"status": "deleted"}')

    monkeypatch.setattr(channels_module, "_remove_channel", fake_remove_channel)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "channels",
            "remove",
            "--user-id",
            "206",
            "--channel-id",
            "507f1f77bcf86cd799439014",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert "deleted" in result.output
>>>>>>> origin/master
