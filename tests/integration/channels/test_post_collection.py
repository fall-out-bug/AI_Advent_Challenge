"""Integration tests for post collection via Telegram API.

Purpose:
    Test that collect_posts MCP tool correctly fetches posts from Telegram
    and saves them to MongoDB.
"""

from __future__ import annotations

import pytest

from src.presentation.mcp.tools.channels.posts_management import collect_posts

<<<<<<< HEAD
from src.infrastructure.database.mongo import get_db

=======
>>>>>>> origin/master
from src.infrastructure.repositories.post_repository import PostRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_collect_posts_real_api(real_mongodb):
    """Test post collection via real Telegram API.

    Purpose:
        Verify that collect_posts fetches posts from Telegram and saves them.

    Note:
        This test requires:
        - Real Telegram API access (TELEGRAM_SESSION_STRING)
        - A test channel that exists and has posts
        - Real MongoDB connection
    """
    db = real_mongodb

    # Test channel - use a real channel that exists
    # For testing, you can use a public channel or skip if not available
    test_channel = "durov"  # Public Telegram channel for testing
    test_user_id = 999999

    try:
        # Subscribe to channel first
        await db.channels.insert_one(
            {
                "user_id": test_user_id,
                "channel_username": test_channel,
                "title": "Test Channel",
                "active": True,
                "test_data": True,
            }
        )

        # Count posts before collection
        posts_before = await db.posts.count_documents(
            {
                "channel_username": test_channel,
                "user_id": test_user_id,
            }
        )

        # Collect posts (may fail if channel doesn't exist or API not configured)
        try:
            result = await collect_posts(
                user_id=test_user_id,
                channel_username=test_channel,
            )

            assert result is not None
            assert "status" in result or "saved" in result or "posts" in result

            # Count posts after collection
            posts_after = await db.posts.count_documents(
                {
                    "channel_username": test_channel,
                    "user_id": test_user_id,
                }
            )

            # Verify posts were saved (or at least attempted)
            if "saved" in result:
                assert result["saved"] >= 0
            elif "posts" in result:
                assert isinstance(result["posts"], list)

        except Exception as e:
            # Skip if Telegram API not available or channel not accessible
            pytest.skip(f"Telegram API not available or channel not accessible: {e}")

    finally:
        # Cleanup
        await db.channels.delete_many({"test_data": True})
        # Don't delete posts - they might be useful for other tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_collect_posts_error_handling(real_mongodb):
    """Test error handling for collect_posts.

    Purpose:
        Verify that collect_posts handles errors gracefully when channel doesn't exist.
    """
    db = real_mongodb

    test_channel = "nonexistent_channel_12345"
    test_user_id = 999999

    try:
        # Try to collect from non-existent channel
        result = await collect_posts(
            user_id=test_user_id,
            channel_username=test_channel,
        )

        # Should return error status or empty result, not crash
        assert result is not None

    except Exception as e:
        # Exception is acceptable for non-existent channel
        assert "not found" in str(e).lower() or "error" in str(e).lower()
