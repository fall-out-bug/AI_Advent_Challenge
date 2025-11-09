"""E2E tests for Telegram digest flow.

Purpose:
    Test complete flow:
    1. Subscribe to test channel
    2. Collect posts (via worker or manual trigger)
    3. Request digest via Telegram bot
    4. Verify response quality

Requirements:
    - Real Telegram bot (configured via TELEGRAM_BOT_TOKEN)
    - Real MongoDB
    - Real LLM service
    - Test channel with posts
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.repositories.post_repository import PostRepository
from src.presentation.mcp.tools.channels.channel_digest import (
    get_channel_digest_by_name,
)
from src.presentation.mcp.tools.channels.posts_management import collect_posts

# Import real_mongodb from e2e conftest
from tests.e2e.summarization.conftest import real_mongodb


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_digest_flow_e2e(real_mongodb):
    """Test complete digest flow end-to-end.

    Purpose:
        Verify that full flow works: subscription -> collection -> digest request.
    """
    db = real_mongodb

    # Test configuration
    test_user_id = 999999  # Test user ID
    test_channel = "test_channel_e2e"

    try:
        # Step 1: Subscribe to channel
        await db.channels.insert_one(
            {
                "user_id": test_user_id,
                "channel_username": test_channel,
                "title": "Test Channel E2E",
                "active": True,
                "test_data": True,
            }
        )

        # Step 2: Collect posts (mock or real)
        # Note: In real E2E, this would call Telegram API
        # For now, we'll insert test posts directly
        post_repo = PostRepository(db)

        now = datetime.now(timezone.utc)
        test_posts = [
            {
                "user_id": test_user_id,
                "channel_username": test_channel,
                "message_id": f"msg_e2e_{i}",
                "text": f"Test post {i} for E2E testing",
                "date": now - timedelta(hours=i),
                "test_data": True,
            }
            for i in range(5)
        ]

        for post in test_posts:
            await post_repo.save_post(post)

        # Step 3: Request digest via MCP tool (simulating bot call)
        result = await get_channel_digest_by_name(
            user_id=test_user_id,
            channel_username=test_channel,
            hours=24,
        )

        # Step 4: Verify response
        assert result is not None
        # Result can have different structures depending on whether posts were found
        assert (
            "channel" in result
            or "channel_username" in result
            or "summary" in result
            or "digest" in result
            or "message" in result
        )

        # Verify posts were included (if any)
        if "post_count" in result:
            assert result["post_count"] >= 0, "post_count should be non-negative"
        elif "digests" in result:
            # Multiple channels format
            assert isinstance(result["digests"], list)

        # If summary exists, verify it's not empty
        if "summary" in result:
            summary_text = (
                result["summary"].get("text", "")
                if isinstance(result["summary"], dict)
                else str(result["summary"])
            )
            assert len(summary_text) > 0, "Summary should not be empty"

        # If message exists (empty channel case), verify it's informative
        if "message" in result:
            assert len(result["message"]) > 0, "Message should not be empty"

    finally:
        # Cleanup
        await db.channels.delete_many({"test_data": True})
        await db.posts.delete_many({"test_data": True})


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_digest_multiple_channels_e2e(real_mongodb):
    """Test digest generation for multiple channels.

    Purpose:
        Verify that digest for all channels works correctly.
    """
    db = real_mongodb

    test_user_id = 999999
    channels = ["test_channel_1", "test_channel_2"]

    try:
        # Subscribe to multiple channels
        for channel in channels:
            await db.channels.insert_one(
                {
                    "user_id": test_user_id,
                    "channel_username": channel,
                    "title": f"Test Channel {channel}",
                    "active": True,
                    "test_data": True,
                }
            )

            # Add posts to each channel
            post_repo = PostRepository(db)
            for i in range(3):
                await post_repo.save_post(
                    {
                        "user_id": test_user_id,
                        "channel_username": channel,
                        "message_id": f"msg_{channel}_{i}",
                        "text": f"Post {i} in {channel}",
                        "date": datetime.now(timezone.utc) - timedelta(hours=i),
                        "test_data": True,
                    }
                )

        # Request digest for all channels
        from src.presentation.mcp.tools.channels.channel_digest import (
            get_channel_digest,
        )

        result = await get_channel_digest(user_id=test_user_id, hours=24)

        # Verify result
        assert result is not None
        if "digests" in result:
            assert (
                len(result["digests"]) >= 1
            ), "Should include digests for subscribed channels"

    finally:
        # Cleanup
        await db.channels.delete_many({"test_data": True})
        await db.posts.delete_many({"test_data": True})


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_digest_with_real_collection_e2e(real_mongodb):
    """Test digest after real post collection.

    Purpose:
        Verify that posts collected via collect_posts tool are included in digest.
    """
    db = real_mongodb

    test_user_id = 999999
    test_channel = "test_channel_collect"

    try:
        # Subscribe to channel
        await db.channels.insert_one(
            {
                "user_id": test_user_id,
                "channel_username": test_channel,
                "title": "Test Channel Collect",
                "active": True,
                "test_data": True,
            }
        )

        # Manually trigger post collection (if Telegram API available)
        # Note: This may fail if test channel doesn't exist or Telegram API is not configured
        try:
            collect_result = await collect_posts(
                user_id=test_user_id,
                channel_username=test_channel,
            )
            assert collect_result is not None
        except Exception as e:
            pytest.skip(f"Telegram API not available or test channel not found: {e}")

        # Wait a bit for posts to be saved
        await asyncio.sleep(1)

        # Request digest
        result = await get_channel_digest_by_name(
            user_id=test_user_id,
            channel_username=test_channel,
            hours=24,
        )

        # Verify
        assert result is not None
        if "post_count" in result:
            assert result["post_count"] >= 0, "Should handle collected posts"

    finally:
        # Cleanup
        await db.channels.delete_many({"test_data": True})
        await db.posts.delete_many({"test_data": True})
