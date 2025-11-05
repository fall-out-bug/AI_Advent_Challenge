"""Map-Reduce summarizer for long texts."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from src.domain.services.summarizer import SummarizerService
from src.domain.services.summary_quality_checker import (
    QualityScore,
    SummaryQualityChecker,
)
from src.domain.services.text_cleaner import TextCleanerService
from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.llm.chunking.semantic_chunker import SemanticChunker
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.llm.prompts.summarization_prompts import (
    get_map_prompt,
    get_reduce_prompt,
)
from src.infrastructure.llm.token_counter import TokenCounter

try:
    from prometheus_client import Counter, Histogram  # type: ignore

    _map_phase_duration = Histogram(
        "map_reduce_map_phase_duration_seconds",
        "Time spent in Map phase",
    )
    _reduce_phase_duration = Histogram(
        "map_reduce_reduce_phase_duration_seconds",
        "Time spent in Reduce phase",
    )
    _chunks_processed = Counter(
        "map_reduce_chunks_processed_total",
        "Total chunks processed in Map phase",
    )
except Exception:  # pragma: no cover - metrics are optional
    _map_phase_duration = None
    _reduce_phase_duration = None
    _chunks_processed = None


class MapReduceSummarizer:
    """Map-Reduce summarizer for long texts.

    Purpose:
        Implements SummarizerService using Map-Reduce strategy:
        - Map: Summarize each chunk in parallel
        - Reduce: Combine chunk summaries into final summary

    Args:
        llm_client: LLM client for generation.
        chunker: Semantic chunker for text splitting.
        token_counter: Token counter for validation.
        text_cleaner: Text cleaning service.
        quality_checker: Quality checking service.
        temperature: Sampling temperature (default: 0.2 for deterministic output).
        map_max_tokens: Max tokens for Map phase (default: 600).
        reduce_max_tokens: Max tokens for Reduce phase (default: 2000).
    """

    def __init__(
        self,
        llm_client: LLMClient,
        chunker: SemanticChunker,
        token_counter: TokenCounter,
        text_cleaner: TextCleanerService,
        quality_checker: SummaryQualityChecker,
        temperature: float = 0.2,
        map_max_tokens: int = 600,
        reduce_max_tokens: int = 2000,
    ) -> None:
        self.llm_client = llm_client
        self.chunker = chunker
        self.token_counter = token_counter
        self.text_cleaner = text_cleaner
        self.quality_checker = quality_checker
        self.temperature = temperature
        self.map_max_tokens = map_max_tokens
        self.reduce_max_tokens = reduce_max_tokens

    async def summarize_text(
        self,
        text: str,
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize text using Map-Reduce strategy.

        Purpose:
            Splits text into chunks, summarizes each chunk (Map),
            then combines summaries (Reduce).

        Args:
            text: Input text to summarize.
            max_sentences: Maximum sentences in final summary.
            language: Target language.
            context: Optional context.

        Returns:
            SummaryResult with summary and metadata.
        """
        start_time = time.time()

        # Clean input
        cleaned_text = self.text_cleaner.clean_for_summarization(text, max_length_per_item=10000)

        # Chunk text
        chunks = self.chunker.chunk_text(cleaned_text)

        # If single chunk, use direct summarization
        if len(chunks) == 1:
            chunk = chunks[0]
            map_result = await self._summarize_chunk(
                chunk, max_sentences=max_sentences, language=language, context=context
            )
            duration = time.time() - start_time

            sentences = self._split_sentences(map_result)
            return SummaryResult(
                text=map_result,
                sentences_count=len(sentences),
                method="map_reduce",
                confidence=1.0,
                metadata={
                    "method": "map_reduce",
                    "chunks": 1,
                    "duration": duration,
                    "phase": "single_chunk",
                },
            )

        # Map phase: summarize chunks in parallel
        map_start = time.time()
        chunk_summaries = await asyncio.gather(
            *[
                self._summarize_chunk(
                    chunk,
                    max_sentences=max(3, max_sentences // 2),
                    language=language,
                    context=context,
                )
                for chunk in chunks
            ]
        )
        map_duration = time.time() - map_start

        if _map_phase_duration:
            _map_phase_duration.observe(map_duration)
        if _chunks_processed:
            _chunks_processed.inc(len(chunks))

        # Reduce phase: combine summaries
        reduce_start = time.time()
        combined = "\n\n".join(
            [f"Fragment {i+1}:\n{s}" for i, s in enumerate(chunk_summaries)]
        )
        # Pass channel context to reduce prompt for better isolation
        channel_username = context.channel_username if context else None
        channel_title = context.channel_title if context else None
        reduce_prompt = get_reduce_prompt(
            summaries=combined, language=language, max_sentences=max_sentences
        )
        # Note: get_reduce_prompt already has channel isolation built in

        reduce_response = await self.llm_client.generate(
            reduce_prompt,
            temperature=self.temperature,
            max_tokens=self.reduce_max_tokens,
        )

        # Clean and finalize
        summary_text = self.text_cleaner.clean_llm_response(reduce_response)
        summary_text = self._finalize_summary(summary_text, max_sentences, language)

        reduce_duration = time.time() - reduce_start
        total_duration = time.time() - start_time

        if _reduce_phase_duration:
            _reduce_phase_duration.observe(reduce_duration)

        # Check quality
        quality = self.quality_checker.check_quality(
            summary_text, cleaned_text, max_sentences
        )

        sentences = self._split_sentences(summary_text)

        metadata: dict[str, Any] = {
            "method": "map_reduce",
            "chunks": len(chunks),
            "map_duration": map_duration,
            "reduce_duration": reduce_duration,
            "total_duration": total_duration,
            "quality_score": quality.score,
            "input_tokens": sum(c.token_count for c in chunks),
            "output_tokens": self.token_counter.count_tokens(summary_text),
        }

        return SummaryResult(
            text=summary_text,
            sentences_count=len(sentences),
            method="map_reduce",
            confidence=quality.score,
            metadata=metadata,
        )

    async def summarize_posts(
        self,
        posts: list[PostContent],
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize multiple posts using Map-Reduce.

        Purpose:
            Combines posts into text and uses Map-Reduce summarization.

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
                i for i, post in enumerate(posts)
                if post.channel_username and post.channel_username != context.channel_username
            ]
            if wrong_channel_posts:
                from src.infrastructure.logging import get_logger
                logger = get_logger("map_reduce_summarizer")
                logger.warning(
                    f"Found {len(wrong_channel_posts)} posts from different channel in MapReduceSummarizer. "
                    f"Expected: {context.channel_username}, filtering them out."
                )
                cleaned_posts = [
                    cleaned for i, cleaned in enumerate(cleaned_posts)
                    if i not in wrong_channel_posts
                ]
                posts = [
                    post for i, post in enumerate(posts)
                    if i not in wrong_channel_posts
                ]

        if not cleaned_posts:
            return SummaryResult(
                text="Нет пригодных постов для суммаризации." if language == "ru" else "No suitable posts.",
                sentences_count=0,
                method="map_reduce",
                confidence=0.0,
                metadata={"method": "map_reduce", "reason": "no_suitable_posts"},
            )

        combined_text = "\n\n".join(cleaned_posts)
        return await self.summarize_text(
            combined_text, max_sentences=max_sentences, language=language, context=context
        )

    async def _summarize_chunk(
        self, chunk, max_sentences: int, language: str
    ) -> str:
        """Summarize a single chunk (Map phase).

        Args:
            chunk: TextChunk to summarize.
            max_sentences: Max sentences for this chunk.
            language: Target language.

        Returns:
            Chunk summary text.
        """
        map_prompt = get_map_prompt(
            text=chunk.text, language=language, max_sentences=max_sentences
        )

        response = await self.llm_client.generate(
            map_prompt,
            temperature=self.temperature,
            max_tokens=self.map_max_tokens,
        )

        # Clean response
        cleaned = self.text_cleaner.clean_llm_response(response)
        return cleaned

    def _finalize_summary(
        self, summary: str, max_sentences: int, language: str
    ) -> str:
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

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        import re

        pattern = r"[.!?…]+"
        sentences = re.split(pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]
