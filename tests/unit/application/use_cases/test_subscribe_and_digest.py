"""Tests for SubscribeAndGenerateDigestUseCase."""

import pytest
from unittest.mock import AsyncMock, patch

from src.application.use_cases.subscribe_and_generate_digest import (
    SubscribeAndGenerateDigestUseCase,
    DigestResult,
)
from src.application.use_cases.subscribe_with_collection import (
    SubscribeWithCollectionResult,
)


@pytest.mark.asyncio
async def test_subscribe_and_digest_new_channel():
    """Test subscribe and digest for new channel.

    Purpose:
        Test full flow: subscribe → collect → generate digest.
    """
    # Arrange
    user_id = 123
    channel_username = "onaboka"
    hours = 72
    collected_count = 5
    digest_summary = "Test digest summary"

    # Mock subscribe use case
    mock_subscribe_result = SubscribeWithCollectionResult(
        status="subscribed",
        channel_username=channel_username,
        collected_count=collected_count,
    )

    # Mock MCP client
    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        return_value={
            "digests": [
                {
                    "channel": channel_username,
                    "summary": digest_summary,
                    "post_count": collected_count,
                    "tags": [],
                }
            ],
            "channel": channel_username,
            "generated_at": "2024-01-01T00:00:00",
        }
    )

    # Mock subscribe use case
    with patch(
        "src.application.use_cases.subscribe_and_generate_digest.SubscribeToChannelWithCollectionUseCase"
    ) as mock_subscribe_class:
        mock_subscribe_instance = AsyncMock()
        mock_subscribe_instance.execute = AsyncMock(return_value=mock_subscribe_result)
        mock_subscribe_class.return_value = mock_subscribe_instance

        use_case = SubscribeAndGenerateDigestUseCase(mcp_client=mock_mcp)

        # Act
        result = await use_case.execute(
            user_id=user_id,
            channel_username=channel_username,
            hours=hours,
        )

    # Assert
    assert isinstance(result, DigestResult)
    assert result.status == "success"
    assert result.channel_username == channel_username
    assert result.summary == digest_summary
    assert result.post_count == collected_count
    assert result.collected_count == collected_count


@pytest.mark.asyncio
async def test_subscribe_and_digest_no_posts_collected():
    """Test when no posts collected after subscription.

    Purpose:
        Test that digest returns appropriate message when no posts found.
    """
    # Arrange
    user_id = 123
    channel_username = "onaboka"
    hours = 72

    mock_subscribe_result = SubscribeWithCollectionResult(
        status="subscribed",
        channel_username=channel_username,
        collected_count=0,
    )

    mock_mcp = AsyncMock()
    mock_mcp.call_tool = AsyncMock(
        return_value={
            "digests": [],
            "channel": channel_username,
            "message": "За последние 72 часов постов не найдено",
        }
    )

    with patch(
        "src.application.use_cases.subscribe_and_generate_digest.SubscribeToChannelWithCollectionUseCase"
    ) as mock_subscribe_class:
        mock_subscribe_instance = AsyncMock()
        mock_subscribe_instance.execute = AsyncMock(return_value=mock_subscribe_result)
        mock_subscribe_class.return_value = mock_subscribe_instance

        use_case = SubscribeAndGenerateDigestUseCase(mcp_client=mock_mcp)

        # Act
        result = await use_case.execute(
            user_id=user_id,
            channel_username=channel_username,
            hours=hours,
        )

    # Assert
    assert result.status == "success"
    assert result.summary is None or "не найдено" in result.summary.lower()
    assert result.post_count == 0


@pytest.mark.asyncio
async def test_subscribe_and_digest_subscription_fails():
    """Test when subscription fails.

    Purpose:
        Test that use case returns error when subscription fails.
    """
    # Arrange
    user_id = 123
    channel_username = "invalid_channel"

    mock_subscribe_result = SubscribeWithCollectionResult(
        status="error",
        channel_username=channel_username,
        collected_count=0,
        error="Channel not found",
    )

    mock_mcp = AsyncMock()

    with patch(
        "src.application.use_cases.subscribe_and_generate_digest.SubscribeToChannelWithCollectionUseCase"
    ) as mock_subscribe_class:
        mock_subscribe_instance = AsyncMock()
        mock_subscribe_instance.execute = AsyncMock(return_value=mock_subscribe_result)
        mock_subscribe_class.return_value = mock_subscribe_instance

        use_case = SubscribeAndGenerateDigestUseCase(mcp_client=mock_mcp)

        # Act
        result = await use_case.execute(
            user_id=user_id,
            channel_username=channel_username,
        )

    # Assert
    assert result.status == "error"
    assert result.error is not None
    assert result.summary is None
    # Should not call get_channel_digest_by_name if subscription fails
    assert mock_mcp.call_tool.call_count == 0
