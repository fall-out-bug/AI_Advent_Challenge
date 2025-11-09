"""Use case for generating channel digest by channel name."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.services.summarizer import SummarizerService
from src.domain.value_objects.post_content import PostContent
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summary_result import SummaryResult
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.post_repository import PostRepository

logger = get_logger("use_cases.generate_channel_digest_by_name")


class GenerateChannelDigestByNameUseCase:
    """Use case for generating digest for a specific channel.

    Purpose:
        Generates digest for a single channel by username.
        Includes automatic subscription and post collection.

    Args:
        post_repository: Optional PostRepository.
        summarizer: SummarizerService for generating summaries.
        settings: Optional settings.
    """

    def __init__(
        self,
        post_repository: PostRepository | None = None,
        summarizer: SummarizerService | None = None,
        settings: Any = None,
    ) -> None:
        self._post_repository = post_repository
        self._summarizer = summarizer
        self._settings = settings or get_settings()

    async def execute(
        self, user_id: int, channel_username: str, hours: int = 72
    ) -> ChannelDigest:
        """Execute channel digest generation by name.

        Purpose:
            Resolves channel, collects posts, and generates summary using AdaptiveSummarizer.

        Args:
            user_id: Telegram user ID.
            channel_username: Channel username without @.
            hours: Time window in hours.

        Returns:
            ChannelDigest object with summary and metadata.

        Raises:
            ValueError: If channel not found or invalid input.
        """
        logger.info(
            f"Generating channel digest by name: user_id={user_id}, channel={channel_username}, hours={hours}"
        )

        # Get repositories
        if self._post_repository is None:
            db = await get_db()
            post_repo = PostRepository(db)
        else:
            post_repo = self._post_repository

        # Clean username
        channel_username = channel_username.lstrip("@")

        # Get posts for channel from database (cached posts)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        posts_data = await post_repo.get_posts_by_channel(
            channel_username, since, user_id=user_id
        )

        # Get channel title from database
        db = await get_db()
        channel_doc = await db.channels.find_one(
            {"user_id": user_id, "channel_username": channel_username, "active": True}
        )
        channel_title = channel_doc.get("title") if channel_doc else None

        if not posts_data:
            logger.warning(
                f"No posts found in database for channel: {channel_username}, "
                f"hours={hours}, user_id={user_id}, since={since.isoformat()}. "
                f"Make sure post_fetcher_worker has collected posts for this channel."
            )
            # Return empty digest
            language = self._settings.summarizer_language
            return ChannelDigest(
                channel_username=channel_username,
                channel_title=channel_title,
                summary=SummaryResult(
                    text=(
                        "Нет постов за указанный период."
                        if language == "ru"
                        else "No posts for the specified period."
                    ),
                    sentences_count=0,
                    method="direct",
                    confidence=0.0,
                ),
                post_count=0,
                time_window_hours=hours,
                tags=[],
                generated_at=datetime.now(timezone.utc),
            )

        # Convert posts to PostContent
        post_contents = []
        for post_data in posts_data:
            post_date = None
            if isinstance(post_data.get("date"), str):
                try:
                    post_date = datetime.fromisoformat(
                        post_data["date"].replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass
            elif isinstance(post_data.get("date"), datetime):
                post_date = post_data["date"]

            post_contents.append(
                PostContent(
                    text=post_data.get("text", ""),
                    date=post_date,
                    message_id=post_data.get("message_id"),
                    channel_username=channel_username,
                )
            )

        # Generate summary using summarizer
        if self._summarizer is None:
            from src.infrastructure.di.factories import create_adaptive_summarizer

            summarizer = create_adaptive_summarizer()
        else:
            summarizer = self._summarizer

        max_sentences = self._settings.digest_summary_sentences
        language = self._settings.summarizer_language
        max_chars = self._settings.digest_summary_max_chars

        context = SummarizationContext(
            time_period_hours=hours,
            source_type="telegram_posts",
            max_chars=max_chars,
            language=language,
            max_sentences=max_sentences,
            channel_username=channel_username,
            channel_title=channel_title,
        )

        try:
            logger.info(
                f"Starting summarization: channel={channel_username}, "
                f"posts_count={len(post_contents)}, max_sentences={max_sentences}, "
                f"language={language}, hours={hours}"
            )

            # Log sample post data for debugging
            if post_contents:
                sample_posts = post_contents[:3]
                logger.debug(
                    f"Sample posts for summarization: "
                    f"count={len(sample_posts)}, "
                    f"first_post_length={len(sample_posts[0].text) if sample_posts else 0}, "
                    f"first_post_preview={sample_posts[0].text[:200] if sample_posts else 'N/A'}"
                )

            summary_result = await summarizer.summarize_posts(
                posts=post_contents,
                max_sentences=max_sentences,
                language=language,
                context=context,
            )

            logger.info(
                f"Summary generated successfully: channel={channel_username}, "
                f"method={summary_result.method}, sentences={summary_result.sentences_count}, "
                f"summary_length={len(summary_result.text)}, "
                f"confidence={summary_result.confidence}"
            )

            # Trigger async evaluation (fire-and-forget)
            # Only evaluate if summary was successfully generated (not error)
            if (
                self._settings.enable_quality_evaluation
                and summary_result.method != "error"
                and summary_result.confidence > 0
            ):
                # Combine posts text for evaluation
                combined_text = "\n\n".join(
                    post.text for post in post_contents if post.text
                )
                asyncio.create_task(
                    self._evaluate_summary_quality(
                        original_text=combined_text,
                        summary_result=summary_result,
                        context=context,
                    )
                )
        except Exception as e:
            logger.error(
                f"Error generating summary, using fallback: channel={channel_username}, "
                f"error_type={type(e).__name__}, error={str(e)}, "
                f"posts_count={len(post_contents)}, "
                f"max_sentences={max_sentences}, language={language}",
                exc_info=True,
            )
            # Fallback summary
            language = self._settings.summarizer_language
            summary_result = SummaryResult(
                text=(
                    "Ошибка при генерации суммаризации."
                    if language == "ru"
                    else "Error generating summary."
                ),
                sentences_count=0,
                method="direct",
                confidence=0.0,
                metadata={"error": str(e)},
            )

        # Extract tags from posts (if any)
        # Note: Tag extraction is currently minimal - extracts hashtags from post text
        # Future enhancement: Use NLP to identify topic tags, extract from metadata
        tags = []
        for post in posts:
            if post.text:
                # Extract hashtags
                hashtags = re.findall(r"#\w+", post.text)
                tags.extend([tag.lower().strip("#") for tag in hashtags])
        # Deduplicate and limit
        tags = list(set(tags))[:10]

        return ChannelDigest(
            channel_username=channel_username,
            channel_title=channel_title,
            summary=summary_result,
            post_count=len(posts_data),
            time_window_hours=hours,
            tags=tags,
            generated_at=datetime.now(timezone.utc),
        )

    async def _evaluate_summary_quality(
        self,
        original_text: str,
        summary_result: SummaryResult,
        context: SummarizationContext,
    ) -> None:
        """Evaluate summary quality asynchronously (background task).

        Purpose:
            Fire-and-forget task that evaluates summary quality using LLM,
            stores results in MongoDB for fine-tuning dataset creation.

        Args:
            original_text: Original combined text from posts.
            summary_result: Generated summary result.
            context: Summarization context.
        """
        try:
            from src.infrastructure.database.mongo import get_db
            from src.infrastructure.di.factories import create_summarization_evaluator
            from src.infrastructure.repositories.summarization_evaluation_repository import (
                SummarizationEvaluationRepository,
            )

            # Create evaluator
            evaluator = create_summarization_evaluator()

            # Evaluate
            evaluation = await evaluator.evaluate(
                original_text=original_text,
                summary_text=summary_result.text,
                context=context,
                summary_metadata=summary_result.metadata,
            )

            # Save to DB
            db = await get_db()
            repo = SummarizationEvaluationRepository(db)
            evaluation_id = await repo.save_evaluation(evaluation)

            logger.info(
                f"Summary evaluation complete: id={evaluation_id}, "
                f"score={evaluation.overall_score:.2f}"
            )
        except Exception as e:
            # Don't fail main flow if evaluation fails
            logger.error(f"Error evaluating summary quality: {e}", exc_info=True)
            # Evaluation is non-critical, just log and continue
