"""Tests for channel_metadata guard fixes."""

import pytest
from unittest.mock import AsyncMock, patch

from src.presentation.mcp.tools.channels.channel_metadata import get_channel_metadata


@pytest.mark.asyncio
async def test_get_channel_metadata_no_unbound_error_when_not_found():
    """Should return structured error, not raise UnboundLocalError.
    
    Purpose:
        Test that get_channel_metadata handles missing channel gracefully
        without UnboundLocalError when channel is not initialized.
    """
    # Arrange: channel does not exist in DB and search fails
    with patch("src.presentation.mcp.tools.channels.channel_metadata.get_database") as mock_db:
        db_mock = AsyncMock()
        mock_db.return_value = db_mock
        
        # Mock empty results from all queries
        db_mock.channels.find_one.return_value = None
        db_mock.channels.find.return_value.to_list = AsyncMock(return_value=[])
        
        # Mock Telegram search to return empty
        with patch(
            "src.presentation.mcp.tools.channels.channel_metadata.search_channels_by_name",
            new_callable=AsyncMock,
            return_value=[]
        ):
            # Act: should not raise UnboundLocalError
            result = await get_channel_metadata("nonexistent_channel", user_id=123)
        
        # Assert: structured error response
        assert result["success"] is False
        assert "error" in result
        assert "message" in result
        assert "nonexistent_channel" in result.get("channel_username", "")


@pytest.mark.asyncio
async def test_get_channel_metadata_no_unbound_error_when_user_id_none():
    """Should handle case when user_id is None and input is not title.
    
    Purpose:
        Test that channel is initialized even when input_is_title condition
        doesn't execute (user_id is None).
    """
    # Arrange: user_id is None, input is not a title (username-like)
    with patch("src.presentation.mcp.tools.channels.channel_metadata.get_database") as mock_db:
        db_mock = AsyncMock()
        mock_db.return_value = db_mock
        
        # Mock empty results
        db_mock.channels.find_one.return_value = None
        db_mock.channels.find.return_value.to_list = AsyncMock(return_value=[])
        
        # Mock Telegram search to return empty
        with patch(
            "src.presentation.mcp.tools.channels.channel_metadata.search_channels_by_name",
            new_callable=AsyncMock,
            return_value=[]
        ):
            # Act: should not raise UnboundLocalError
            result = await get_channel_metadata("onaboka", user_id=None)
        
        # Assert: structured error response
        assert result["success"] is False
        assert "error" in result

