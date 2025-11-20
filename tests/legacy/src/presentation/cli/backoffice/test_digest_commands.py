"""Tests for digest CLI commands."""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.value_objects.summary_result import SummaryResult
from src.presentation.cli.backoffice.commands.digest import digest

digest_module = importlib.import_module(
    "src.presentation.cli.backoffice.commands.digest"
)


def _make_digest() -> ChannelDigest:
    return ChannelDigest(
        channel_username="tech_news",
        channel_title="Tech News",
        summary=SummaryResult(
            text="Summary body",
            sentences_count=2,
            method="direct",
            confidence=0.9,
        ),
        post_count=5,
        time_window_hours=24,
        tags=["analytics"],
        generated_at=datetime.now(timezone.utc),
    )


def test_digest_run_all_channels_outputs_table() -> None:
    """`digest run` without channel should aggregate all subscriptions."""
    runner = CliRunner()
    digest_obj = _make_digest()

    fake_use_case = AsyncMock()
    fake_use_case.execute = AsyncMock(return_value=[digest_obj])

    with patch(
        "src.application.use_cases.generate_channel_digest.GenerateChannelDigestUseCase",
        return_value=fake_use_case,
    ):
        result = runner.invoke(digest, ["run", "--user-id", "42"])

    assert result.exit_code == 0
    assert "tech_news" in result.output
    fake_use_case.execute.assert_awaited_once_with(user_id=42, hours=24)


def test_digest_run_single_channel_json_output() -> None:
    """`digest run --channel --json` returns JSON payload."""
    runner = CliRunner()
    digest_obj = _make_digest()

    fake_use_case = AsyncMock()
    fake_use_case.execute = AsyncMock(return_value=digest_obj)

    with patch(
        "src.application.use_cases.generate_channel_digest_by_name.GenerateChannelDigestByNameUseCase",
        return_value=fake_use_case,
    ):
        result = runner.invoke(
            digest,
            [
                "run",
                "--user-id",
                "42",
                "--channel",
                "tech_news",
                "--json",
            ],
        )

    assert result.exit_code == 0
    assert '"channel": "tech_news"' in result.output
    fake_use_case.execute.assert_awaited_once()


def test_digest_run_handles_errors() -> None:
    """`digest run` should bubble up errors as CLI exceptions."""
    runner = CliRunner()

    fake_use_case = AsyncMock()
    fake_use_case.execute = AsyncMock(side_effect=RuntimeError("boom"))

    with patch(
        "src.application.use_cases.generate_channel_digest.GenerateChannelDigestUseCase",
        return_value=fake_use_case,
    ):
        result = runner.invoke(digest, ["run", "--user-id", "42"])

    assert result.exit_code == 1
    assert "boom" in result.output


def test_digest_last_outputs_table() -> None:
    """`digest last` should fetch metadata from channels collection."""
    runner = CliRunner()

    class _ChannelsCollection:
        def __init__(self, document: dict | None):
            self._document = document

        async def find_one(self, query):
            return self._document

    class _DB:
        def __init__(self, document: dict | None):
            self.channels = _ChannelsCollection(document)

    document = {
        "user_id": 42,
        "channel_username": "tech_news",
        "title": "Tech News",
        "last_digest": "2025-11-09T10:00:00Z",
        "tags": ["analytics"],
        "active": True,
    }

    with patch(
        "src.infrastructure.database.mongo.get_db",
        new=AsyncMock(return_value=_DB(document)),
    ):
        result = runner.invoke(
            digest,
            ["last", "--user-id", "42", "--channel", "tech_news"],
        )

    assert result.exit_code == 0
    assert "Tech News" in result.output


def test_digest_last_handles_missing_channel() -> None:
    """`digest last` should exit with error when channel missing."""
    runner = CliRunner()

    class _ChannelsCollection:
        async def find_one(self, query):
            return None

    class _DB:
        def __init__(self):
            self.channels = _ChannelsCollection()

    with patch(
        "src.infrastructure.database.mongo.get_db",
        new=AsyncMock(return_value=_DB()),
    ):
        result = runner.invoke(
            digest,
            ["last", "--user-id", "42", "--channel", "missing"],
        )

    assert result.exit_code == 1
    assert "Channel 'missing' not found" in result.output
