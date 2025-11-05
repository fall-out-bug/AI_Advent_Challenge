"""Tests for SubscribeToChannelWithCollectionUseCase."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.application.use_cases.subscribe_with_collection import (
    SubscribeToChannelWithCollectionUseCase,
    SubscribeWithCollectionResult,
)


@pytest.mark.asyncio
async def test_subscribe_with_collection_success():
    """Test successful subscription with post collection.
    
    Purpose:
        Test that use case subscribes to channel and collects posts,
        returning correct result.
    """
    # Arrange
    user_id = 123
    channel_username = "onaboka"
    collected_count = 5
    
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(side_effect=[
        {"status": "subscribed", "channel_id": "channel_123"},  # add_channel
        {"status": "success", "collected_count": collected_count}  # collect_posts
    ])
    
    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    
    # Act
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)
    
    # Assert
    assert isinstance(result, SubscribeWithCollectionResult)
    assert result.status == "subscribed"
    assert result.channel_username == channel_username
    assert result.collected_count == collected_count
    assert result.error is None
    
    # Verify MCP calls
    assert mock_mcp.call_tool.call_count == 2
    add_call = mock_mcp.call_tool.call_args_list[0]
    assert add_call[0][0] == "add_channel"
    assert add_call[0][1]["user_id"] == user_id
    assert add_call[0][1]["channel_username"] == channel_username
    
    collect_call = mock_mcp.call_tool.call_args_list[1]
    assert collect_call[0][0] == "collect_posts"
    assert collect_call[0][1]["user_id"] == user_id
    assert collect_call[0][1]["channel_username"] == channel_username
    assert collect_call[0][1]["wait_for_completion"] is True
    assert collect_call[0][1]["hours"] == 72
    assert collect_call[0][1]["fallback_to_7_days"] is True


@pytest.mark.asyncio
async def test_subscribe_with_collection_already_subscribed():
    """Test subscription when already subscribed.
    
    Purpose:
        Test that use case still collects posts even if already subscribed.
    """
    # Arrange
    user_id = 123
    channel_username = "onaboka"
    collected_count = 3
    
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(side_effect=[
        {"status": "already_subscribed", "channel_id": "channel_123"},
        {"status": "success", "collected_count": collected_count}
    ])
    
    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    
    # Act
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)
    
    # Assert
    assert result.status == "already_subscribed"
    assert result.collected_count == collected_count


@pytest.mark.asyncio
async def test_subscribe_with_collection_collect_fails():
    """Test when subscription succeeds but collection fails.
    
    Purpose:
        Test that subscription succeeds even if collection fails,
        and error is reported.
    """
    # Arrange
    user_id = 123
    channel_username = "onaboka"
    
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(side_effect=[
        {"status": "subscribed", "channel_id": "channel_123"},
        {"status": "error", "error": "pyrogram_not_available"}  # collect_posts fails
    ])
    
    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    
    # Act
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)
    
    # Assert
    assert result.status == "subscribed"
    assert result.collected_count == 0
    assert result.error is not None
    assert "pyrogram" in result.error.lower() or "collection" in result.error.lower()


@pytest.mark.asyncio
async def test_subscribe_with_collection_subscription_fails():
    """Test when subscription itself fails.
    
    Purpose:
        Test that use case returns error status when subscription fails.
    """
    # Arrange
    user_id = 123
    channel_username = "invalid_channel"
    
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(return_value={
        "status": "error",
        "error": "channel_validation_failed",
        "message": "Channel not found"
    })
    
    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    
    # Act
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)
    
    # Assert
    assert result.status == "error"
    assert result.error is not None
    assert result.collected_count == 0
    # Should not call collect_posts if subscription fails
    assert mock_mcp.call_tool.call_count == 1

