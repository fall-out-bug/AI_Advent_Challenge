"""Unit tests for SummarizerService abstraction.

Purpose:
    Verify that SummarizerService abstraction works correctly
    and that implementations conform to the protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.services.summarizer import SummarizerService
from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.di.factories import create_adaptive_summarizer
from src.infrastructure.llm.summarizers.adaptive_summarizer import AdaptiveSummarizer


@pytest.mark.asyncio
async def test_summarizer_service_protocol_implementation():
    """Test that AdaptiveSummarizer implements SummarizerService protocol.

    Purpose:
        Verify that the default implementation conforms to the protocol.
    """
    summarizer = create_adaptive_summarizer()

    # Verify it's an instance of AdaptiveSummarizer
    assert isinstance(summarizer, AdaptiveSummarizer), (
        "Factory should return AdaptiveSummarizer instance"
    )

    # Verify it implements SummarizerService protocol
    # (Protocol checking is structural - if methods exist, it conforms)
    assert hasattr(summarizer, "summarize_text"), "Should have summarize_text method"
    assert hasattr(summarizer, "summarize_posts"), "Should have summarize_posts method"
    assert callable(summarizer.summarize_text), "summarize_text should be callable"
    assert callable(summarizer.summarize_posts), "summarize_posts should be callable"


@pytest.mark.asyncio
async def test_summarizer_service_summarize_text_signature():
    """Test that summarize_text has correct signature.

    Purpose:
        Verify the method signature matches SummarizerService protocol.
    """
    summarizer = create_adaptive_summarizer()

    # Verify method signature by calling with test data
    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        max_chars=1000,
        language="ru",
        max_sentences=5,
        channel_username="test",
        channel_title=None,
    )

    # Should accept: text, max_sentences, language, context
    result = await summarizer.summarize_text(
        text="Test text for summarization",
        max_sentences=5,
        language="ru",
        context=context,
    )

    # Should return SummaryResult
    assert isinstance(result, SummaryResult), "Should return SummaryResult"


@pytest.mark.asyncio
async def test_summarizer_service_summarize_posts_signature():
    """Test that summarize_posts has correct signature.

    Purpose:
        Verify the method signature matches SummarizerService protocol.
    """
    summarizer = create_adaptive_summarizer()

    posts = [
        PostContent(
            text="Test post for summarization",
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

    # Should accept: posts, max_sentences, language, context
    result = await summarizer.summarize_posts(
        posts=posts,
        max_sentences=5,
        language="ru",
        context=context,
    )

    # Should return SummaryResult
    assert isinstance(result, SummaryResult), "Should return SummaryResult"


@pytest.mark.asyncio
async def test_summarizer_service_can_be_mocked():
    """Test that SummarizerService can be mocked for testing.

    Purpose:
        Verify that use cases can inject mock SummarizerService
        for isolated testing (important for B.4).
    """
    # Create mock SummarizerService
    mock_summarizer = AsyncMock(spec=SummarizerService)

    # Configure mock to return SummaryResult
    mock_summary = SummaryResult(
        text="Mock summary text",
        sentences_count=3,
        method="direct",
        confidence=0.8,
    )
    mock_summarizer.summarize_posts.return_value = mock_summary

    # Verify mock can be used as SummarizerService
    posts = [
        PostContent(
            text="Test post",
            date=datetime.now(timezone.utc),
            message_id="msg_1",
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

    result = await mock_summarizer.summarize_posts(
        posts=posts,
        max_sentences=5,
        language="ru",
        context=context,
    )

    assert result == mock_summary, "Mock should return configured result"
    mock_summarizer.summarize_posts.assert_called_once()


@pytest.mark.asyncio
async def test_summarizer_service_factory_returns_protocol_type():
    """Test that factory returns SummarizerService type.

    Purpose:
        Verify that factories return protocol type, not concrete implementation.
        This allows dependency injection and testing flexibility.
    """
    summarizer = create_adaptive_summarizer()

    # Type check: should be compatible with SummarizerService protocol
    # (Structural typing - if methods exist, it's compatible)
    assert hasattr(summarizer, "summarize_text"), "Should implement summarize_text"
    assert hasattr(summarizer, "summarize_posts"), "Should implement summarize_posts"

    # Verify it can be used where SummarizerService is expected
    # (This is a runtime check - type checkers will verify at compile time)
    async def use_summarizer(service: SummarizerService) -> SummaryResult:
        """Function that accepts SummarizerService protocol."""
        return await service.summarize_text(
            text="test",
            max_sentences=1,
            language="ru",
        )

    result = await use_summarizer(summarizer)
    assert isinstance(result, SummaryResult), "Should work with protocol type"


@pytest.mark.asyncio
async def test_summarizer_service_empty_input_handling():
    """Test that SummarizerService handles empty input gracefully.

    Purpose:
        Verify error handling and edge cases.
    """
    summarizer = create_adaptive_summarizer()

    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
        max_chars=1000,
        language="ru",
        max_sentences=5,
        channel_username="test",
        channel_title=None,
    )

    # Empty text should return fallback summary
    result = await summarizer.summarize_text(
        text="",
        max_sentences=5,
        language="ru",
        context=context,
    )

    assert isinstance(result, SummaryResult), "Should return SummaryResult even for empty text"
    assert isinstance(result.text, str), "Should have text (fallback message)"

    # Empty posts list should return fallback summary
    result_posts = await summarizer.summarize_posts(
        posts=[],
        max_sentences=5,
        language="ru",
        context=context,
    )

    assert isinstance(result_posts, SummaryResult), "Should return SummaryResult even for empty posts"
    assert isinstance(result_posts.text, str), "Should have text (fallback message)"
