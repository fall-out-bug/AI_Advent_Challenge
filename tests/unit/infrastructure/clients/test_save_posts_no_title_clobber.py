"""Tests for _save_posts_to_db title preservation."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.infrastructure.clients.telegram_utils import _save_posts_to_db


@pytest.mark.asyncio
async def test_save_posts_preserves_existing_title():
    """Should not overwrite title with input when updating username.
    
    Purpose:
        Test that when updating channel_username from incorrect value
        (e.g., "Набока" -> "onaboka"), the existing title is preserved.
    """
    # Arrange: DB has channel with title="Набока орёт в борщ", username="Набока" (wrong)
    user_id = 123
    original_username = "Набока"  # Wrong username (actually a title)
    actual_username = "onaboka"  # Correct username from Telegram
    existing_title = "Набока орёт в борщ"
    
    posts = [
        {
            "channel": actual_username,  # Actual username from Telegram
            "text": "Test post",
            "date": datetime.utcnow(),
            "message_id": "123",
        }
    ]
    
    # Mock DB with existing channel
    mock_db = AsyncMock()
    mock_channel_doc = {
        "_id": "channel_id_123",
        "user_id": user_id,
        "channel_username": original_username,
        "title": existing_title,
        "active": True,
    }
    
    mock_db.channels.update_one = AsyncMock()
    mock_db.channels.find_one = AsyncMock(return_value=mock_channel_doc)
    
    # Mock get_db from mongo module (used in _update_channel_username_in_db)
    # Mock save_posts_to_db MCP tool - patch before importing digest_tools
    async def mock_save_posts(*args, **kwargs):
        return {"saved": 1, "skipped": 0, "total": 1}
    
    with patch("src.infrastructure.database.mongo.get_db", new_callable=AsyncMock, return_value=mock_db):
        # Patch the import path before it's loaded
        with patch(
            "src.presentation.mcp.tools.digest_tools.save_posts_to_db",
            new_callable=AsyncMock,
            side_effect=mock_save_posts
        ):
            # Act: save posts with actual_username different from input
            await _save_posts_to_db(posts, original_username, user_id)
    
    # Assert: update_one was called, but title was NOT overwritten with input
    assert mock_db.channels.update_one.called
    call_args = mock_db.channels.update_one.call_args
    
    # Check that update_one was called with correct filter
    filter_dict = call_args[0][0]
    assert filter_dict["user_id"] == user_id
    assert filter_dict["channel_username"] == original_username
    assert filter_dict["active"] is True
    
    # Check that $set only contains channel_username, NOT title
    update_dict = call_args[0][1]
    set_dict = update_dict["$set"]
    assert set_dict["channel_username"] == actual_username
    assert "title" not in set_dict, "Title should not be updated from input parameter"


@pytest.mark.asyncio
async def test_save_posts_no_update_when_username_same():
    """Should not update channel if username is already correct.
    
    Purpose:
        Test that if actual_username equals input channel_username,
        no database update is performed.
    """
    user_id = 123
    channel_username = "onaboka"
    
    posts = [
        {
            "channel": channel_username,  # Same as input
            "text": "Test post",
            "date": datetime.utcnow(),
            "message_id": "123",
        }
    ]
    
    mock_db = AsyncMock()
    
    # Mock get_db from mongo module (used in _update_channel_username_in_db)
    # Mock save_posts_to_db MCP tool
    async def mock_save_posts(*args, **kwargs):
        return {"saved": 1, "skipped": 0, "total": 1}
    
    with patch("src.infrastructure.database.mongo.get_db", new_callable=AsyncMock, return_value=mock_db):
        with patch(
            "src.presentation.mcp.tools.digest_tools.save_posts_to_db",
            side_effect=mock_save_posts
        ):
            # Act
            await _save_posts_to_db(posts, channel_username, user_id)
    
    # Assert: update_one should NOT be called
    assert not mock_db.channels.update_one.called, "Should not update when username is same"

