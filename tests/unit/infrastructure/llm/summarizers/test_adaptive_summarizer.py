"""Unit tests for AdaptiveSummarizer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.llm.summarizers.adaptive_summarizer import AdaptiveSummarizer
from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
from src.infrastructure.llm.summarizers.map_reduce_summarizer import MapReduceSummarizer
from src.infrastructure.llm.token_counter import TokenCounter


@pytest.fixture
def mock_direct_summarizer():
    """Mock direct summarizer."""
    summarizer = MagicMock(spec=LLMSummarizer)
    summarizer.summarize_text = AsyncMock(
        return_value=SummaryResult(
            text="Direct summary.",
            sentences_count=2,
            method="direct",
        )
    )
    summarizer.summarize_posts = AsyncMock(
        return_value=SummaryResult(
            text="Direct summary.",
            sentences_count=2,
            method="direct",
        )
    )
    return summarizer


@pytest.fixture
def mock_map_reduce_summarizer():
    """Mock map-reduce summarizer."""
    summarizer = MagicMock(spec=MapReduceSummarizer)
    summarizer.summarize_text = AsyncMock(
        return_value=SummaryResult(
            text="Map-reduce summary.",
            sentences_count=5,
            method="map_reduce",
        )
    )
    summarizer.summarize_posts = AsyncMock(
        return_value=SummaryResult(
            text="Map-reduce summary.",
            sentences_count=5,
            method="map_reduce",
        )
    )
    return summarizer


@pytest.fixture
def mock_token_counter():
    """Mock token counter."""
    counter = MagicMock(spec=TokenCounter)
    return counter


@pytest.fixture
def adaptive_summarizer(
    mock_direct_summarizer, mock_map_reduce_summarizer, mock_token_counter
):
    """AdaptiveSummarizer instance."""
    return AdaptiveSummarizer(
        direct_summarizer=mock_direct_summarizer,
        map_reduce_summarizer=mock_map_reduce_summarizer,
        token_counter=mock_token_counter,
        threshold_tokens=3000,
    )


@pytest.mark.asyncio
async def test_uses_direct_for_short_text(
    adaptive_summarizer, mock_token_counter, mock_direct_summarizer
):
    """Test uses direct summarizer for short text."""
    mock_token_counter.count_tokens = MagicMock(return_value=1000)  # Below threshold

    result = await adaptive_summarizer.summarize_text(
        text="Short text",
        max_sentences=3,
        language="ru",
    )

    assert result.method == "direct"
    mock_direct_summarizer.summarize_text.assert_called_once()
    mock_token_counter.count_tokens.assert_called_once()


@pytest.mark.asyncio
async def test_uses_map_reduce_for_long_text(
    adaptive_summarizer, mock_token_counter, mock_map_reduce_summarizer
):
    """Test uses map-reduce for long text."""
    mock_token_counter.count_tokens = MagicMock(return_value=5000)  # Above threshold

    result = await adaptive_summarizer.summarize_text(
        text="Long text " * 1000,
        max_sentences=5,
        language="ru",
    )

    assert result.method == "map_reduce"
    mock_map_reduce_summarizer.summarize_text.assert_called_once()


@pytest.mark.asyncio
async def test_uses_direct_at_threshold(
    adaptive_summarizer, mock_token_counter, mock_direct_summarizer
):
    """Test uses direct at threshold."""
    mock_token_counter.count_tokens = MagicMock(return_value=3000)  # Exactly threshold

    result = await adaptive_summarizer.summarize_text(
        text="Text at threshold",
        max_sentences=3,
        language="ru",
    )

    assert result.method == "direct"
    mock_direct_summarizer.summarize_text.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_posts_delegates(
    adaptive_summarizer, mock_token_counter, mock_direct_summarizer
):
    """Test summarize_posts delegates correctly."""
    from src.domain.value_objects.post_content import PostContent

    posts = [
        PostContent(text="Short post " * 10, channel_username="test")
    ]  # Longer post
    mock_token_counter.count_tokens = MagicMock(return_value=500)  # Short

    result = await adaptive_summarizer.summarize_posts(
        posts=posts,
        max_sentences=3,
        language="ru",
    )

    assert result.method == "direct"
    # AdaptiveSummarizer converts posts to text and calls summarize_text
    # So we check that summarize_text was called
    mock_direct_summarizer.summarize_text.assert_called_once()
