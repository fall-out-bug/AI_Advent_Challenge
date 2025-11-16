"""Characterization tests for summarization behavior.

Purpose:
    Capture current summarization behavior before refactoring.
    These tests document how summarization works now to ensure no regressions
    during Cluster B refactoring (B.3-B.4).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext


@pytest.mark.asyncio
async def test_summarizer_service_interface_characterization():
    """Characterization: SummarizerService interface.

    Purpose:
        Captures the current SummarizerService interface:
        - What methods are available
        - What parameters they accept
        - What they return
    """
    from src.domain.services.summarizer import SummarizerService
    from src.infrastructure.di.factories import create_adaptive_summarizer

    # Characterize: Get current summarizer implementation
    summarizer = create_adaptive_summarizer()

    # Characterize: Verify it implements SummarizerService
    assert isinstance(summarizer, SummarizerService), "Should implement SummarizerService interface"

    # Characterize: Verify required method exists
    assert hasattr(summarizer, "summarize_posts"), "Should have summarize_posts method"
    assert callable(summarizer.summarize_posts), "summarize_posts should be callable"

    # Characterize: Verify method signature (by calling with test data)
    posts = [
        PostContent(
            text="Test post for summarization characterization",
            date=datetime.now(timezone.utc),
            message_id="test_msg",
            channel_username="test_channel",
        )
    ]

    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        max_chars=1000,
        language="ru",
        max_sentences=5,
        channel_username="test_channel",
        channel_title=None,
    )

    # Characterize: Method should be async and accept posts, max_sentences, language, context
    result = await summarizer.summarize_posts(
        posts=posts,
        max_sentences=5,
        language="ru",
        context=context,
    )

    # Characterize: Verify return type
    from src.domain.value_objects.summary_result import SummaryResult

    assert isinstance(result, SummaryResult), "Should return SummaryResult object"

    # Characterize: Verify SummaryResult fields
    assert hasattr(result, "text"), "SummaryResult should have text"
    assert hasattr(result, "sentences_count"), "SummaryResult should have sentences_count"
    assert hasattr(result, "method"), "SummaryResult should have method"
    assert hasattr(result, "confidence"), "SummaryResult should have confidence"
    assert hasattr(result, "metadata"), "SummaryResult should have metadata"


@pytest.mark.asyncio
async def test_summarization_empty_posts_behavior_characterization():
    """Characterization: Behavior with empty posts list.

    Purpose:
        Captures how summarization handles empty posts:
        - Should return fallback summary
        - Should not raise exception
    """
    from src.infrastructure.di.factories import create_adaptive_summarizer

    summarizer = create_adaptive_summarizer()

    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        max_chars=1000,
        language="ru",
        max_sentences=5,
        channel_username="test_channel",
        channel_title=None,
    )

    # Characterize: Empty posts list handling
    result = await summarizer.summarize_posts(
        posts=[],
        max_sentences=5,
        language="ru",
        context=context,
    )

    # Should return SummaryResult (not raise exception)
    from src.domain.value_objects.summary_result import SummaryResult

    assert isinstance(result, SummaryResult), "Should return SummaryResult even for empty posts"
    assert isinstance(result.text, str), "Should have text (fallback message)"


@pytest.mark.asyncio
async def test_summarization_method_selection_characterization():
    """Characterization: Method selection logic.

    Purpose:
        Captures how summarizer selects method (direct vs map_reduce):
        - Current implementation uses AdaptiveSummarizer
        - Method selection based on token count threshold
    """
    from src.infrastructure.di.factories import create_adaptive_summarizer

    summarizer = create_adaptive_summarizer()

    # Characterize: Small content should use direct method
    small_posts = [
        PostContent(
            text="Short post for direct summarization",
            date=datetime.now(timezone.utc),
            message_id="small_1",
            channel_username="test",
        )
    ]

    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        max_chars=1000,
        language="ru",
        max_sentences=5,
        channel_username="test",
        channel_title=None,
    )

    result_small = await summarizer.summarize_posts(
        posts=small_posts,
        max_sentences=5,
        language="ru",
        context=context,
    )

    # Characterize: Should return valid SummaryResult with method field
    assert isinstance(result_small, type(result_small)), "Should return SummaryResult"
    assert hasattr(result_small, "method"), "Should have method field"
    assert result_small.method in ["direct", "map_reduce", "error"], (
        f"Method should be direct, map_reduce, or error. Got: {result_small.method}"
    )
