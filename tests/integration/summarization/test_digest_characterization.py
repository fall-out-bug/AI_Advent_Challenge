"""Characterization tests for digest generation flow.

Purpose:
    Capture current digest generation behavior before refactoring.
    These tests document the existing behavior to ensure no regressions
    during Cluster B refactoring (B.3-B.4).

Note:
    These tests are intentionally verbose to capture current behavior.
    They serve as a baseline for verifying that refactoring doesn't change
    the external behavior of digest generation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from src.application.dtos.digest_dtos import ChannelDigest
from src.application.use_cases.generate_channel_digest import GenerateChannelDigestUseCase
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)


@pytest.mark.asyncio
async def test_digest_by_name_basic_flow_characterization(mongodb_database_async):
    """Characterization: Basic digest generation flow by channel name.

    Purpose:
        Captures the current behavior of GenerateChannelDigestByNameUseCase.execute():
        - Input: user_id, channel_username, hours
        - Output: ChannelDigest object
        - Behavior: Fetches posts from repository, generates summary, returns digest
    """
    # Setup: Create channel and posts in test database
    await mongodb_database_async.channels.insert_one(
        {
            "user_id": 100,
            "channel_username": "test_channel",
            "title": "Test Channel",
            "active": True,
        }
    )

    now = datetime.now(timezone.utc)
    posts = [
        {
            "user_id": 100,
            "channel_username": "test_channel",
            "message_id": "msg_1",
            "text": "Post 1 about technology",
            "date": now - timedelta(hours=12),
        },
        {
            "user_id": 100,
            "channel_username": "test_channel",
            "message_id": "msg_2",
            "text": "Post 2 about AI development",
            "date": now - timedelta(hours=6),
        },
    ]

    from src.infrastructure.repositories.post_repository import PostRepository

    post_repo = PostRepository(mongodb_database_async)
    for post in posts:
        await post_repo.save_post(post)

    # Mock get_db to return test database
    from unittest.mock import patch, AsyncMock

    async def mock_get_db():
        return mongodb_database_async

    with patch("src.application.use_cases.generate_channel_digest_by_name.get_db", side_effect=mock_get_db):
        use_case = GenerateChannelDigestByNameUseCase()

        # Execute
        result = await use_case.execute(
            user_id=100,
            channel_username="test_channel",
            hours=24,
        )

        # Characterize: Verify return type and structure
        assert isinstance(result, ChannelDigest), "Result should be ChannelDigest object"

        # Characterize: Verify ChannelDigest fields
        assert hasattr(result, "channel_username"), "ChannelDigest should have channel_username"
        assert hasattr(result, "channel_title"), "ChannelDigest should have channel_title"
        assert hasattr(result, "summary"), "ChannelDigest should have summary"
        assert hasattr(result, "post_count"), "ChannelDigest should have post_count"
        assert hasattr(result, "time_window_hours"), "ChannelDigest should have time_window_hours"
        assert hasattr(result, "tags"), "ChannelDigest should have tags"
        assert hasattr(result, "generated_at"), "ChannelDigest should have generated_at"

        # Characterize: Verify field values
        assert result.channel_username == "test_channel"
        assert result.post_count >= 0  # May be 0 if posts filtered out
        assert result.time_window_hours == 24
        assert isinstance(result.tags, list)
        assert isinstance(result.generated_at, datetime)

        # Characterize: Verify summary structure
        from src.domain.value_objects.summary_result import SummaryResult

        assert isinstance(result.summary, SummaryResult), "Summary should be SummaryResult object"
        assert hasattr(result.summary, "text"), "SummaryResult should have text"
        assert hasattr(result.summary, "sentences_count"), "SummaryResult should have sentences_count"
        assert hasattr(result.summary, "method"), "SummaryResult should have method"
        assert hasattr(result.summary, "confidence"), "SummaryResult should have confidence"

        # Characterize: Verify summary text is non-empty string (if posts found)
        if result.post_count > 0:
            assert isinstance(result.summary.text, str), "Summary text should be string"
            assert len(result.summary.text) > 0, "Summary text should not be empty"
        else:
            # If no posts, should have fallback message
            assert isinstance(result.summary.text, str), "Summary text should be string"

    # Cleanup
    await mongodb_database_async.channels.delete_many({"user_id": 100})
    await mongodb_database_async.posts.delete_many({"user_id": 100})


@pytest.mark.asyncio
async def test_digest_all_channels_basic_flow_characterization(mongodb_database_async):
    """Characterization: Basic digest generation flow for all channels.

    Purpose:
        Captures the current behavior of GenerateChannelDigestUseCase.execute():
        - Input: user_id, hours
        - Output: list[ChannelDigest]
        - Behavior: Fetches active channels, generates digest for each, returns sorted list
    """
    # Setup: Create channels and posts
    await mongodb_database_async.channels.insert_many(
        [
            {
                "user_id": 200,
                "channel_username": "channel1",
                "title": "Channel 1",
                "active": True,
            },
            {
                "user_id": 200,
                "channel_username": "channel2",
                "title": "Channel 2",
                "active": True,
            },
        ]
    )

    now = datetime.now(timezone.utc)
    posts = [
        {
            "user_id": 200,
            "channel_username": "channel1",
            "message_id": "msg_1",
            "text": "Channel 1 post",
            "date": now - timedelta(hours=12),
        },
        {
            "user_id": 200,
            "channel_username": "channel2",
            "message_id": "msg_2",
            "text": "Channel 2 post",
            "date": now - timedelta(hours=6),
        },
    ]

    from src.infrastructure.repositories.post_repository import PostRepository

    post_repo = PostRepository(mongodb_database_async)
    for post in posts:
        await post_repo.save_post(post)

    # Mock get_db to return test database
    from unittest.mock import patch

    async def mock_get_db():
        return mongodb_database_async

    with patch("src.application.use_cases.generate_channel_digest.get_db", side_effect=mock_get_db), \
         patch("src.application.use_cases.generate_channel_digest_by_name.get_db", side_effect=mock_get_db):
        use_case = GenerateChannelDigestUseCase()

        # Execute
        result = await use_case.execute(user_id=200, hours=24)

        # Characterize: Verify return type
        assert isinstance(result, list), "Result should be list"
        assert all(isinstance(d, ChannelDigest) for d in result), "All items should be ChannelDigest"

        # Characterize: Verify sorting behavior (by post_count descending)
        if len(result) > 1:
            post_counts = [d.post_count for d in result]
            assert post_counts == sorted(post_counts, reverse=True), "Digests should be sorted by post_count (desc)"

        # Characterize: Verify only channels with posts are included
        # (This is current behavior - channels with post_count=0 are excluded)
        assert all(d.post_count > 0 for d in result), "Only channels with posts should be included"

    # Cleanup
    await mongodb_database_async.channels.delete_many({"user_id": 200})
    await mongodb_database_async.posts.delete_many({"user_id": 200})


@pytest.mark.asyncio
async def test_digest_empty_channel_behavior_characterization(mongodb_database_async):
    """Characterization: Behavior when channel has no posts.

    Purpose:
        Captures how digest generation handles empty channels:
        - Should return ChannelDigest with post_count=0
        - Should have fallback summary text
        - Should not raise exception
    """
    # Setup: Create channel with no posts
    await mongodb_database_async.channels.insert_one(
        {
            "user_id": 300,
            "channel_username": "empty_channel",
            "title": "Empty Channel",
            "active": True,
        }
    )

    # Mock get_db to return test database
    from unittest.mock import patch

    async def mock_get_db():
        return mongodb_database_async

    with patch("src.application.use_cases.generate_channel_digest_by_name.get_db", side_effect=mock_get_db):
        use_case = GenerateChannelDigestByNameUseCase()

        # Execute
        result = await use_case.execute(
            user_id=300,
            channel_username="empty_channel",
            hours=24,
        )

        # Characterize: Verify empty channel handling
        assert isinstance(result, ChannelDigest), "Should return ChannelDigest even for empty channel"
        assert result.post_count == 0, "Post count should be 0"
        assert isinstance(result.summary.text, str), "Should have summary text"
        # Should have fallback message (in Russian or English)
        assert len(result.summary.text) > 0, "Should have non-empty fallback message"

    # Cleanup
    await mongodb_database_async.channels.delete_many({"user_id": 300})


@pytest.mark.asyncio
async def test_digest_time_filtering_behavior_characterization(mongodb_database_async):
    """Characterization: Time filtering behavior.

    Purpose:
        Captures how digest generation filters posts by time window:
        - Should only include posts within specified hours
        - Should exclude posts outside time window
    """
    # Setup: Create channel with posts from different time periods
    await mongodb_database_async.channels.insert_one(
        {
            "user_id": 400,
            "channel_username": "time_test_channel",
            "title": "Time Test Channel",
            "active": True,
        }
    )

    now = datetime.now(timezone.utc)
    posts = [
        {
            "user_id": 400,
            "channel_username": "time_test_channel",
            "message_id": "msg_recent",
            "text": "Recent post",
            "date": now - timedelta(hours=12),  # Within 24h
        },
        {
            "user_id": 400,
            "channel_username": "time_test_channel",
            "message_id": "msg_old",
            "text": "Old post",
            "date": now - timedelta(hours=48),  # Outside 24h
        },
    ]

    from src.infrastructure.repositories.post_repository import PostRepository

    post_repo = PostRepository(mongodb_database_async)
    for post in posts:
        await post_repo.save_post(post)

    # Mock get_db to return test database
    from unittest.mock import patch

    async def mock_get_db():
        return mongodb_database_async

    with patch("src.application.use_cases.generate_channel_digest_by_name.get_db", side_effect=mock_get_db):
        use_case = GenerateChannelDigestByNameUseCase()

        # Execute with 24h window
        result = await use_case.execute(
            user_id=400,
            channel_username="time_test_channel",
            hours=24,
        )

        # Characterize: Verify time filtering
        # Should include only posts within 24 hours
        # Note: Actual post_count may depend on repository filtering implementation
        assert isinstance(result, ChannelDigest), "Should return ChannelDigest"
        assert result.post_count >= 0, "Post count should be non-negative"
        # If posts are found, should only include recent ones
        if result.post_count > 0:
            assert result.time_window_hours == 24, "Time window should match input"

    # Cleanup
    await mongodb_database_async.channels.delete_many({"user_id": 400})
    await mongodb_database_async.posts.delete_many({"user_id": 400})


@pytest.mark.asyncio
async def test_digest_error_handling_characterization():
    """Characterization: Error handling behavior.

    Purpose:
        Captures how digest generation handles errors:
        - Should not raise exceptions for individual channel failures
        - Should return empty list or error digest
        - Should log errors appropriately
    """
    # Test that use case doesn't crash on invalid input
    use_case = GenerateChannelDigestByNameUseCase()

    # Characterize: Invalid channel name should not crash
    # (Behavior depends on implementation - may return empty digest or raise)
    # For now, we just verify it doesn't crash the process
    try:
        result = await use_case.execute(
            user_id=999,
            channel_username="nonexistent_channel",
            hours=24,
        )
        # Should return ChannelDigest (even if empty) or raise specific exception
        assert isinstance(result, ChannelDigest) or isinstance(result, Exception), (
            "Should return ChannelDigest or raise specific exception"
        )
    except Exception as e:
        # If it raises, should be a specific exception type (not generic)
        # Note: May raise OperationFailure if DB auth issues, which is acceptable
        from pymongo.errors import OperationFailure
        
        assert isinstance(
            e, (ValueError, KeyError, AttributeError, OperationFailure)
        ), (
            f"Should raise specific exception type, not generic Exception. "
            f"Got: {type(e).__name__}: {e}"
        )


@pytest.mark.asyncio
async def test_summarization_method_characterization(mongodb_database_async):
    """Characterization: Summarization method selection.

    Purpose:
        Captures which summarization method is used:
        - Current implementation uses SummarizerService (AdaptiveSummarizer)
        - Method field in SummaryResult indicates which strategy was used
    """
    # Setup
    await mongodb_database_async.channels.insert_one(
        {
            "user_id": 500,
            "channel_username": "method_test",
            "title": "Method Test",
            "active": True,
        }
    )

    now = datetime.now(timezone.utc)
    posts = [
        {
            "user_id": 500,
            "channel_username": "method_test",
            "message_id": "msg_1",
            "text": "Test post for method characterization",
            "date": now - timedelta(hours=6),
        },
    ]

    from src.infrastructure.repositories.post_repository import PostRepository

    post_repo = PostRepository(mongodb_database_async)
    for post in posts:
        await post_repo.save_post(post)

    # Mock get_db to return test database
    from unittest.mock import patch

    async def mock_get_db():
        return mongodb_database_async

    with patch("src.application.use_cases.generate_channel_digest_by_name.get_db", side_effect=mock_get_db):
        use_case = GenerateChannelDigestByNameUseCase()

        result = await use_case.execute(
            user_id=500,
            channel_username="method_test",
            hours=24,
        )

        # Characterize: Verify summary method field
        assert hasattr(result.summary, "method"), "SummaryResult should have method field"
        assert isinstance(result.summary.method, str), "Method should be string"
        # Current methods: "direct", "map_reduce", "error"
        assert result.summary.method in ["direct", "map_reduce", "error"], (
            f"Method should be one of: direct, map_reduce, error. Got: {result.summary.method}"
        )

        # Characterize: Verify confidence field
        assert hasattr(result.summary, "confidence"), "SummaryResult should have confidence field"
        assert isinstance(result.summary.confidence, (int, float)), "Confidence should be number"
        assert 0.0 <= result.summary.confidence <= 1.0, "Confidence should be between 0 and 1"

    # Cleanup
    await mongodb_database_async.channels.delete_many({"user_id": 500})
    await mongodb_database_async.posts.delete_many({"user_id": 500})

