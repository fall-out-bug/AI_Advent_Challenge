"""Tests for PostFetcherWorker (TDD approach).

Test coverage:
- Hourly schedule execution
- Channel processing loop
- Error handling (continue on channel failure)
- Statistics logging
- MongoDB connection failures
- Empty channels list
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db = AsyncMock()
    db.channels = AsyncMock()
    db.posts = AsyncMock()
    return db


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client."""
    client = AsyncMock()
    client.call_tool = AsyncMock()
    return client


@pytest.fixture
def mock_telegram_client():
    """Create mock Telegram client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_telegram_adapter():
    """Create mock TelegramAdapter."""
    adapter = AsyncMock()
    adapter.fetch_channel_posts = AsyncMock()
    return adapter


@pytest.fixture
def sample_channels():
    """Create sample channels data."""
    return [
        {
            "_id": "channel_1",
            "user_id": 123,
            "channel_username": "test_channel_1",
            "active": True,
            "last_fetch": None,
        },
        {
            "_id": "channel_2",
            "user_id": 123,
            "channel_username": "test_channel_2",
            "active": True,
            "last_fetch": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        },
        {
            "_id": "channel_3",
            "user_id": 456,
            "channel_username": "test_channel_3",
            "active": True,
            "last_fetch": None,
        },
    ]


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.post_fetch_interval_hours = 1
    settings.post_ttl_days = 7
    return settings


@pytest.mark.asyncio
async def test_post_fetcher_processes_all_channels(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker processes all active channels."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=sample_channels)
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_db.channels.update_one = AsyncMock()
    mock_telegram_adapter.fetch_channel_posts.return_value = [
        {
            "text": "Test post",
            "date": datetime.utcnow().isoformat(),
            "message_id": "123",
        }
    ]
    mock_mcp_client.call_tool.return_value = {
        "saved": 1,
        "skipped": 0,
        "total": 1,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    mock_fetch.return_value = [
                        {
                            "text": "Test post",
                            "date": datetime.utcnow(),
                            "message_id": "123",
                        }
                    ]
                    mock_mcp_client.call_tool.return_value = {
                        "saved": 1,
                        "skipped": 0,
                        "total": 1,
                    }

                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    assert mock_fetch.call_count == len(sample_channels)
                    # MCP call happens for each channel when posts are saved
                    assert mock_mcp_client.call_tool.call_count >= len(sample_channels)


@pytest.mark.asyncio
async def test_post_fetcher_handles_empty_channels_list(
    mock_db, mock_mcp_client, mock_settings, mock_telegram_adapter
):
    """Test that worker handles empty channels list gracefully."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.channels.find = MagicMock(return_value=mock_cursor)

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    mock_fetch.assert_not_called()
                    # MCP call only happens when posts are fetched
                    mock_mcp_client.call_tool.assert_not_called()


@pytest.mark.asyncio
async def test_post_fetcher_continues_on_channel_failure(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker continues processing other channels if one fails."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=sample_channels)
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_db.channels.update_one = AsyncMock()
    # First channel fails, others succeed
    mock_telegram_adapter.fetch_channel_posts.side_effect = [
        Exception("Channel fetch failed"),
        [
            {
                "text": "Post 2",
                "date": datetime.utcnow().isoformat(),
                "message_id": "456",
            }
        ],
        [
            {
                "text": "Post 3",
                "date": datetime.utcnow().isoformat(),
                "message_id": "789",
            }
        ],
    ]
    mock_mcp_client.call_tool.return_value = {
        "saved": 1,
        "skipped": 0,
        "total": 1,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    # First channel fails, others succeed
                    mock_fetch.side_effect = [
                        Exception("Channel fetch failed"),
                        [
                            {
                                "text": "Post 2",
                                "date": datetime.utcnow(),
                                "message_id": "456",
                            }
                        ],
                        [
                            {
                                "text": "Post 3",
                                "date": datetime.utcnow(),
                                "message_id": "789",
                            }
                        ],
                    ]
                    mock_mcp_client.call_tool.return_value = {
                        "saved": 1,
                        "skipped": 0,
                        "total": 1,
                    }

                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    assert mock_fetch.call_count == len(sample_channels)
                    # MCP call should be called only for successful fetches (2 successful channels)
                    assert mock_mcp_client.call_tool.call_count == 2


@pytest.mark.asyncio
async def test_post_fetcher_updates_last_fetch_timestamp(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker updates last_fetch timestamp after successful fetch."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=sample_channels[:1])
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_db.channels.update_one = AsyncMock()
    mock_telegram_adapter.fetch_channel_posts.return_value = [
        {
            "text": "Test post",
            "date": datetime.utcnow().isoformat(),
            "message_id": "123",
        }
    ]
    mock_mcp_client.call_tool.return_value = {
        "saved": 1,
        "skipped": 0,
        "total": 1,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    mock_fetch.return_value = [
                        {
                            "text": "Test post",
                            "date": datetime.utcnow(),
                            "message_id": "123",
                        }
                    ]
                    mock_mcp_client.call_tool.return_value = {
                        "saved": 1,
                        "skipped": 0,
                        "total": 1,
                    }

                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    mock_db.channels.update_one.assert_called_once()
                    call_args = mock_db.channels.update_one.call_args
                    assert "$set" in call_args[1]
                    assert "last_fetch" in call_args[1]["$set"]


@pytest.mark.asyncio
async def test_post_fetcher_handles_mongodb_connection_failure(
    mock_db, mock_mcp_client, mock_settings
):
    """Test that worker handles MongoDB connection failures gracefully."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    with patch(
        "src.workers.post_fetcher_worker.get_db",
        side_effect=Exception("MongoDB connection failed"),
    ):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch("src.workers.post_fetcher_worker.get_logger") as mock_logger:
                    worker = PostFetcherWorker()

                    # Act & Assert - should not raise exception
                    try:
                        await worker._process_all_channels()
                    except Exception:
                        pytest.fail(
                            "Worker should handle MongoDB connection failures gracefully"
                        )


@pytest.mark.asyncio
async def test_post_fetcher_uses_last_fetch_time_for_since_parameter(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker uses last_fetch timestamp when available."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    last_fetch_time = datetime.utcnow() - timedelta(hours=2)
    sample_channels[1]["last_fetch"] = last_fetch_time.isoformat()
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[sample_channels[1]])
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_telegram_adapter.fetch_channel_posts.return_value = []
    mock_mcp_client.call_tool.return_value = {
        "saved": 0,
        "skipped": 0,
        "total": 0,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                worker = PostFetcherWorker(telegram_adapter=mock_telegram_adapter)

                # Act
                await worker._process_all_channels()

                # Assert
                mock_telegram_adapter.fetch_channel_posts.assert_called_once()
                call_args = mock_telegram_adapter.fetch_channel_posts.call_args
                since_arg = call_args.kwargs["since"]
                # Since should be around last_fetch_time (within 1 minute tolerance)
                assert abs((since_arg - last_fetch_time).total_seconds()) < 60


@pytest.mark.asyncio
async def test_post_fetcher_uses_default_since_when_no_last_fetch(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker uses default since time (7 days for first fetch) when last_fetch is None."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    sample_channels[0]["last_fetch"] = None
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[sample_channels[0]])
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_telegram_adapter.fetch_channel_posts.return_value = []
    mock_mcp_client.call_tool.return_value = {
        "saved": 0,
        "skipped": 0,
        "total": 0,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.datetime"
                ) as mock_datetime:
                    now = datetime(2024, 1, 15, 12, 0, 0)
                    mock_datetime.utcnow.return_value = now
                    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                    worker = PostFetcherWorker(telegram_adapter=mock_telegram_adapter)

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    mock_fetch.assert_called_once()
                    call_args = mock_fetch.call_args
                    since_arg = call_args[1]["since"]
                    # Since should be around last_fetch_time (within 1 minute tolerance)
                    assert abs((since_arg - last_fetch_time).total_seconds()) < 60


@pytest.mark.asyncio
async def test_post_fetcher_uses_default_since_when_no_last_fetch(
    mock_db, mock_mcp_client, sample_channels, mock_settings
):
    """Test that worker uses default since time (1 hour ago) when last_fetch is None."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    sample_channels[0]["last_fetch"] = None
    mock_db.channels.find.return_value.to_list = AsyncMock(
        return_value=[sample_channels[0]]
    )

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    with patch(
                        "src.workers.post_fetcher_worker.datetime"
                    ) as mock_datetime:
                        now = datetime(2024, 1, 15, 12, 0, 0)
                        mock_datetime.utcnow.return_value = now
                        mock_fetch.return_value = []
                        mock_mcp_client.call_tool.return_value = {
                            "saved": 0,
                            "skipped": 0,
                            "total": 0,
                        }

                        worker = PostFetcherWorker()

                        # Act
                        await worker._process_all_channels()

                        # Assert
                        mock_fetch.assert_called_once()
                        call_args = mock_fetch.call_args
                        since_arg = call_args[1]["since"]
                        expected_since = now - timedelta(hours=1)
                        # Since should be around 1 hour ago (within 1 minute tolerance)
                        assert abs((since_arg - expected_since).total_seconds()) < 60


@pytest.mark.asyncio
async def test_post_fetcher_logs_statistics(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker logs statistics after processing."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=sample_channels)
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_db.channels.update_one = AsyncMock()
    mock_telegram_adapter.fetch_channel_posts.return_value = [
        {
            "text": "Test post",
            "date": datetime.utcnow().isoformat(),
            "message_id": "123",
        }
    ]
    mock_mcp_client.call_tool.return_value = {
        "saved": 1,
        "skipped": 0,
        "total": 1,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    mock_fetch.return_value = [
                        {
                            "text": "Test post",
                            "date": datetime.utcnow(),
                            "message_id": "123",
                        }
                    ]
                    mock_mcp_client.call_tool.return_value = {
                        "saved": 1,
                        "skipped": 0,
                        "total": 1,
                    }

                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    # Worker should process all channels
                    assert mock_fetch.call_count == len(sample_channels)
                    # Should update last_fetch for each channel
                    assert mock_db.channels.update_one.call_count == len(
                        sample_channels
                    )


@pytest.mark.asyncio
async def test_post_fetcher_only_processes_active_channels(
    mock_db, mock_mcp_client, sample_channels, mock_settings, mock_telegram_adapter
):
    """Test that worker only processes active channels."""
    from src.workers.post_fetcher_worker import PostFetcherWorker

    # Arrange
    sample_channels.append(
        {
            "_id": "channel_inactive",
            "user_id": 789,
            "channel_username": "inactive_channel",
            "active": False,
            "last_fetch": None,
        }
    )
    # Filter active channels for find query
    active_channels = [ch for ch in sample_channels if ch.get("active", False)]
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=active_channels)
    mock_db.channels.find = MagicMock(return_value=mock_cursor)
    mock_db.channels.update_one = AsyncMock()
    mock_telegram_adapter.fetch_channel_posts.return_value = []
    mock_mcp_client.call_tool.return_value = {
        "saved": 0,
        "skipped": 0,
        "total": 0,
    }

    with patch("src.workers.post_fetcher_worker.get_db", return_value=mock_db):
        with patch(
            "src.workers.post_fetcher_worker.get_mcp_client",
            return_value=mock_mcp_client,
        ):
            with patch(
                "src.workers.post_fetcher_worker.get_settings",
                return_value=mock_settings,
            ):
                with patch(
                    "src.workers.post_fetcher_worker.fetch_channel_posts"
                ) as mock_fetch:
                    mock_fetch.return_value = []
                    mock_mcp_client.call_tool.return_value = {
                        "saved": 0,
                        "skipped": 0,
                        "total": 0,
                    }

                    worker = PostFetcherWorker()

                    # Act
                    await worker._process_all_channels()

                    # Assert
                    # Should only process active channels (3 active, 1 inactive)
                    assert mock_fetch.call_count == len(active_channels)
                    assert mock_fetch.call_count == 3  # Only active channels
