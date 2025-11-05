"""Use case for requesting async channel digest generation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.value_objects.long_summarization_task import LongSummarizationTask
from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.task_status import TaskStatus
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.agent_metrics import long_tasks_total
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository

logger = get_logger("use_cases.request_channel_digest_async")


class RequestChannelDigestAsyncUseCase:
    """Use case for requesting async channel digest generation.

    Purpose:
        Creates and enqueues a long-running summarization task.
        Returns immediately with task ID and acknowledgment message.
        Actual summarization happens in background worker.

    Args:
        long_tasks_repository: Optional LongTasksRepository.
        settings: Optional settings.
    """

    def __init__(
        self,
        long_tasks_repository: LongTasksRepository | None = None,
        settings: Any = None,
    ) -> None:
        """Initialize use case.

        Args:
            long_tasks_repository: Optional LongTasksRepository instance.
            settings: Optional settings instance.
        """
        self._long_tasks_repository = long_tasks_repository
        self._settings = settings or get_settings()

    async def execute(
        self,
        user_id: int,
        chat_id: int,
        channel_username: str | None = None,
        hours: int = 72,
        language: str | None = None,
        max_sentences: int | None = None,
        max_chars: int | None = None,
    ) -> dict[str, str]:
        """Execute async digest request.

        Purpose:
            Creates a long-running task and enqueues it for processing.
            Returns task ID and acknowledgment message.

        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID for sending results.
            channel_username: Optional channel username (None = all channels).
            hours: Time window in hours.
            language: Language for summary ("ru" | "en").
            max_sentences: Maximum sentences in summary.
            max_chars: Optional maximum characters (soft limit).

        Returns:
            Dictionary with task_id and ack_message.

        Raises:
            ValueError: If inputs are invalid.
        """
        # Use settings defaults if not provided
        if language is None:
            language = self._settings.summarizer_language
        if max_sentences is None:
            max_sentences = self._settings.digest_summary_sentences

        logger.info(
            f"Requesting async digest: user_id={user_id}, chat_id={chat_id}, "
            f"channel={channel_username}, hours={hours}, max_sentences={max_sentences}, language={language}"
        )

        # Validate inputs
        if user_id <= 0:
            raise ValueError("user_id must be positive")
        if chat_id <= 0:
            raise ValueError("chat_id must be positive")
        if hours <= 0:
            raise ValueError("hours must be positive")

        # Create task ID
        task_id = f"digest_{uuid.uuid4().hex[:12]}_{int(datetime.now(timezone.utc).timestamp())}"

        # Create context
        context = SummarizationContext(
            time_period_hours=hours,
            source_type="telegram_posts",
            max_chars=max_chars or self._settings.digest_summary_max_chars,
            language=language,
            max_sentences=max_sentences,
        )

        # Create task
        task = LongSummarizationTask(
            task_id=task_id,
            user_id=user_id,
            chat_id=chat_id,
            channel_username=channel_username.lstrip("@") if channel_username else None,
            context=context,
            status=TaskStatus.QUEUED,
        )

        # Get repository
        if self._long_tasks_repository is None:
            db = await get_db()
            repo = LongTasksRepository(db)
        else:
            repo = self._long_tasks_repository

        # Save task
        await repo.create(task)

        # Record metric
        long_tasks_total.labels(status="queued").inc()

        # Generate acknowledgment message
        if channel_username:
            ack_message = (
                f"Принял задачу на создание дайджеста канала {channel_username} "
                f"за {hours} часов. Пришлю результат отдельным сообщением."
            )
        else:
            ack_message = (
                f"Принял задачу на создание дайджеста по всем каналам "
                f"за {hours} часов. Пришлю результат отдельным сообщением."
            )

        logger.info(f"Created async task: task_id={task_id}, user_id={user_id}")

        return {
            "task_id": task_id,
            "ack_message": ack_message,
        }

