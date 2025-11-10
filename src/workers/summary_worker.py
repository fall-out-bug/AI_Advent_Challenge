"""Background worker for scheduled summaries and digests."""

from __future__ import annotations

import asyncio
import os
import signal
from datetime import datetime, time
import inspect
from typing import Any, Callable, Optional, Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from src.application.use_cases.process_long_summarization_task import (
    ProcessLongSummarizationTaskUseCase,
)
from src.domain.value_objects.task_type import TaskType
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.agent_metrics import (
    long_tasks_duration,
    long_tasks_queue_size,
    long_tasks_total,
)
from src.infrastructure.monitoring.worker_metrics import (
    record_worker_task,
    set_worker_queue_depth,
)
from src.infrastructure.notifiers.telegram_notifier import TelegramNotifier
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository
from src.presentation.mcp.client import get_mcp_client
from src.presentation.mcp.http_client import MCPHTTPClient
from src.workers.data_fetchers import get_digest_texts, get_summary_text
from src.workers.formatters import clean_markdown
from src.workers.schedulers import is_quiet_hours, is_time_to_send

logger = get_logger("summary_worker")

# Constants
CHECK_INTERVAL_SECONDS = 60
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0
SAFE_MESSAGE_LIMIT = 4000


class SummaryWorker:
    """Background worker for scheduled notifications.

    Purpose:
        Send morning summaries and evening digests at configured times,
        respecting quiet hours. Coordinates data fetching, formatting,
        and message sending.
    """

    def __init__(self, bot_token: str, mcp_url: Optional[str] = None) -> None:
        """Initialize worker.

        Args:
            bot_token: Telegram bot token
            mcp_url: Optional MCP server URL (defaults to stdio)
        """
        self.bot = Bot(token=bot_token)
        mcp_url = mcp_url or os.getenv("MCP_SERVER_URL")
        self.mcp = get_mcp_client(server_url=mcp_url)
        self.settings = get_settings()
        logger.info(
            f"Worker settings loaded: debug_interval={self.settings.debug_notification_interval_minutes}, "
            f"morning_time={self.settings.morning_summary_time}, "
            f"evening_time={self.settings.evening_digest_time}"
        )
        self._running = False
        self._last_debug_send: Optional[datetime] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received shutdown signal: {signum}")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self) -> None:
        """Main worker loop."""
        self._running = True
        logger.info("Unified task worker started (summarization + review)")
        try:
            while self._running:
                try:
                    await self._check_and_send()
                    # Process summarization tasks if enabled
                    if self.settings.enable_async_long_summarization:
                        await self._process_long_tasks()
                    # Process review tasks
                    await self._process_review_tasks()
                    await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                except Exception as e:
                    logger.error(f"Worker error in main loop: {e}", exc_info=True)
                    await asyncio.sleep(300)  # Wait 5 min on error
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up worker resources")
        await self.bot.session.close()

    def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping worker")
        self._running = False

    async def _process_long_tasks(self) -> None:
        """Process long summarization tasks from queue.

        Purpose:
            Polls for queued long tasks, processes them with extended timeout,
            and sends results via Telegram.
        """
        if not self.settings.enable_async_long_summarization:
            return

        try:
            db = await get_db()
            long_tasks_repo = LongTasksRepository(db)
            notifier = TelegramNotifier(self.bot)

            # Update queue size metric (count all queued tasks)
            from src.domain.value_objects.task_status import TaskStatus

            queued_count = await db.long_tasks.count_documents(
                {"status": TaskStatus.QUEUED.value}
            )
            long_tasks_queue_size.set(queued_count)
            set_worker_queue_depth("summarization", queued_count)

            # Pick next queued summarization task (filter by type)
            task = await long_tasks_repo.pick_next_queued(
                task_type=TaskType.SUMMARIZATION
            )

            if not task:
                return  # No tasks to process

            import time

            start_time = time.time()

            logger.info(
                f"Processing summarization task: task_id={task.task_id}, user_id={task.user_id}, "
                f"channel={task.channel_username}"
            )

            # Record metric
            long_tasks_total.labels(status="running").inc()

            # Process summarization task
            process_use_case = ProcessLongSummarizationTaskUseCase(
                long_tasks_repository=long_tasks_repo,
            )

            try:
                result_text = await process_use_case.execute(task)

                # Send result to user
                if task.channel_username:
                    message = (
                        f"📋 Дайджест канала {task.channel_username}:\n\n{result_text}"
                    )
                else:
                    message = f"📋 Дайджест по всем каналам:\n\n{result_text}"

                await notifier.send_message(task.chat_id, message)

                duration = time.time() - start_time
                record_worker_task("summarization", "success", duration)
                logger.info(
                    f"Summarization task completed and sent: task_id={task.task_id}, "
                    f"user_id={task.user_id}, result_length={len(result_text)}, "
                    f"duration={duration:.2f}s"
                )

            except Exception as e:
                duration = time.time() - start_time
                record_worker_task("summarization", "error", duration)
                error_msg = f"Ошибка при создании дайджеста: {str(e)[:200]}"
                logger.error(
                    f"Summarization task failed: task_id={task.task_id}, error={error_msg}, "
                    f"duration={duration:.2f}s",
                    exc_info=True,
                )

                # Send error message to user
                try:
                    await notifier.send_message(
                        task.chat_id,
                        f"❌ {error_msg}\n\nTask ID: {task.task_id}",
                    )
                except Exception as notify_error:
                    logger.error(
                        f"Failed to send error notification: task_id={task.task_id}, "
                        f"error={notify_error}",
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(f"Error processing summarization tasks: {e}", exc_info=True)

    async def _process_review_tasks(self) -> None:
        """Process code review tasks from queue.

        Purpose:
            Polls for queued code review tasks, processes them using
            ReviewSubmissionUseCase, and updates task status.
        """
        try:
            db = await get_db()
            long_tasks_repo = LongTasksRepository(db)

            # Update queue size metric for review tasks
            queued_count = await long_tasks_repo.get_queue_size(
                task_type=TaskType.CODE_REVIEW
            )
            set_worker_queue_depth("code_review", queued_count)

            # Pick next queued review task (filter by type)
            task = await long_tasks_repo.pick_next_queued(
                task_type=TaskType.CODE_REVIEW
            )

            if not task:
                return  # No tasks to process

            import time

            start_time = time.time()

            logger.info(
                f"Processing review task: task_id={task.task_id}, user_id={task.user_id}"
            )

            # Record metric (reuse existing metric for now)
            long_tasks_total.labels(status="running").inc()

            # Process review task
            # Import here to avoid circular dependencies
            import sys
            from pathlib import Path

            from src.application.use_cases.review_submission_use_case import (
                ReviewSubmissionUseCase,
            )
            from src.domain.services.diff_analyzer import DiffAnalyzer
            from src.infrastructure.archive.archive_service import ZipArchiveService
            from src.infrastructure.clients.external_api_client import ExternalAPIClient
            from src.infrastructure.clients.external_api_mock import (
                ExternalAPIClientMock,
            )
            from src.infrastructure.repositories.homework_review_repository import (
                HomeworkReviewRepository,
            )

            # Add shared to path for UnifiedModelClient
            _root = Path(__file__).parent.parent.parent.parent
            sys.path.insert(0, str(_root))
            shared_path = _root / "shared"
            sys.path.insert(0, str(shared_path))

            try:
                from shared_package.clients.unified_client import UnifiedModelClient
            except ImportError:
                try:
                    from shared.clients.unified_client import UnifiedModelClient
                except ImportError:
                    shared_package_path = _root / "shared" / "shared_package"
                    if shared_package_path.exists():
                        sys.path.insert(0, str(shared_package_path.parent))
                        from shared_package.clients.unified_client import (
                            UnifiedModelClient,
                        )
                    else:
                        raise RuntimeError("UnifiedModelClient not available")

            # Initialize dependencies
            archive_service = ZipArchiveService(self.settings)
            diff_analyzer = DiffAnalyzer()
            review_repo = HomeworkReviewRepository(db)

            # UnifiedModelClient reads LLM_URL from environment or settings
            # Ensure LLM_URL is set in environment for UnifiedModelClient
            llm_url = self.settings.llm_url or os.getenv("LLM_URL")
            if not llm_url:
                raise ValueError("LLM_URL must be configured for code review")

            # Set LLM_URL in environment if not already set (UnifiedModelClient reads from env)
            if not os.getenv("LLM_URL"):
                os.environ["LLM_URL"] = llm_url

            unified_client = UnifiedModelClient(
                timeout=self.settings.review_llm_timeout
            )

            # Use real client if enabled, otherwise mock
            if self.settings.external_api_enabled and self.settings.external_api_url:
                publisher = ExternalAPIClient(self.settings)
            else:
                publisher = ExternalAPIClientMock(self.settings)

            mcp_client_instance = None
            if self.settings.hw_checker_mcp_enabled:
                mcp_client_instance = MCPHTTPClient(
                    base_url=self.settings.hw_checker_mcp_url,
                )

            # Initialize log analysis components
            from src.infrastructure.logs.llm_log_analyzer import LLMLogAnalyzer
            from src.infrastructure.logs.log_normalizer import LogNormalizer
            from src.infrastructure.logs.log_parser_impl import LogParserImpl

            log_parser = LogParserImpl()
            log_normalizer = LogNormalizer()
            log_analyzer = LLMLogAnalyzer(
                unified_client=unified_client,
                timeout=self.settings.log_analysis_timeout,
                retries=self.settings.review_max_retries,
            )

            review_use_case = ReviewSubmissionUseCase(
                archive_reader=archive_service,
                diff_analyzer=diff_analyzer,
                unified_client=unified_client,
                review_repository=review_repo,
                tasks_repository=long_tasks_repo,
                publisher=publisher,
                log_parser=log_parser,
                log_normalizer=log_normalizer,
                log_analyzer=log_analyzer,
                settings=self.settings,
                mcp_client=mcp_client_instance,
                fallback_publisher=publisher,
            )

            try:
                session_id = await review_use_case.execute(task)
                duration = time.time() - start_time
                long_tasks_duration.observe(duration)
                long_tasks_total.labels(status="succeeded").inc()
                record_worker_task("code_review", "success", duration)
                logger.info(
                    f"Review task completed: task_id={task.task_id}, "
                    f"session_id={session_id}, duration={duration:.2f}s"
                )
            except Exception as e:
                duration = time.time() - start_time
                long_tasks_duration.observe(duration)
                long_tasks_total.labels(status="failed").inc()
                record_worker_task("code_review", "error", duration)
                logger.error(
                    f"Review task failed: task_id={task.task_id}, error={e}",
                    exc_info=True,
                )
                raise

        except Exception as e:
            logger.error(f"Error processing review tasks: {e}", exc_info=True)

    async def _check_and_send(self) -> None:
        """Check if it's time to send notifications."""
        now = datetime.utcnow()

        # Debug mode: send every N minutes if enabled
        debug_interval = self.settings.debug_notification_interval_minutes
        if debug_interval > 0:
            should_send = False
            if self._last_debug_send is None:
                should_send = True
                logger.info(
                    f"Debug mode: first run, sending notifications immediately (interval={debug_interval} min)"
                )
            elif (now - self._last_debug_send).total_seconds() >= (debug_interval * 60):
                should_send = True
                logger.info(
                    f"Debug mode: sending notifications (interval={debug_interval} min)"
                )

            if should_send:
                await self._send_debug_notifications()
                self._last_debug_send = now
            return

        # Normal mode: respect quiet hours and scheduled times
        if is_quiet_hours(
            now, self.settings.quiet_hours_start, self.settings.quiet_hours_end
        ):
            return

        morning_time = self._parse_time(self.settings.morning_summary_time)
        evening_time = self._parse_time(self.settings.evening_digest_time)

        if morning_time and is_time_to_send(now, morning_time):
            await self._send_morning_summary()

        if evening_time and is_time_to_send(now, evening_time):
            await self._send_evening_digest()

    async def _send_morning_summary(self) -> None:
        """Send morning task summary to all users."""
        db = await get_db()
        user_ids = await db.tasks.distinct("user_id")
        logger.info(f"Sending morning summaries to {len(user_ids)} users")

        for user_id in user_ids:

            async def get_text(uid: int) -> Optional[str]:
                return await get_summary_text(
                    self.mcp, uid, timeframe="today", debug=False
                )

            await send_with_retry(self.bot, user_id, get_text, "morning summary")

    async def _send_evening_digest(self) -> None:
        """Send evening channel digest to all users."""
        db = await get_db()
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        user_ids = set(doc["user_id"] for doc in channel_docs)
        logger.info(f"Sending evening digests to {len(user_ids)} users")

        for user_id in user_ids:
            try:
                digest_texts = await get_digest_texts(self.mcp, user_id, debug=False)
                if digest_texts:
                    # Send each channel digest as a separate message
                    for digest_text in digest_texts:
                        if digest_text:
                            await send_with_retry(
                                self.bot, user_id, digest_text, "evening digest"
                            )
                            # Small delay between messages to avoid rate limiting
                            await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(
                    f"Error sending evening digests for user {user_id}: {e}",
                    exc_info=True,
                )

    async def _send_debug_notifications(self) -> None:
        """Send debug notifications (summary + digest) to all users.

        Sends both task summary and channel digest for the last 24 hours.
        """
        db = await get_db()
        task_user_ids = await db.tasks.distinct("user_id")
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        channel_user_ids = set(doc["user_id"] for doc in channel_docs)
        user_ids = set(task_user_ids) | channel_user_ids

        logger.info(
            f"Debug mode: sending notifications to {len(user_ids)} users "
            f"(tasks: {len(task_user_ids)}, channels: {len(channel_user_ids)})"
        )

        summary_count = 0
        digest_count = 0

        for user_id in user_ids:
            logger.info(
                f"Processing user {user_id} (has_tasks={user_id in task_user_ids}, "
                f"has_channels={user_id in channel_user_ids})"
            )

            # Send task summary for last 24 hours
            if user_id in task_user_ids:
                logger.info(f"Sending debug summary for user {user_id}")
                try:
                    text = await get_summary_text(
                        self.mcp, user_id, timeframe="last_24h", debug=True
                    )
                    logger.info(
                        f"Got summary text for user {user_id}: "
                        f"length={len(text) if text else 0}, has_text={text is not None}"
                    )
                    if text:
                        await send_with_retry(self.bot, user_id, text, "debug summary")
                        summary_count += 1
                    else:
                        logger.warning(
                            f"No summary text to send for user {user_id}, skipping"
                        )
                except Exception as e:
                    logger.error(
                        f"Error getting summary text for user {user_id}: {e}",
                        exc_info=True,
                    )

            # Send channel digests - one message per channel
            if user_id in channel_user_ids:
                logger.info(f"Sending debug digests for user {user_id}")
                try:
                    digest_texts = await get_digest_texts(self.mcp, user_id, debug=True)
                    logger.info(
                        f"Got {len(digest_texts)} digest texts for user {user_id}"
                    )
                    if digest_texts:
                        for digest_text in digest_texts:
                            if digest_text:
                                await send_with_retry(
                                    self.bot, user_id, digest_text, "debug digest"
                                )
                                digest_count += 1
                                await asyncio.sleep(0.5)
                    else:
                        logger.warning(
                            f"No digest texts to send for user {user_id}, skipping"
                        )
                except Exception as e:
                    logger.error(
                        f"Error getting digest texts for user {user_id}: {e}",
                        exc_info=True,
                    )

        logger.info(
            f"Debug notifications sent: {summary_count} summaries, {digest_count} digests"
        )

    @staticmethod
    def _parse_time(time_str: str) -> Optional[time]:
        """Parse HH:MM string to time object.

        Args:
            time_str: Time string in HH:MM format

        Returns:
            time object or None if parsing fails
        """
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except Exception:
            return None


async def send_with_retry(
    bot: Bot,
    user_id: int,
    get_text_fn_or_str: Union[str, Callable[..., Any]],
    notification_type: str,
) -> None:
    """Send message with exponential backoff retry."""
    delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RETRIES):
        text: Optional[str] = None
        try:
            text = await _resolve_text(get_text_fn_or_str, user_id)
            if not text:
                logger.warning(
                    "No text to send, skipping",
                    user_id=user_id,
                    type=notification_type,
                )
                return

            is_digest = "digest" in notification_type.lower()
            if is_digest:
                original_length = len(text)
                text = clean_markdown(text)
                logger.info(
                    "Cleaned digest text",
                    user_id=user_id,
                    original_length=original_length,
                    cleaned_length=len(text),
                )

            logger.info(
                "Attempting to send message",
                user_id=user_id,
                type=notification_type,
                text_preview=text[:150] if text else None,
                is_digest=is_digest,
                text_length=len(text),
            )

            if len(text) > SAFE_MESSAGE_LIMIT:
                logger.warning(
                    "Message too long, truncating",
                    user_id=user_id,
                    type=notification_type,
                    length=len(text),
                )
                text = text[:3950] + "\n...message truncated..."

            use_markdown = not is_digest and notification_type != "debug summary"
            await _send_message_safe(bot, user_id, text, use_markdown, notification_type)

            log_message = (
                "Successfully sent after retry"
                if attempt > 0
                else "Successfully sent notification"
            )
            logger.info(log_message, user_id=user_id, type=notification_type)
            return

        except TelegramBadRequest as error:
            if not await _handle_telegram_error(
                bot, user_id, text or "", error, notification_type, attempt
            ):
                return
        except (TelegramNetworkError, ConnectionError, TimeoutError) as error:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "Network error, retrying",
                    user_id=user_id,
                    type=notification_type,
                    attempt=attempt + 1,
                    error=str(error),
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logger.error(
                    "Failed after all retries",
                    user_id=user_id,
                    type=notification_type,
                    attempts=MAX_RETRIES,
                    error=str(error),
                )
                raise
        except Exception as error:
            logger.error(
                "Unexpected error sending notification",
                user_id=user_id,
                type=notification_type,
                error=str(error),
            )
            return


async def _resolve_text(
    get_text_fn_or_str: Union[str, Callable[..., Any]], user_id: int
) -> Optional[str]:
    """Resolve text from string or callable."""
    if isinstance(get_text_fn_or_str, str):
        return get_text_fn_or_str

    if not callable(get_text_fn_or_str):
        return str(get_text_fn_or_str) if get_text_fn_or_str else None

    if inspect.iscoroutinefunction(get_text_fn_or_str):
        return await get_text_fn_or_str(user_id)

    result = get_text_fn_or_str(user_id)
    if inspect.iscoroutine(result):
        return await result

    return result


async def _send_message_safe(
    bot: Bot,
    user_id: int,
    text: str,
    use_markdown: bool,
    notification_type: str,
) -> None:
    """Send message with Markdown error handling."""
    try:
        if use_markdown:
            await bot.send_message(user_id, text, parse_mode="Markdown")
        else:
            await bot.send_message(user_id, text, parse_mode=None)
    except TelegramBadRequest as error:
        if _is_markdown_parse_error(str(error)):
            logger.warning(
                "Markdown parse error, retrying without formatting",
                user_id=user_id,
                type=notification_type,
                error=str(error),
            )
            await bot.send_message(user_id, _normalize_text(text), parse_mode=None)
        else:
            raise


def _is_markdown_parse_error(error_msg: str) -> bool:
    """Check if error is a Markdown parse error."""
    lowered = error_msg.lower()
    return "can't parse entities" in lowered or (
        "parse" in lowered and "entity" in lowered
    )


def _normalize_text(text: str) -> str:
    """Normalize text by removing Markdown and cleaning."""
    return clean_markdown(text)


async def _handle_telegram_error(
    bot: Bot,
    user_id: int,
    text: str,
    error: TelegramBadRequest,
    notification_type: str,
    attempt: int,
) -> bool:
    """Handle Telegram errors and decide if retry is needed."""
    error_msg = str(error)

    if _is_markdown_parse_error(error_msg):
        logger.warning(
            "Markdown parse error in outer handler, trying plain text fallback",
            user_id=user_id,
            type=notification_type,
            error=error_msg,
            attempt=attempt,
        )
        try:
            await bot.send_message(user_id, _normalize_text(text), parse_mode=None)
            logger.info(
                "Successfully sent as plain text after Markdown error (outer handler)",
                user_id=user_id,
                type=notification_type,
            )
            return False
        except Exception as plain_err:
            logger.error(
                "Failed to send plain text fallback in outer handler",
                user_id=user_id,
                type=notification_type,
                error=str(plain_err),
            )

    logger.warning(
        "Cannot send to user", user_id=user_id, type=notification_type, error=error_msg
    )

    if "chat not found" in error_msg.lower() or "blocked" in error_msg.lower():
        return False

    return True
