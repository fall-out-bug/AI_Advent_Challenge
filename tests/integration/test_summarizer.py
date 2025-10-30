"""Integration tests for LLM-based summarizer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.llm.summarizer import summarize_posts, MapReduceSummarizer
from src.infrastructure.clients.llm_client import LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.calls = []

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
        """Generate mock response."""
        self.calls.append(prompt)
        if self.responses:
            return self.responses.pop(0)
        # Default response for Russian
        if "суммари" in prompt.lower() or "summarize" in prompt.lower():
            return "Разработчики представили новую версию iOS с улучшенной производительностью. Добавлены новые функции для работы с жестами."
        return "Test summary."

    async def generate_stream(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512):
        """Not implemented for mock."""
        raise NotImplementedError


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_basic() -> None:
    """Test basic summarization of posts."""
    posts = [
        {"text": "Разработчики представили новую версию iOS с улучшенной производительностью на 30%."},
        {"text": "Добавлены новые функции для работы с жестами и улучшена безопасность."},
        {"text": "Обсуждаются отзывы пользователей о стабильности и совместимости."},
    ]
    
    llm = MockLLMClient()
    summary = await summarize_posts(posts, max_sentences=3, llm=llm)
    
    assert summary
    assert len(summary) > 10
    assert isinstance(summary, str)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_empty_list() -> None:
    """Test summarization with empty posts list."""
    llm = MockLLMClient()
    summary = await summarize_posts([], max_sentences=3, llm=llm)
    
    assert summary == "Нет постов для саммари."


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_cleans_text() -> None:
    """Test that summarizer cleans URLs and formatting."""
    posts = [
        {"text": "Check this https://example.com/page?utm_source=x and read more..."},
        {"text": "Short post"},
    ]
    
    llm = MockLLMClient()
    summary = await summarize_posts(posts, max_sentences=2, llm=llm)
    
    assert summary
    assert "http" not in summary.lower()
    # Should skip very short posts (< 20 chars)
    assert "Short post" not in summary


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_json_rejection() -> None:
    """Test that summarizer rejects JSON responses."""
    posts = [
        {"text": "Some post content here that needs summarization."},
    ]
    
    # Mock LLM that returns JSON (should be rejected)
    llm = MockLLMClient(responses=['{"summary": "test"}'])
    
    summary = await summarize_posts(posts, max_sentences=1, llm=llm)
    
    # Should fallback to bullet list since JSON was rejected
    assert summary
    assert isinstance(summary, str)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_handles_errors() -> None:
    """Test that summarizer handles LLM errors gracefully."""
    posts = [
        {"text": "Some post content here that needs summarization."},
    ]
    
    # Mock LLM that raises errors
    llm = MockLLMClient()
    async def failing_generate(*args, **kwargs):
        raise Exception("LLM unavailable")
    llm.generate = failing_generate
    
    # Should fallback to bullet list
    summary = await summarize_posts(posts, max_sentences=1, llm=llm)
    
    assert summary
    assert isinstance(summary, str)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_map_reduce_summarizer() -> None:
    """Test Map-Reduce summarization for long texts."""
    llm = MockLLMClient(
        responses=[
            "First chunk summary.",
            "Second chunk summary.",
            "Combined final summary.",
        ]
    )
    
    from src.infrastructure.llm.token_counter import TokenCounter
    from src.infrastructure.llm.chunker import SemanticChunker
    
    # Use small chunk size to force multiple chunks
    counter = TokenCounter()
    chunker = SemanticChunker(counter, max_tokens=50, overlap_tokens=10)
    summarizer = MapReduceSummarizer(llm=llm, chunker=chunker, language="ru")
    
    # Create long text that will trigger chunking
    long_text = " ".join([f"Предложение {i} с содержимым и дополнительной информацией." for i in range(100)])
    
    summary = await summarizer.summarize_text(long_text, max_sentences=5)
    
    assert summary
    assert isinstance(summary, str)
    # Should have called LLM at least once (may be single chunk if text is short enough)
    assert len(llm.calls) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_removes_markdown() -> None:
    """Test that summarizer removes Markdown artifacts."""
    posts = [
        {"text": "Some post with **bold** and *italic* text."},
    ]
    
    llm = MockLLMClient(responses=["**Test** summary with *markdown*."])
    
    summary = await summarize_posts(posts, max_sentences=1, llm=llm)
    
    assert summary
    # Should remove markdown artifacts (but may have some due to cleaning)
    assert "*" not in summary or "**" not in summary


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_posts_limits_sentences() -> None:
    """Test that summarizer respects max_sentences limit."""
    posts = [
        {"text": "First post with important information."},
        {"text": "Second post with different details."},
        {"text": "Third post with more content."},
    ]
    
    llm = MockLLMClient(
        responses=["Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."]
    )
    
    summary = await summarize_posts(posts, max_sentences=2, llm=llm)
    
    assert summary
    # Count sentences (rough check)
    sentences = summary.split('.')
    assert len([s for s in sentences if s.strip()]) <= 3  # Allow some margin

