"""Use case for processing long summarization tasks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.services.summarizer import SummarizerService
from src.domain.value_objects.long_summarization_task import LongSummarizationTask
from src.domain.value_objects.post_content import PostContent
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.agent_metrics import (
    long_tasks_total,
    long_tasks_duration,
)
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository
from src.infrastructure.repositories.post_repository import PostRepository

logger = get_logger("use_cases.process_long_summarization_task")


class ProcessLongSummarizationTaskUseCase:
    """Use case for processing long summarization tasks.

    Purpose:
        Executes long-running summarization task with extended timeout.
        Generates summary and updates task status.
        Should be called by background worker.

    Args:
        long_tasks_repository: Optional LongTasksRepository.
        post_repository: Optional PostRepository.
        summarizer: Optional SummarizerService.
        settings: Optional settings.
    """

    def __init__(
        self,
        long_tasks_repository: LongTasksRepository | None = None,
        post_repository: PostRepository | None = None,
        summarizer: SummarizerService | None = None,
        settings: Any = None,
    ) -> None:
        """Initialize use case.

        Args:
            long_tasks_repository: Optional LongTasksRepository instance.
            post_repository: Optional PostRepository instance.
            summarizer: Optional SummarizerService instance.
            settings: Optional settings instance.
        """
        self._long_tasks_repository = long_tasks_repository
        self._post_repository = post_repository
        self._summarizer = summarizer
        self._settings = settings or get_settings()

    async def execute(self, task: LongSummarizationTask) -> str:
        """Execute long summarization task.

        Purpose:
            Processes task with extended timeout, generates summary,
            and updates task status in database.

        Args:
            task: LongSummarizationTask to process.

        Returns:
            Generated summary text.

        Raises:
            ValueError: If task is invalid.
            RuntimeError: If summarization fails.
        """
        logger.info(
            f"Processing long task: task_id={task.task_id}, user_id={task.user_id}, "
            f"channel={task.channel_username}, hours={task.context.time_period_hours}"
        )

        # Get repositories
        if self._long_tasks_repository is None:
            db = await get_db()
            long_tasks_repo = LongTasksRepository(db)
        else:
            long_tasks_repo = self._long_tasks_repository

        if self._post_repository is None:
            db = await get_db()
            post_repo = PostRepository(db)
        else:
            post_repo = self._post_repository

        # Get posts
        hours = task.context.time_period_hours or 72
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        if task.channel_username:
            # Single channel digest - get posts from database
            posts_data = await post_repo.get_posts_by_channel(
                task.channel_username, since, user_id=task.user_id
            )
            channel_username = task.channel_username
        else:
            # All channels digest - get all posts for user's subscribed channels
            hours = task.context.time_period_hours or 72
            posts_data = await post_repo.get_posts_by_user_subscriptions(
                task.user_id, hours=hours
            )
            channel_username = None  # Will be aggregated

        if not posts_data:
            logger.warning(
                f"No posts found for task: task_id={task.task_id}, user_id={task.user_id}, "
                f"channel={task.channel_username}, hours={hours}"
            )
            language = task.context.language or "ru"
            result_text = (
                "Нет постов за указанный период."
                if language == "ru"
                else "No posts for the specified period."
            )
            await long_tasks_repo.complete(task.task_id, result_text)
            return result_text

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
                    channel_username=post_data.get("channel_username"),
                )
            )

        # Get summarizer with long timeout
        if self._summarizer is None:
            from src.infrastructure.di.factories import create_adaptive_summarizer_with_long_timeout

            summarizer = create_adaptive_summarizer_with_long_timeout()
        else:
            summarizer = self._summarizer

        # Generate summary with extended timeout
        max_sentences = task.context.max_sentences or self._settings.digest_summary_sentences
        language = task.context.language or "ru"
        max_chars = task.context.max_chars or self._settings.digest_summary_max_chars

        import time
        start_time = time.time()

        try:
            summary_result = await summarizer.summarize_posts(
                posts=post_contents,
                max_sentences=max_sentences,
                language=language,
                context=task.context,
            )

            result_text = summary_result.text
            duration = time.time() - start_time

            logger.info(
                f"Summary generated for task: task_id={task.task_id}, "
                f"method={summary_result.method}, length={len(result_text)}, "
                f"duration={duration:.2f}s"
            )

            # Update task status
            await long_tasks_repo.complete(task.task_id, result_text)

            # Record metrics
            long_tasks_total.labels(status="succeeded").inc()
            long_tasks_duration.labels(status="succeeded").observe(duration)

            return result_text

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Summarization failed: {str(e)}"
            logger.error(
                f"Failed to process task: task_id={task.task_id}, error={error_msg}, "
                f"duration={duration:.2f}s",
                exc_info=True,
            )
            await long_tasks_repo.fail(task.task_id, error_msg)

            # Record metrics
            long_tasks_total.labels(status="failed").inc()
            long_tasks_duration.labels(status="failed").observe(duration)

            raise RuntimeError(error_msg) from e

