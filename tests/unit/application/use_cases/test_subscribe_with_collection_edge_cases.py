"""Edge case tests for SubscribeToChannelWithCollectionUseCase."""

import pytest
from unittest.mock import AsyncMock

from src.application.use_cases.subscribe_with_collection import (
    SubscribeToChannelWithCollectionUseCase,
    SubscribeWithCollectionResult,
)


@pytest.mark.asyncio
async def test_subscribe_with_collection_empty_search_results():
    """Test when no channels found in search.

    Purpose:
        Test that use case handles empty search results gracefully.
    """
    # This test is handled at handler level, but use case should handle
    # if subscription fails due to channel not found
    user_id = 123
    channel_username = "nonexistent_channel"

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        return_value={
            "status": "error",
            "error": "channel_validation_failed",
            "message": "Channel not found",
        }
    )

    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)

    assert result.status == "error"
    assert result.collected_count == 0
    assert "not found" in result.error.lower() or "validation" in result.error.lower()


@pytest.mark.asyncio
async def test_subscribe_with_collection_timeout():
    """Test when post collection times out.

    Purpose:
        Test that timeout is handled gracefully and subscription still succeeds.
    """
    import asyncio

    user_id = 123
    channel_username = "onaboka"

    mock_mcp = AsyncMock()

    async def slow_collect(*args, **kwargs):
        await asyncio.sleep(70)  # Longer than timeout
        return {"status": "success", "collected_count": 5}

    # First call returns subscription, second call is slow_collect
    call_count = 0

    async def call_tool_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"status": "subscribed", "channel_id": "channel_123"}
        else:
            return await slow_collect()

    mock_mcp.call_tool = AsyncMock(side_effect=call_tool_side_effect)

    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)

    assert result.status == "subscribed"
    assert result.collected_count == 0
    assert result.error is not None
    assert "timeout" in result.error.lower() or "фоне" in result.error.lower()


@pytest.mark.asyncio
async def test_subscribe_with_collection_pyrogram_not_available():
    """Test when Pyrogram is not available for collection.

    Purpose:
        Test that missing Pyrogram config is handled gracefully.
    """
    user_id = 123
    channel_username = "onaboka"

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        side_effect=[
            {"status": "subscribed", "channel_id": "channel_123"},
            {
                "status": "error",
                "error": "telegram_config_missing",
            },  # Pyrogram not available
        ]
    )

    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)

    assert result.status == "subscribed"
    assert result.collected_count == 0
    assert "автоматически" in result.error.lower() or "skipped" in result.error.lower()


@pytest.mark.asyncio
async def test_subscribe_with_collection_zero_posts_collected():
    """Test when collection succeeds but finds 0 posts.

    Purpose:
        Test that 0 posts is still considered success.
    """
    user_id = 123
    channel_username = "onaboka"

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        side_effect=[
            {"status": "subscribed", "channel_id": "channel_123"},
            {"status": "success", "collected_count": 0},  # No posts found
        ]
    )

    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)

    assert result.status == "subscribed"
    assert result.collected_count == 0
    assert result.error is None  # No error - channel just has no recent posts


@pytest.mark.asyncio
async def test_subscribe_with_collection_exception_during_collection():
    """Test when exception occurs during collection.

    Purpose:
        Test that exceptions are caught and reported correctly.
    """
    user_id = 123
    channel_username = "onaboka"

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        side_effect=[
            {"status": "subscribed", "channel_id": "channel_123"},
            Exception("Network error"),  # Exception during collection
        ]
    )

    use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=mock_mcp)
    result = await use_case.execute(user_id=user_id, channel_username=channel_username)

    assert result.status == "subscribed"
    assert result.collected_count == 0
    assert result.error is not None
    assert "error" in result.error.lower() or "exception" in result.error.lower()
