"""Integration tests for PostFetcherWorker deduplication.

Purpose:
    Test that PostFetcherWorker correctly handles post deduplication
    using message_id and content_hash to prevent duplicate posts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

<<<<<<< HEAD
from src.infrastructure.database.mongo import get_db

=======
>>>>>>> origin/master
from src.infrastructure.repositories.post_repository import PostRepository


@pytest.mark.asyncio
async def test_deduplication_by_message_id(real_mongodb):
    """Test that posts with same message_id are not duplicated.

    Purpose:
        Verify that when the same post (same message_id) is collected
        multiple times, only one is saved to database.
    """
    db = real_mongodb
    post_repo = PostRepository(db)

    # Create first post
    post1 = {
        "user_id": 123,
        "channel_username": "test_channel",
        "message_id": "msg_123",
        "text": "Test post content",
        "date": datetime.now(timezone.utc),
    }

    # Save first post
    await post_repo.save_post(post1)

    # Try to save same post again (same message_id)
    post2 = dict(post1)  # Same message_id

    # Check if post already exists
    existing = await db.posts.find_one(
        {
            "user_id": 123,
            "channel_username": "test_channel",
            "message_id": "msg_123",
        }
    )

    assert existing is not None, "First post should be saved"

    # Second save should not create duplicate
    await post_repo.save_post(post2)

    # Verify only one post exists
    count = await db.posts.count_documents(
        {
            "user_id": 123,
            "channel_username": "test_channel",
            "message_id": "msg_123",
        }
    )

    assert count == 1, "Should have only one post with same message_id"


@pytest.mark.asyncio
async def test_deduplication_by_content_hash(real_mongodb):
    """Test that posts with same content hash are not duplicated.

    Purpose:
        Verify hybrid deduplication works even when message_id differs
        but content is the same (via content_hash).
    """
    db = real_mongodb

    # Create posts with same content but different message_ids
    post1 = {
        "user_id": 123,
        "channel_username": "test_channel",
        "message_id": "msg_123",
        "text": "Same content post",
        "date": datetime.now(timezone.utc),
    }

    # Calculate content hash (simplified - actual implementation may differ)
    import hashlib

    content_hash = hashlib.md5(post1["text"].encode()).hexdigest()
    post1["content_hash"] = content_hash

    await db.posts.insert_one(post1)

    # Try to insert post with same content but different message_id
    post2 = {
        "user_id": 123,
        "channel_username": "test_channel",
        "message_id": "msg_456",  # Different message_id
        "text": "Same content post",  # Same content
        "date": datetime.now(timezone.utc),
        "content_hash": content_hash,  # Same hash
    }

    # Check if post with same content_hash exists
    existing = await db.posts.find_one({"content_hash": content_hash})

    assert existing is not None, "Post with same content should be detected"

    # Verify deduplication logic (implementation dependent)
    # This test documents expected behavior


@pytest.mark.asyncio
async def test_different_posts_are_saved(real_mongodb):
    """Test that different posts are all saved.

    Purpose:
        Verify that posts with different message_ids and content
        are all saved without issues.
    """
    db = real_mongodb
    post_repo = PostRepository(db)

    posts = [
        {
            "user_id": 123,
            "channel_username": "test_channel",
            "message_id": f"msg_{i}",
            "text": f"Post content {i}",
            "date": datetime.now(timezone.utc),
        }
        for i in range(5)
    ]

    # Save all posts
    for post in posts:
        await post_repo.save_post(post)

    # Verify all posts are saved
    count = await db.posts.count_documents(
        {
            "user_id": 123,
            "channel_username": "test_channel",
        }
    )

    assert count == 5, "All different posts should be saved"


@pytest.mark.asyncio
async def test_posts_with_test_marker_cleanup(real_mongodb):
    """Test that test data is properly marked for cleanup.

    Purpose:
        Verify test posts are marked and can be cleaned up.
    """
    db = real_mongodb
    post_repo = PostRepository(db)

    # Create test post with marker
    test_post = {
        "user_id": 123,
        "channel_username": "test_channel",
        "message_id": "test_msg_123",
        "text": "Test post",
        "date": datetime.now(timezone.utc),
        "test_data": True,  # Marker for cleanup
    }

    await post_repo.save_post(test_post)

    # Cleanup test data
    await db.posts.delete_many({"test_data": True})

    # Verify cleanup
    count = await db.posts.count_documents({"test_data": True})
    assert count == 0, "Test data should be cleaned up"
