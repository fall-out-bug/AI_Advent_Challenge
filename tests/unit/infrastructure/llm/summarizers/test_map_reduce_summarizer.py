"""Unit tests for MapReduceSummarizer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.services.summary_quality_checker import (
    QualityScore,
    SummaryQualityChecker,
)
from src.domain.services.text_cleaner import TextCleanerService
from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker, TextChunk
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.llm.summarizers.map_reduce_summarizer import MapReduceSummarizer
from src.infrastructure.llm.token_counter import TokenCounter


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock(
        side_effect=[
            "Chunk 1 summary.",
            "Chunk 2 summary.",
            "Combined final summary.",
        ]
    )
    return client


@pytest.fixture
def mock_chunker():
    """Mock chunker."""
    chunker = MagicMock(spec=SemanticChunker)
    chunker.chunk_text = MagicMock(
        return_value=[
            TextChunk(text="Chunk 1", token_count=2000, chunk_id=0),
            TextChunk(text="Chunk 2", token_count=2000, chunk_id=1),
        ]
    )
    return chunker


@pytest.fixture
def mock_token_counter():
    """Mock token counter."""
    counter = MagicMock(spec=TokenCounter)
    counter.count_tokens = MagicMock(return_value=100)
    return counter


@pytest.fixture
def text_cleaner():
    """Text cleaner."""
    return TextCleanerService()


@pytest.fixture
def quality_checker():
    """Quality checker."""
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
def summarizer(
    mock_llm_client, mock_chunker, mock_token_counter, text_cleaner, quality_checker
):
    """MapReduceSummarizer instance."""
    return MapReduceSummarizer(
        llm_client=mock_llm_client,
        chunker=mock_chunker,
        token_counter=mock_token_counter,
        text_cleaner=text_cleaner,
        quality_checker=quality_checker,
        temperature=0.2,
        map_max_tokens=600,
        reduce_max_tokens=2000,
    )


@pytest.mark.asyncio
async def test_map_reduce_flow(summarizer, mock_chunker, mock_llm_client):
    """Test complete map-reduce flow."""
    long_text = "Long text " * 1000

    result = await summarizer.summarize_text(
        text=long_text,
        max_sentences=5,
        language="ru",
    )

    assert result is not None
    assert result.method == "map_reduce"
    assert len(result.text) > 0

    # Verify chunking was called
    mock_chunker.chunk_text.assert_called_once()

    # Verify LLM was called for map phase (2 chunks) and reduce phase (1 call)
    assert mock_llm_client.generate.call_count >= 3


@pytest.mark.asyncio
async def test_summarize_posts(summarizer, mock_chunker, mock_llm_client):
    """Test summarizing posts."""
    from src.domain.value_objects.post_content import PostContent

    posts = [
        PostContent(text="Long post " * 100, channel_username="test"),
        PostContent(text="Another long post " * 100, channel_username="test"),
    ]

    result = await summarizer.summarize_posts(
        posts=posts,
        max_sentences=5,
        language="ru",
    )

    assert result is not None
    assert result.method == "map_reduce"


@pytest.mark.asyncio
async def test_parallel_map_phase(summarizer, mock_chunker, mock_llm_client):
    """Test map phase processes chunks in parallel."""
    mock_chunker.chunk_text.return_value = [
        TextChunk(text=f"Chunk {i}", token_count=2000, chunk_id=i) for i in range(5)
    ]

    mock_llm_client.generate.side_effect = [
        f"Summary {i}" for i in range(6)  # 5 map + 1 reduce
    ]

    result = await summarizer.summarize_text(
        text="Long text",
        max_sentences=5,
        language="ru",
    )

    assert result is not None
    # Should have called generate for each chunk + reduce
    assert mock_llm_client.generate.call_count == 6


@pytest.mark.asyncio
async def test_reduce_phase_combines_summaries(
    summarizer, mock_chunker, mock_llm_client
):
    """Test reduce phase properly combines chunk summaries."""
    mock_chunker.chunk_text.return_value = [
        TextChunk(text="Chunk 1", token_count=2000, chunk_id=0),
        TextChunk(text="Chunk 2", token_count=2000, chunk_id=1),
    ]

    map_summaries = ["First chunk summary.", "Second chunk summary."]
    final_summary = "Combined summary."

    mock_llm_client.generate.side_effect = map_summaries + [final_summary]

    result = await summarizer.summarize_text(
        text="Long text",
        max_sentences=3,
        language="ru",
    )

    assert result is not None
    assert result.text == final_summary or final_summary in result.text
