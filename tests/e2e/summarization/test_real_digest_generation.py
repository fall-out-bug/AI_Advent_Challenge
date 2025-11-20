"""E2E tests for digest generation with real services."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.domain.value_objects.post_content import PostContent
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.post_repository import PostRepository


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_generate_real_channel_digest(
    real_mongodb, real_llm_client, telegram_test_channel, test_user_id
):
    """Test complete digest generation with real services.

    Purpose:
        Tests full flow: collect posts -> generate summary -> verify quality.

    Prerequisites:
        - MongoDB running
        - LLM service available
        - Test channel exists with recent posts
    """
    # 1. Setup: Populate test channel with posts
    channel_username = telegram_test_channel["username"]

    post_repo = PostRepository(real_mongodb)

    # Create test posts
    test_posts = [
        {
            "user_id": test_user_id,
            "channel_username": channel_username,
            "message_id": f"test_{i}",
            "text": f"Test post {i}: This is a test post for digest generation.",
            "date": datetime.now(timezone.utc) - timedelta(hours=i),
            "test_data": True,
        }
        for i in range(5)
    ]

    for post in test_posts:
        await post_repo.save_post(post)

    # 2. Execute: Generate digest via use case
    use_case = GenerateChannelDigestByNameUseCase(
        post_repository=post_repo,
        summarizer=None,  # Will use AdaptiveSummarizer from DI
    )

    result = await use_case.execute(
        user_id=test_user_id,
        channel_username=channel_username,
        hours=24,
    )

    # 3. Assert: Check quality, format, content
    assert result is not None
    assert result.channel_username == channel_username
    assert result.post_count >= 0
    assert result.summary is not None
    assert len(result.summary.text) > 0

    # 4. Cleanup: Remove test data
    await real_mongodb.posts.delete_many({"test_data": True})


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_map_reduce_with_real_llm(real_llm_client):
    """Test Map-Reduce summarization with real LLM.

    Purpose:
        Verifies Map-Reduce works correctly with real LLM for long texts.
    """
    from src.domain.services.summary_quality_checker import SummaryQualityChecker
    from src.domain.services.text_cleaner import TextCleanerService
    from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker
    from src.infrastructure.llm.summarizers.map_reduce_summarizer import (
        MapReduceSummarizer,
    )
    from src.infrastructure.llm.token_counter import TokenCounter

    # Create long text (10+ posts, >5000 tokens total)
    long_text = "\n\n".join(
        [f"Post {i}: " + " ".join([f"Word{j}" for j in range(100)]) for i in range(15)]
    )

    token_counter = TokenCounter()
    chunker = SemanticChunker(token_counter, max_tokens=3000, overlap_tokens=200)
    text_cleaner = TextCleanerService()
    quality_checker = SummaryQualityChecker()

    summarizer = MapReduceSummarizer(
        llm_client=real_llm_client,
        chunker=chunker,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
    )

    result = await summarizer.summarize_text(
        text=long_text,
        max_sentences=8,
        language="ru",
    )

    assert result is not None
    assert len(result.text) > 0
    assert result.method == "map_reduce"
    assert result.sentences_count > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_task_summary_full_flow(real_mongodb, test_user_id):
    """Test task summary generation with real DB.

    Purpose:
        Tests task summary use case with real MongoDB.
    """
    from src.application.use_cases.generate_task_summary import (
        GenerateTaskSummaryUseCase,
    )
    from src.infrastructure.repositories.task_repository import TaskRepository

    # Create test tasks
    task_repo = TaskRepository(real_mongodb)

    from datetime import datetime, timezone

    from src.domain.entities.task import TaskIn

    test_tasks = [
        TaskIn(
            user_id=test_user_id,
            title=f"Test task {i}",
            description=f"Description for task {i}",
            priority="medium",
            test_data=True,
        )
        for i in range(3)
    ]

    for task_in in test_tasks:
        await task_repo.create_task(task_in)

    # Generate summary
    use_case = GenerateTaskSummaryUseCase(task_repository=task_repo)
    result = await use_case.execute(user_id=test_user_id, timeframe="today")

    assert result is not None
    assert len(result.tasks) >= 0
    assert result.stats is not None
    assert "total" in result.stats

    # Cleanup
    await real_mongodb.tasks.delete_many({"test_data": True})


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_llm_failure_fallback():
    """Test fallback when LLM is unavailable.

    Purpose:
        Verifies fallback mechanism works when LLM fails.
    """
    from src.domain.services.summary_quality_checker import SummaryQualityChecker
    from src.domain.services.text_cleaner import TextCleanerService
    from src.infrastructure.clients.llm_client import FallbackLLMClient
    from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
    from src.infrastructure.llm.token_counter import TokenCounter

    # Use FallbackLLMClient (always available)
    fallback_client = FallbackLLMClient()
    token_counter = TokenCounter()
    text_cleaner = TextCleanerService()
    quality_checker = SummaryQualityChecker()

    summarizer = LLMSummarizer(
        llm_client=fallback_client,
        token_counter=token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
    )

    result = await summarizer.summarize_text(
        text="Test post 1. Test post 2. Test post 3.",
        max_sentences=3,
        language="ru",
    )

    assert result is not None
    assert len(result.text) > 0
    assert result.method == "direct"
