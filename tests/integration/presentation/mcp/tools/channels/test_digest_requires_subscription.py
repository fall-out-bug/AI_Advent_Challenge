"""Integration tests for digest requiring subscription.

Tests that digests cannot be generated without subscription.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.presentation.mcp.tools.channels.channel_digest import (
    get_channel_digest_by_name,
)


@pytest.mark.asyncio
async def test_digest_by_name_not_subscribed():
    """Test that digest returns not_subscribed when channel not subscribed.

    Purpose:
        Verify that auto-subscription is removed and proper status is returned.
    """
    # Arrange: Channel not in database
    user_id = 123
    channel_username = "newchannel"

    with patch(
        "src.presentation.mcp.tools.channels.channel_digest.get_database"
    ) as mock_db:
        db_mock = AsyncMock()
        mock_db.return_value = db_mock

        # Mock empty channel search
        db_mock.channels.find_one = AsyncMock(return_value=None)
        # Mock find() - it returns a cursor object (not async), but to_list() is async
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        # find() itself is NOT async, it returns a cursor synchronously
        db_mock.channels.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await get_channel_digest_by_name(
            user_id=user_id,
            channel_username=channel_username,
            hours=72,
        )

    # Assert: not_subscribed status
    assert result["digests"] == []
    assert result["status"] == "not_subscribed"
    assert "Подписка не найдена" in result["message"]
    assert channel_username in result["channel"]

    # Assert: No channel was inserted (auto-subscription removed)
    assert not db_mock.channels.insert_one.called


@pytest.mark.asyncio
async def test_digest_by_name_subscribed():
    """Test that digest works when channel is subscribed.

    Purpose:
        Verify that digest generation works for subscribed channels.
    """
    # Arrange: Channel exists in database
    user_id = 123
    channel_username = "onaboka"

    with patch(
        "src.presentation.mcp.tools.channels.channel_digest.get_database"
    ) as mock_db:
        db_mock = AsyncMock()
        mock_db.return_value = db_mock

        # Mock existing channel
        existing_channel = {
            "_id": "channel_id_123",
            "user_id": user_id,
            "channel_username": channel_username,
            "active": True,
            "title": "Набока орёт в борщ",
        }
        db_mock.channels.find_one = AsyncMock(return_value=existing_channel)

        # Mock posts repository
        with patch(
            "src.presentation.mcp.tools.channels.channel_digest.PostRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            # Mock posts with recent date
            from datetime import datetime, timedelta

            recent_date = datetime.utcnow() - timedelta(hours=24)

            mock_repo.get_posts_by_user_subscriptions = AsyncMock(
                return_value=[
                    {
                        "channel_username": channel_username,
                        "text": "Test post",
                        "date": recent_date,
                        "message_id": "123",
                    }
                ]
            )

            # Mock summarizer
            with patch(
                "src.presentation.mcp.tools.channels.channel_digest._generate_summary"
            ) as mock_summary:
                mock_summary.return_value = "Test summary"

                # Act
                result = await get_channel_digest_by_name(
                    user_id=user_id,
                    channel_username=channel_username,
                    hours=72,
                )

    # Assert: Digest generated
    assert result.get("digests"), f"Expected digests, got: {result}"
    assert len(result["digests"]) > 0
    assert result["digests"][0]["channel"] == channel_username
    assert result["digests"][0]["summary"] == "Test summary"
    # Status may or may not be present, but if present should not be "not_subscribed"
    if "status" in result:
        assert result["status"] != "not_subscribed"
