"""Unit tests for LLMSummarizer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.services.summary_quality_checker import (
    QualityScore,
    SummaryQualityChecker,
)
from src.domain.services.text_cleaner import TextCleanerService
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
from src.infrastructure.llm.token_counter import TokenCounter


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock(return_value="First sentence. Second sentence.")
    return client


@pytest.fixture
def mock_token_counter():
    """Mock token counter."""
    counter = MagicMock(spec=TokenCounter)
    counter.count_tokens = MagicMock(return_value=100)
    return counter


@pytest.fixture
def text_cleaner():
    """Text cleaner service."""
    return TextCleanerService()


@pytest.fixture
def quality_checker():
    """Quality checker with good scores."""
    checker = MagicMock(spec=SummaryQualityChecker)
    checker.check_quality = MagicMock(
        return_value=QualityScore(
            score=0.9,
            length_score=1.0,
            sentence_count_score=1.0,
            uniqueness_score=1.0,
            coherence_score=0.9,
            issues=[],
        )
    )
    return checker


@pytest.fixture
def summarizer(mock_llm_client, mock_token_counter, text_cleaner, quality_checker):
    """LLMSummarizer instance."""
    return LLMSummarizer(
        llm_client=mock_llm_client,
        token_counter=mock_token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=0.5,
        max_tokens=2000,
        max_retries=2,
    )


@pytest.mark.asyncio
async def test_summarize_text_success(summarizer, mock_llm_client):
    """Test successful text summarization."""
    text = "This is a test post. It contains multiple sentences. Each sentence has meaning."
    
    result = await summarizer.summarize_text(
        text=text,
        max_sentences=2,
        language="ru",
    )
    
    assert isinstance(result, SummaryResult)
    assert result.method == "direct"
    assert len(result.text) > 0
    assert result.sentences_count >= 0
    # May be called multiple times due to retry logic, so check at least once
    assert mock_llm_client.generate.call_count >= 1


@pytest.mark.asyncio
async def test_summarize_posts(summarizer, mock_llm_client):
    """Test summarizing multiple posts."""
    from src.domain.value_objects.post_content import PostContent
    
    posts = [
        PostContent(text="Post 1 text. " * 5, channel_username="test"),  # Longer posts
        PostContent(text="Post 2 text. " * 5, channel_username="test"),
    ]
    
    result = await summarizer.summarize_posts(
        posts=posts,
        max_sentences=3,
        language="ru",
    )
    
    assert isinstance(result, SummaryResult)
    assert result.method == "direct"
    # May be called multiple times due to retry logic, so check at least once
    assert mock_llm_client.generate.call_count >= 1


@pytest.mark.asyncio
async def test_summarize_with_context(summarizer, mock_llm_client):
    """Test summarization with context."""
    text = "Test text"
    context = SummarizationContext(
        time_period_hours=24,
        source_type="telegram_posts",
    )
    
    result = await summarizer.summarize_text(
        text=text,
        max_sentences=5,
        language="ru",
        context=context,
    )
    
    assert result is not None
    assert result.method == "direct"


@pytest.mark.asyncio
async def test_quality_check_retry(summarizer, mock_llm_client, quality_checker):
    """Test quality check triggers retry on low quality."""
    # First call: low quality
    quality_checker.check_quality.side_effect = [
        QualityScore(
            score=0.3,
            length_score=0.3,
            sentence_count_score=0.3,
            uniqueness_score=0.5,
            coherence_score=0.2,
            issues=["Too short"],
        ),
        QualityScore(
            score=0.9,
            length_score=1.0,
            sentence_count_score=1.0,
            uniqueness_score=1.0,
            coherence_score=0.9,
            issues=[],
        ),
    ]
    quality_checker.should_retry = MagicMock(side_effect=[True, False])
    
    mock_llm_client.generate.side_effect = [
        "Short",
        "First sentence. Second sentence. Third sentence.",
    ]
    
    result = await summarizer.summarize_text(
        text="Test text",
        max_sentences=3,
        language="ru",
    )
    
    assert result is not None
    # Should have retried
    assert mock_llm_client.generate.call_count >= 2


@pytest.mark.asyncio
async def test_fallback_on_llm_error(summarizer, mock_llm_client):
    """Test fallback summary on LLM error."""
    mock_llm_client.generate.side_effect = Exception("LLM error")
    
    result = await summarizer.summarize_text(
        text="Test text",
        max_sentences=3,
        language="ru",
    )
    
    assert result is not None
    assert len(result.text) > 0
    assert result.method == "direct"


@pytest.mark.asyncio
async def test_finalize_summary_sentence_count(summarizer):
    """Test finalize summary respects max_sentences."""
    summary = "First. Second. Third. Fourth. Fifth. Sixth."
    
    finalized = summarizer._finalize_summary(summary, max_sentences=3, language="ru")
    
    sentences = finalized.split(".")
    # Should have max 3 sentences (plus empty after last period)
    assert len([s for s in sentences if s.strip()]) <= 3
