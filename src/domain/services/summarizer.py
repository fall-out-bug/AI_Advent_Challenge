"""Summarizer service interface."""

from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult


class SummarizerService(Protocol):
    """Protocol for summarization services.

    Purpose:
        Defines the interface for text summarization operations.
        Implementations can use different strategies (direct LLM, Map-Reduce, etc.).
    """

    async def summarize_text(
        self,
        text: str,
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize a text string.

        Purpose:
            Generate a summary from a single text string using
            the configured summarization strategy.

        Args:
            text: Input text to summarize.
            max_sentences: Maximum number of sentences in summary.
            language: Target language code (default: "ru").
            context: Optional context for summarization.

        Returns:
            SummaryResult with summary text and metadata.

        Raises:
            Exception: On summarization errors (implementation-specific).
        """
        ...

    async def summarize_posts(
        self,
        posts: list[PostContent],
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize multiple posts.

        Purpose:
            Generate a summary from a list of posts.
            Typically concatenates posts and calls summarize_text.

        Args:
            posts: List of PostContent objects.
            max_sentences: Maximum number of sentences in summary.
            language: Target language code (default: "ru").
            context: Optional context for summarization.

        Returns:
            SummaryResult with summary text and metadata.

        Raises:
            Exception: On summarization errors (implementation-specific).
        """
        ...
