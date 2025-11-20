"""Adaptive summarizer that chooses strategy based on text length."""

from __future__ import annotations

from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.llm.summarizers.llm_summarizer import LLMSummarizer
from src.infrastructure.llm.summarizers.map_reduce_summarizer import MapReduceSummarizer
from src.infrastructure.llm.token_counter import TokenCounter


class AdaptiveSummarizer:
    """Adaptive summarizer that selects strategy automatically.

    Purpose:
        Chooses between direct LLM summarization and Map-Reduce
        based on text token count. Provides transparent interface
        while optimizing for different text lengths.

    Args:
        direct_summarizer: LLMSummarizer for short texts.
        map_reduce_summarizer: MapReduceSummarizer for long texts.
        token_counter: Token counter for length evaluation.
        threshold_tokens: Token threshold for switching strategies (default: 3000).
    """

    def __init__(
        self,
        direct_summarizer: LLMSummarizer,
        map_reduce_summarizer: MapReduceSummarizer,
        token_counter: TokenCounter,
        threshold_tokens: int = 3000,
    ) -> None:
        self.direct_summarizer = direct_summarizer
        self.map_reduce_summarizer = map_reduce_summarizer
        self.token_counter = token_counter
        self.threshold_tokens = threshold_tokens

    async def summarize_text(
        self,
        text: str,
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize text using adaptive strategy selection.

        Purpose:
            Evaluates text length and chooses appropriate strategy.
            Short texts use direct summarization, long texts use Map-Reduce.

        Args:
            text: Input text to summarize.
            max_sentences: Maximum sentences in summary.
            language: Target language.
            context: Optional context.

        Returns:
            SummaryResult with summary and metadata.
        """
        # Count tokens
        token_count = self.token_counter.count_tokens(text)

        # Select strategy based on token count
        if token_count > self.threshold_tokens:
            # Use Map-Reduce for long texts
            result = await self.map_reduce_summarizer.summarize_text(
                text, max_sentences=max_sentences, language=language, context=context
            )
            # Add adaptive metadata
            result.metadata["adaptive_strategy"] = "map_reduce"
            result.metadata["token_count"] = token_count
            result.metadata["threshold"] = self.threshold_tokens
            return result
        else:
            # Use direct summarization for short texts
            result = await self.direct_summarizer.summarize_text(
                text, max_sentences=max_sentences, language=language, context=context
            )
            # Add adaptive metadata
            result.metadata["adaptive_strategy"] = "direct"
            result.metadata["token_count"] = token_count
            result.metadata["threshold"] = self.threshold_tokens
            return result

    async def summarize_posts(
        self,
        posts: list[PostContent],
        max_sentences: int,
        language: str = "ru",
        context: SummarizationContext | None = None,
    ) -> SummaryResult:
        """Summarize multiple posts using adaptive strategy.

        Purpose:
            Combines posts and uses adaptive strategy selection.

        Args:
            posts: List of posts to summarize.
            max_sentences: Maximum sentences in summary.
            language: Target language.
            context: Optional context.

        Returns:
            SummaryResult with summary and metadata.
        """
        # Combine posts into text
        from src.domain.services.text_cleaner import TextCleanerService

        text_cleaner = TextCleanerService()
        cleaned_posts = []
        for post in posts:
            cleaned = text_cleaner.clean_for_summarization(post.text)
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
                logger.warning(
                    f"Found {len(wrong_channel_posts)} posts from different channel in AdaptiveSummarizer. "
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
            return SummaryResult(
                text=(
                    "Нет пригодных постов для суммаризации."
                    if language == "ru"
                    else "No suitable posts."
                ),
                sentences_count=0,
                method="direct",
                confidence=0.0,
                metadata={"method": "adaptive", "reason": "no_suitable_posts"},
            )

        combined_text = "\n\n".join(cleaned_posts)

        # Log before summarization for debugging
        from src.infrastructure.logging import get_logger

        logger = get_logger("adaptive_summarizer")
        logger.info(
            f"Summarizing posts: posts_count={len(posts)}, "
            f"cleaned_posts_count={len(cleaned_posts)}, "
            f"combined_text_length={len(combined_text)}, "
            f"max_sentences={max_sentences}, language={language}"
        )

        try:
            result = await self.summarize_text(
                combined_text,
                max_sentences=max_sentences,
                language=language,
                context=context,
            )
            logger.info(
                f"Summary generated: method={result.method}, "
                f"sentences={result.sentences_count}, "
                f"confidence={result.confidence}, "
                f"strategy={result.metadata.get('adaptive_strategy', 'unknown')}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in adaptive summarization: type={type(e).__name__}, "
                f"error={str(e)}, posts_count={len(posts)}, "
                f"cleaned_posts_count={len(cleaned_posts)}",
                exc_info=True,
            )
            # Return error summary instead of raising
            return SummaryResult(
                text=(
                    "Ошибка при генерации суммаризации."
                    if language == "ru"
                    else "Error generating summary."
                ),
                sentences_count=0,
                method="error",
                confidence=0.0,
                metadata={
                    "method": "adaptive",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
