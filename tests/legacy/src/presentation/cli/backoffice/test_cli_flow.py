"""Integration-style tests for backoffice CLI flow."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.value_objects.summary_result import SummaryResult
from src.presentation.cli.backoffice.commands.channels import channels
from src.presentation.cli.backoffice.commands.digest import digest

channels_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.channels"
)
digest_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.digest"
)


class _ChannelsCollection:
    def __init__(self, document: dict | None):
        self._document = document

    async def find_one(self, query):
        return self._document


class _DummyDB:
    def __init__(self, document: dict | None):
        self.channels = _ChannelsCollection(document)


def _sample_digest() -> ChannelDigest:
    return ChannelDigest(
        channel_username="tech_news",
        channel_title="Tech News",
        summary=SummaryResult(
            text="Summary body",
            sentences_count=2,
            method="direct",
            confidence=0.9,
        ),
        post_count=4,
        time_window_hours=24,
        tags=["analytics"],
        generated_at=datetime.now(timezone.utc),
    )


def test_cli_backoffice_full_flow() -> None:
    """End-to-end happy path using patched dependencies."""
    runner = CliRunner()
    digest_obj = _sample_digest()

    digest_use_case = AsyncMock()
    digest_use_case.execute = AsyncMock(return_value=[digest_obj])

    channel_rows = [
        {
            "id": "abc123",
            "channel": "tech_news",
            "title": "Tech News",
            "tags": ["analytics"],
            "active": True,
            "subscribed_at": "2025-11-09T10:00:00Z",
        }
    ]

    db_stub = _DummyDB(
        {
            "channel_username": "tech_news",
            "title": "Tech News",
            "last_digest": "2025-11-09T11:00:00Z",
            "tags": ["analytics"],
            "active": True,
        }
    )

    with patch.object(
        channels_module, "get_db", new=AsyncMock(return_value=db_stub)
    ), patch.object(
        channels_module,
        "_fetch_channels",
        new=AsyncMock(return_value=channel_rows),
    ), patch.object(
        channels_module,
        "mcp_add_channel",
        new=AsyncMock(return_value={"status": "subscribed", "channel_id": "abc123"}),
    ) as mock_add, patch.object(
        channels_module,
        "mcp_delete_channel",
        new=AsyncMock(return_value={"status": "deleted", "channel_id": "abc123"}),
    ) as mock_delete, patch(
        "src.infrastructure.database.mongo.get_db",
        new=AsyncMock(return_value=db_stub),
    ), patch(
        "src.application.use_cases.generate_channel_digest.GenerateChannelDigestUseCase",
        return_value=digest_use_case,
    ):
        add_result = runner.invoke(
            channels, ["add", "--user-id", "42", "--channel", "tech_news"]
        )
        list_result = runner.invoke(channels, ["list", "--user-id", "42"])
        digest_result = runner.invoke(digest, ["run", "--user-id", "42"])
        last_result = runner.invoke(
            digest, ["last", "--user-id", "42", "--channel", "tech_news"]
        )
        remove_result = runner.invoke(
            channels, ["remove", "--user-id", "42", "--channel-id", "abc123"]
        )

    assert add_result.exit_code == 0
    assert list_result.exit_code == 0
    assert digest_result.exit_code == 0
    assert last_result.exit_code == 0
    assert remove_result.exit_code == 0
    assert "tech_news" in list_result.output
    assert "Tech News" in last_result.output
    mock_add.assert_awaited_once()
    mock_delete.assert_awaited_once()
    digest_use_case.execute.assert_awaited_once_with(user_id=42, hours=24)
