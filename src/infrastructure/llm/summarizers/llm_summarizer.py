"""Direct LLM summarizer implementation."""

from __future__ import annotations

import re
from typing import Any

from src.domain.services.summary_quality_checker import (
    QualityScore,
    SummaryQualityChecker,
)
from src.domain.services.text_cleaner import TextCleanerService
from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.llm.prompts.summarization_prompts import (
    get_direct_summarization_prompt,
)
from src.infrastructure.llm.token_counter import TokenCounter


class LLMSummarizer:
    """Direct LLM summarizer (no Map-Reduce).

    Purpose:
        Implements SummarizerService using direct LLM calls.
        Suitable for texts that fit within token limits.

    Args:
        llm_client: LLM client for generation.
        token_counter: Token counter for validation.
        text_cleaner: Text cleaning service.
        quality_checker: Quality checking service.
        temperature: Sampling temperature (default: 0.5).
        max_tokens: Maximum tokens for generation (default: 2000).
        max_retries: Maximum retry attempts (default: 2).
    """

    def __init__(
        self,
        llm_client: LLMClient,
        token_counter: TokenCounter,
        text_cleaner: TextCleanerService,
        quality_checker: SummaryQualityChecker,
        temperature: float = 0.5,
        max_tokens: int = 2000,
        max_retries: int = 2,
    ) -> None:
        self.llm_client = llm_client
        self.token_counter = token_counter
        self.text_cleaner = text_cleaner
        self.quality_checker = quality_checker
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

    async def summarize_text(
        self,
        text: str,
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize text using direct LLM call.

        Purpose:
            Generates summary directly from text without chunking.
            Includes quality checking and retry logic.

        Args:
            text: Input text to summarize.
            max_sentences: Maximum sentences in summary.
            language: Target language (ru/en).
            context: Optional summarization context.

        Returns:
            SummaryResult with summary and metadata.
        """
        # Clean input text
        cleaned_text = self.text_cleaner.clean_for_summarization(text)

        # Build prompt
        time_period = context.time_period_hours if context else None
        max_chars = context.max_chars if context else None
        channel_username = context.channel_username if context else None
        channel_title = context.channel_title if context else None
        prompt = get_direct_summarization_prompt(
            text=cleaned_text,
            language=language,
            max_sentences=max_sentences,
            time_period_hours=time_period,
            max_chars=max_chars,
            channel_username=channel_username,
            channel_title=channel_title,
        )

        # Generate with retry
        summary_text = ""
        quality: QualityScore | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self.llm_client.generate(
                    prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                # Clean response
                summary_text = self.text_cleaner.clean_llm_response(response)

                # Post-process: ensure proper sentence count
                summary_text = self._finalize_summary(
                    summary_text, max_sentences, language
                )

                # Check quality
                quality = self.quality_checker.check_quality(
                    summary_text, cleaned_text, max_sentences
                )

                # If quality is acceptable, return
                if not self.quality_checker.should_retry(quality):
                    break

            except Exception:
                if attempt == self.max_retries - 1:
                    # Last attempt failed, use fallback
                    summary_text = self._fallback_summary(cleaned_text, language)
                    break
                # Retry on next attempt
                continue

        # Count sentences
        sentences = self._split_sentences(summary_text)
        sentences_count = len(sentences)

        # Build metadata
        metadata: dict[str, Any] = {
            "method": "direct",
            "attempts": attempt + 1 if "attempt" in locals() else 1,
            "quality_score": quality.score if quality else None,
            "input_tokens": self.token_counter.count_tokens(cleaned_text),
            "output_tokens": self.token_counter.count_tokens(summary_text),
        }

        return SummaryResult(
            text=summary_text,
            sentences_count=sentences_count,
            method="direct",
            confidence=quality.score if quality else 0.5,
            metadata=metadata,
        )

    async def summarize_posts(
        self,
        posts: list[PostContent],
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize multiple posts.

        Purpose:
            Concatenates posts and calls summarize_text.

        Args:
            posts: List of posts to summarize.
            max_sentences: Maximum sentences in summary.
            language: Target language.
            context: Optional context.

        Returns:
            SummaryResult with summary and metadata.
        """
        # Clean and combine posts
        cleaned_posts = []
        for post in posts:
            cleaned = self.text_cleaner.clean_for_summarization(post.text)
            if cleaned and len(cleaned) > 20:
                # Increased limit to 1000 chars per post for better context
                cleaned_posts.append(cleaned[:1000])

        # Verify all posts belong to the same channel (if context provided)
        if context and context.channel_username:
            wrong_channel_posts = [
                i
                for i, post in enumerate(posts)
                if post.channel_username
                and post.channel_username != context.channel_username
            ]
            if wrong_channel_posts:
                from src.infrastructure.logging import get_logger

                logger = get_logger("llm_summarizer")
                logger.warning(
                    f"Found {len(wrong_channel_posts)} posts from different channel in LLMSummarizer. "
                    f"Expected: {context.channel_username}, filtering them out."
                )
                cleaned_posts = [
                    cleaned
                    for i, cleaned in enumerate(cleaned_posts)
                    if i not in wrong_channel_posts
                ]
                posts = [
                    post for i, post in enumerate(posts) if i not in wrong_channel_posts
                ]

        if not cleaned_posts:
            # Fallback: return empty summary
            return SummaryResult(
                text="Нет пригодных постов для суммаризации."
                if language == "ru"
                else "No suitable posts for summarization.",
                sentences_count=0,
                method="direct",
                confidence=0.0,
                metadata={"method": "direct", "reason": "no_suitable_posts"},
            )

        # Combine posts into text
        combined_text = "\n".join(
            f"{i+1}. {text}" for i, text in enumerate(cleaned_posts)
        )

        # Summarize combined text
        return await self.summarize_text(
            combined_text,
            max_sentences=max_sentences,
            language=language,
            context=context,
        )

    def _finalize_summary(self, summary: str, max_sentences: int, language: str) -> str:
        """Finalize summary: ensure proper sentence count and format.

        Args:
            summary: Raw summary text.
            max_sentences: Maximum sentences.
            language: Target language.

        Returns:
            Finalized summary text.
        """
        sentences = self._split_sentences(summary)

        # Deduplicate
        unique_sentences = self.text_cleaner.deduplicate_sentences(sentences)

        # Limit to max_sentences
        if len(unique_sentences) > max_sentences:
            unique_sentences = unique_sentences[:max_sentences]

        # Join sentences
        result = ". ".join(unique_sentences)
        if not result.endswith((".", "!", "?")):
            result += "."

        return result

    def _fallback_summary(self, text: str, language: str) -> str:
        """Generate fallback summary when LLM fails.

        Args:
            text: Input text.
            language: Target language.

        Returns:
            Simple fallback summary.
        """
        # Extract first sentences from text
        sentences = self._split_sentences(text)
        if sentences:
            return ". ".join(sentences[:3]) + "."

        if language == "ru":
            return "Обсуждаются основные темы и новости."
        return "Main topics and news are discussed."

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        pattern = r"[.!?…]+"
        sentences = re.split(pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]
