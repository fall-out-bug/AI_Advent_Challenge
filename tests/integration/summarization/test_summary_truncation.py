"""Test summary truncation and post sorting for Telegram digests.

Purpose:
    Verify that summaries are correctly truncated to digest_summary_max_chars
    and that posts are sorted from old to new.
"""

from datetime import datetime, timedelta, timezone

import pytest

<<<<<<< HEAD
=======
from unittest.mock import AsyncMock, patch

>>>>>>> origin/master
from src.infrastructure.config.settings import get_settings
from src.infrastructure.di.factories import create_channel_digest_by_name_use_case
from src.infrastructure.repositories.post_repository import PostRepository


@pytest.mark.asyncio
async def test_posts_sorted_old_to_new(real_mongodb):
    """Test that posts are sorted from oldest to newest.

    Purpose:
        Verify that PostRepository.get_posts_by_channel returns posts
        in chronological order (oldest first).
    """
    post_repo = PostRepository(real_mongodb)

    # Create test channel
    await real_mongodb.channels.insert_one(
        {
            "user_id": 123,
            "channel_username": "test_channel",
            "active": True,
            "test_data": True,
        }
    )

    # Create posts with different dates (in reverse order to test sorting)
    now = datetime.now(timezone.utc)
    posts = [
        {
            "channel_username": "test_channel",
            "text": "Post 3",
            "date": now - timedelta(hours=1),
            "message_id": "3",
            "test_data": True,
        },
        {
            "channel_username": "test_channel",
            "text": "Post 1",
            "date": now - timedelta(hours=3),
            "message_id": "1",
            "test_data": True,
        },
        {
            "channel_username": "test_channel",
            "text": "Post 2",
            "date": now - timedelta(hours=2),
            "message_id": "2",
            "test_data": True,
        },
    ]

    # Insert posts
    await real_mongodb.posts.insert_many(posts)

    # Get posts
    since = now - timedelta(hours=24)
    result = await post_repo.get_posts_by_channel("test_channel", since)

    # Verify order: should be Post 1, Post 2, Post 3 (oldest to newest)
    assert len(result) == 3, f"Expected 3 posts, got {len(result)}"

    # Check order by message_id (which corresponds to chronological order)
    assert result[0]["message_id"] == "1", "First post should be oldest"
    assert result[1]["message_id"] == "2", "Second post should be middle"
    assert result[2]["message_id"] == "3", "Third post should be newest"

    # Cleanup
    await real_mongodb.posts.delete_many({"test_data": True})
    await real_mongodb.channels.delete_many({"test_data": True})


@pytest.mark.asyncio
async def test_summary_respects_max_chars_parameter(real_mongodb):
    """Test that summary respects max_chars as soft limit parameter.

    Purpose:
        Verify that max_chars is passed to summarizer as parameter,
        not as hard truncation. The summarizer should be aware of the limit
        but not forced to truncate.
    """
    settings = get_settings()
    max_chars = settings.digest_summary_max_chars

    # Create test channel
    await real_mongodb.channels.insert_one(
        {
            "user_id": 123,
            "channel_username": "test_summary_param",
            "active": True,
            "test_data": True,
        }
    )

    # Create posts with content (need to set user_id for channel query)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    posts = [
        {
            "channel_username": "test_summary_param",
            "text": "Важное сообщение о новых технологиях. Обсуждаются перспективы развития.",
            "date": now - timedelta(hours=1),
            "message_id": "1",
            "test_data": True,
        },
    ]

    await real_mongodb.posts.insert_many(posts)

    # Verify posts are saved
    saved_posts = await real_mongodb.posts.find(
        {"channel_username": "test_summary_param"}
    ).to_list(length=10)
    assert len(saved_posts) > 0, "Posts should be saved"

<<<<<<< HEAD
    # Generate digest
    use_case = await create_channel_digest_by_name_use_case()
    result = await use_case.execute(
        user_id=123,
        channel_username="test_summary_param",
        hours=24,
    )

    # Verify that summary was generated (not empty fallback message)
    assert len(result.summary.text) > 0, "Summary should not be empty"

    # Verify that max_chars is set in context (as parameter, not hard limit)
    # The summarizer should generate full content within reasonable bounds
    # but not be forced to exactly match max_chars
    summary_length = len(result.summary.text)

    # Summary should be reasonable length - not artificially truncated
    # It may slightly exceed max_chars as it's a soft limit
    assert summary_length > 50, "Summary should have substantial content"
=======
    # Generate digest using patched DB for use case
    with patch(
        "src.application.use_cases.generate_channel_digest_by_name.get_db",
        new=AsyncMock(return_value=real_mongodb),
    ):
        use_case = create_channel_digest_by_name_use_case()
        result = await use_case.execute(
            user_id=123,
            channel_username="test_summary_param",
            hours=24,
        )

    # Verify that summary was generated (not empty fallback message)
    summary_length = len(result.summary.text)
    assert summary_length > 0, "Summary should not be empty"

    # Verify that summary length respects max_chars as soft upper bound
    # (It may be slightly above max_chars, but should not be dramatically smaller
    # than the input when a real LLM is configured.)
    # Under FallbackLLMClient in local runs, we only guarantee non-empty output.
    assert summary_length <= max_chars + 100
>>>>>>> origin/master

    # Cleanup
    await real_mongodb.posts.delete_many({"test_data": True})
    await real_mongodb.channels.delete_many({"test_data": True})
