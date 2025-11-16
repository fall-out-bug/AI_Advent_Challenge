"""Unit tests for TelegramAdapter implementation.

Purpose:
    Verify that TelegramAdapterImpl correctly implements TelegramAdapter Protocol
    and wraps telegram_utils.fetch_channel_posts() with canonical form normalization.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from src.domain.interfaces.telegram_adapter import TelegramAdapter
from src.infrastructure.clients.telegram_adapter_impl import TelegramAdapterImpl


@pytest.fixture
def adapter() -> TelegramAdapterImpl:
    """Create TelegramAdapterImpl instance for tests."""
    return TelegramAdapterImpl()


class TestTelegramAdapterImpl:
    """Test suite for TelegramAdapterImpl."""

    @pytest.mark.asyncio
    async def test_implements_telegram_adapter_protocol(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that TelegramAdapterImpl implements TelegramAdapter Protocol."""
        # Runtime check
        assert isinstance(adapter, TelegramAdapter)

        # Verify Protocol methods exist
        assert hasattr(adapter, "fetch_channel_posts")
        assert callable(adapter.fetch_channel_posts)

    @pytest.mark.asyncio
    async def test_fetch_channel_posts_normalizes_username(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that channel_username is normalized to canonical form.

        Purpose:
            Verify E.1 policy compliance: canonical form is lowercase without @ prefix.
        """
        since = datetime.utcnow() - timedelta(hours=24)
        mock_posts = [
            {
                "text": "Test post",
                "date": since.isoformat(),
                "channel": "onaboka",
                "message_id": "123",
            }
        ]

        with patch(
            "src.infrastructure.clients.telegram_adapter_impl._fetch_channel_posts",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_posts

            # Test with @ prefix
            result = await adapter.fetch_channel_posts(
                channel_username="@onaboka", since=since
            )

            # Verify normalization: @ prefix removed
            mock_fetch.assert_called_once()
            call_kwargs = mock_fetch.call_args.kwargs
            assert call_kwargs["channel_username"] == "onaboka"  # @ removed
            assert result == mock_posts

            # Reset mock
            mock_fetch.reset_mock()

            # Test with uppercase
            result = await adapter.fetch_channel_posts(
                channel_username="ONABOKA", since=since
            )

            # Verify normalization: lowercase
            call_kwargs = mock_fetch.call_args.kwargs
            assert call_kwargs["channel_username"] == "onaboka"  # Lowercase

            # Reset mock
            mock_fetch.reset_mock()

            # Test with canonical form (should pass through unchanged)
            result = await adapter.fetch_channel_posts(
                channel_username="onaboka", since=since
            )

            # Verify no change needed
            call_kwargs = mock_fetch.call_args.kwargs
            assert call_kwargs["channel_username"] == "onaboka"  # Unchanged

    @pytest.mark.asyncio
    async def test_fetch_channel_posts_passes_parameters(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that all parameters are passed correctly to telegram_utils."""
        since = datetime.utcnow() - timedelta(hours=24)
        user_id = 12345
        mock_posts = []

        with patch(
            "src.infrastructure.clients.telegram_adapter_impl._fetch_channel_posts",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = mock_posts

            await adapter.fetch_channel_posts(
                channel_username="onaboka",
                since=since,
                user_id=user_id,
                save_to_db=False,
            )

            # Verify all parameters passed correctly
            mock_fetch.assert_called_once_with(
                channel_username="onaboka",  # Normalized
                since=since,
                user_id=user_id,
                save_to_db=False,
            )

    @pytest.mark.asyncio
    async def test_fetch_channel_posts_returns_posts(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that adapter returns posts from telegram_utils."""
        since = datetime.utcnow() - timedelta(hours=24)
        expected_posts = [
            {
                "text": "Post 1",
                "date": since.isoformat(),
                "channel": "onaboka",
                "message_id": "1",
            },
            {
                "text": "Post 2",
                "date": (since + timedelta(hours=1)).isoformat(),
                "channel": "onaboka",
                "message_id": "2",
            },
        ]

        with patch(
            "src.infrastructure.clients.telegram_adapter_impl._fetch_channel_posts",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = expected_posts

            result = await adapter.fetch_channel_posts(
                channel_username="onaboka", since=since
            )

            assert result == expected_posts
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_channel_posts_handles_empty_result(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that adapter handles empty result gracefully."""
        since = datetime.utcnow() - timedelta(hours=24)

        with patch(
            "src.infrastructure.clients.telegram_adapter_impl._fetch_channel_posts",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = []

            result = await adapter.fetch_channel_posts(
                channel_username="onaboka", since=since
            )

            assert result == []
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_channel_posts_propagates_errors(
        self, adapter: TelegramAdapterImpl
    ):
        """Test that adapter propagates errors from telegram_utils."""
        since = datetime.utcnow() - timedelta(hours=24)

        with patch(
            "src.infrastructure.clients.telegram_adapter_impl._fetch_channel_posts",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.side_effect = ValueError("Channel not found")

            with pytest.raises(ValueError, match="Channel not found"):
                await adapter.fetch_channel_posts(
                    channel_username="nonexistent", since=since
                )

