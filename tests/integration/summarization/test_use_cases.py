"""Integration tests for summarization use cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.dtos.digest_dtos import ChannelDigest
from src.application.use_cases.generate_channel_digest import (
    GenerateChannelDigestUseCase,
)
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.application.use_cases.generate_task_summary import GenerateTaskSummaryUseCase
from src.domain.services.summarizer import SummarizerService
from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.repositories.task_repository import TaskRepository


@pytest.fixture
def mock_post_repository():
    """Mock post repository."""
    repo = MagicMock(spec=PostRepository)
    repo.get_posts_by_channel = AsyncMock(return_value=[])
    repo.get_posts_by_user_subscriptions = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_task_repository():
    """Mock task repository."""
    repo = MagicMock(spec=TaskRepository)
    repo.find_tasks = AsyncMock(return_value=[])
    # Add _collection mock for internal use
    repo._collection = MagicMock()
    repo._collection.find = MagicMock()
    repo._collection.find.return_value.sort = MagicMock(
        return_value=AsyncMock(to_list=AsyncMock(return_value=[]))
    )
    return repo


@pytest.fixture
def mock_summarizer():
    """Mock summarizer service."""
    summarizer = MagicMock(spec=SummarizerService)
    summarizer.summarize_posts = AsyncMock(
        return_value=SummaryResult(
            text="Test summary.",
            sentences_count=3,
            method="direct",
            confidence=0.9,
        )
    )
    return summarizer


@pytest.fixture
def mock_settings():
    """Mock settings."""
    settings = MagicMock()
    settings.digest_summary_sentences = 8
    settings.summarizer_language = "ru"
    settings.digest_max_channels = 10
    return settings


@pytest.mark.asyncio
async def test_generate_channel_digest_by_name_success(
    mock_post_repository, mock_summarizer, mock_settings
):
    """Test successful channel digest generation by name."""
    # Setup: mock posts
    mock_post_repository.get_posts_by_channel = AsyncMock(
        return_value=[
            {
                "text": "Post 1 text.",
                "date": datetime.now(timezone.utc),
                "message_id": "1",
            },
            {
                "text": "Post 2 text.",
                "date": datetime.now(timezone.utc) - timedelta(hours=1),
                "message_id": "2",
            },
        ]
    )

    # Mock database
    mock_db = MagicMock()
    mock_db.channels.find_one = AsyncMock(return_value={"title": "Test Channel"})

    use_case = GenerateChannelDigestByNameUseCase(
        post_repository=mock_post_repository,
        summarizer=mock_summarizer,
        settings=mock_settings,
    )

    with patch(
        "src.application.use_cases.generate_channel_digest_by_name.get_db",
        return_value=mock_db,
    ):
        result = await use_case.execute(
            user_id=123,
            channel_username="test_channel",
            hours=24,
        )

    assert isinstance(result, ChannelDigest)
    assert result.channel_username == "test_channel"
    assert result.post_count == 2
    assert result.summary is not None
    mock_summarizer.summarize_posts.assert_called_once()


@pytest.mark.asyncio
async def test_generate_channel_digest_by_name_no_posts(
    mock_post_repository, mock_summarizer, mock_settings
):
    """Test channel digest with no posts."""
    mock_post_repository.get_posts_by_channel = AsyncMock(return_value=[])

    # Mock database
    mock_db = MagicMock()
    mock_db.channels.find_one = AsyncMock(return_value=None)

    use_case = GenerateChannelDigestByNameUseCase(
        post_repository=mock_post_repository,
        summarizer=mock_summarizer,
        settings=mock_settings,
    )

    with patch(
        "src.application.use_cases.generate_channel_digest_by_name.get_db",
        return_value=mock_db,
    ):
        result = await use_case.execute(
            user_id=123,
            channel_username="empty_channel",
            hours=24,
        )

    assert isinstance(result, ChannelDigest)
    assert result.post_count == 0
    assert "Нет постов" in result.summary.text or "No posts" in result.summary.text
    # Should not call summarizer for empty posts
    mock_summarizer.summarize_posts.assert_not_called()


@pytest.mark.asyncio
async def test_generate_channel_digest_multiple_channels(
    mock_post_repository, mock_summarizer, mock_settings
):
    """Test generating digests for multiple channels."""
    # Mock database channels
    mock_channels = [
        {"channel_username": "channel1", "active": True},
        {"channel_username": "channel2", "active": True},
    ]

    # Mock posts for each channel - need to return posts so digests are created
    call_count = [0]

    async def get_posts_side_effect(channel_username, since, user_id=None):
        """Side effect for get_posts_by_channel mock.

        Purpose:
            Returns different posts based on call count to simulate
            different channels being processed.

        Args:
            channel_username: Channel username (unused but required by signature).
            since: Since datetime (unused but required by signature).
            user_id: Optional user ID (unused but required by signature).

        Returns:
            List of post dictionaries.
        """
        call_count[0] += 1
        if call_count[0] == 1:
            return [
                {
                    "text": "Post from channel1",
                    "date": datetime.now(timezone.utc),
                    "message_id": "1",
                }
            ]
        else:
            return [
                {
                    "text": "Post from channel2",
                    "date": datetime.now(timezone.utc),
                    "message_id": "2",
                }
            ]

    mock_post_repository.get_posts_by_channel = AsyncMock(
        side_effect=get_posts_side_effect
    )

    use_case = GenerateChannelDigestUseCase(
        post_repository=mock_post_repository,
        summarizer=mock_summarizer,
        settings=mock_settings,
    )

    with patch(
        "src.application.use_cases.generate_channel_digest.get_db"
    ) as mock_get_db:
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_channels)
        mock_db.channels.find = MagicMock(return_value=mock_cursor)
        mock_db.channels.find_one = AsyncMock(return_value={"title": "Test Channel"})
        mock_get_db.return_value = mock_db

        # Also patch get_db in generate_channel_digest_by_name
        with patch(
            "src.application.use_cases.generate_channel_digest_by_name.get_db",
            return_value=mock_db,
        ):
            result = await use_case.execute(user_id=123, hours=24)

        assert isinstance(result, list)
        # Should have 2 digests (one per channel with posts)
        assert len(result) == 2
        assert all(isinstance(d, ChannelDigest) for d in result)


@pytest.mark.asyncio
async def test_task_summary_use_case(mock_task_repository):
    """Test task summary generation."""
    # Mock tasks
    mock_task_repository.find_tasks = AsyncMock(
        return_value=[
            {
                "_id": "1",
                "title": "Task 1",
                "completed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "_id": "2",
                "title": "Task 2",
                "completed": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
    )

    use_case = GenerateTaskSummaryUseCase(task_repository=mock_task_repository)

    result = await use_case.execute(user_id=123, timeframe="today")

    assert result is not None
    assert len(result.tasks) >= 0
    assert result.stats is not None
    assert "total" in result.stats


@pytest.mark.asyncio
async def test_digest_generation_with_error_handling(
    mock_post_repository, mock_summarizer, mock_settings
):
    """Test error handling in digest generation."""
    # Setup: posts exist but summarizer fails
    mock_post_repository.get_posts_by_channel = AsyncMock(
        return_value=[
            {"text": "Post", "date": datetime.now(timezone.utc), "message_id": "1"}
        ]
    )
    mock_summarizer.summarize_posts = AsyncMock(side_effect=Exception("LLM error"))

    # Mock database
    mock_db = MagicMock()
    mock_db.channels.find_one = AsyncMock(return_value={"title": "Test Channel"})

    use_case = GenerateChannelDigestByNameUseCase(
        post_repository=mock_post_repository,
        summarizer=mock_summarizer,
        settings=mock_settings,
    )

    with patch(
        "src.application.use_cases.generate_channel_digest_by_name.get_db",
        return_value=mock_db,
    ):
        result = await use_case.execute(
            user_id=123,
            channel_username="test",
            hours=24,
        )

    # Should still return digest with error fallback
    assert isinstance(result, ChannelDigest)
    assert result.post_count == 1
    assert "Ошибка" in result.summary.text or "Error" in result.summary.text
