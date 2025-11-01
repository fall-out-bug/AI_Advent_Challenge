"""Background worker for scheduled summaries and digests."""

from __future__ import annotations

import asyncio
import os
import signal
from datetime import datetime, time
from typing import Optional

from aiogram import Bot

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.presentation.mcp.client import get_mcp_client
from src.workers.data_fetchers import get_digest_texts, get_summary_text
from src.workers.message_sender import send_with_retry
from src.workers.schedulers import is_quiet_hours, is_time_to_send

logger = get_logger("summary_worker")

# Constants
CHECK_INTERVAL_SECONDS = 60


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
        logger.info("Worker settings loaded",
                   debug_interval=self.settings.debug_notification_interval_minutes,
                   morning_time=self.settings.morning_summary_time,
                   evening_time=self.settings.evening_digest_time)
        self._running = False
        self._last_debug_send: Optional[datetime] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self) -> None:
        """Main worker loop."""
        self._running = True
        logger.info("Summary worker started")
        try:
            while self._running:
                try:
                    await self._check_and_send()
                    await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                except Exception as e:
                    logger.error("Worker error in main loop", 
                               error=str(e), 
                               exc_info=True)
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

    async def _check_and_send(self) -> None:
        """Check if it's time to send notifications."""
        now = datetime.utcnow()

        # Debug mode: send every N minutes if enabled
        debug_interval = self.settings.debug_notification_interval_minutes
        if debug_interval > 0:
            should_send = False
            if self._last_debug_send is None:
                should_send = True
                logger.info("Debug mode: first run, sending notifications immediately", 
                          interval_minutes=debug_interval)
            elif (now - self._last_debug_send).total_seconds() >= (debug_interval * 60):
                should_send = True
                logger.info("Debug mode: sending notifications", 
                          interval_minutes=debug_interval)

            if should_send:
                await self._send_debug_notifications()
                self._last_debug_send = now
            return

        # Normal mode: respect quiet hours and scheduled times
        if is_quiet_hours(now, 
                         self.settings.quiet_hours_start, 
                         self.settings.quiet_hours_end):
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
        logger.info("Sending morning summaries", user_count=len(user_ids))

        for user_id in user_ids:
            async def get_text(uid: int) -> Optional[str]:
                return await get_summary_text(self.mcp, uid, timeframe="today", debug=False)

            await send_with_retry(self.bot, user_id, get_text, "morning summary")

    async def _send_evening_digest(self) -> None:
        """Send evening channel digest to all users."""
        db = await get_db()
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        user_ids = set(doc["user_id"] for doc in channel_docs)
        logger.info("Sending evening digests", user_count=len(user_ids))

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
                logger.error("Error sending evening digests", 
                           user_id=user_id, 
                           error=str(e), 
                           exc_info=True)

    async def _send_debug_notifications(self) -> None:
        """Send debug notifications (summary + digest) to all users.

        Sends both task summary and channel digest for the last 24 hours.
        """
        db = await get_db()
        task_user_ids = await db.tasks.distinct("user_id")
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        channel_user_ids = set(doc["user_id"] for doc in channel_docs)
        user_ids = set(task_user_ids) | channel_user_ids

        logger.info("Debug mode: sending notifications",
                   user_count=len(user_ids),
                   users_with_tasks=len(task_user_ids),
                   users_with_channels=len(channel_user_ids))

        summary_count = 0
        digest_count = 0

        for user_id in user_ids:
            logger.info("Processing user", 
                       user_id=user_id, 
                       has_tasks=user_id in task_user_ids, 
                       has_channels=user_id in channel_user_ids)

            # Send task summary for last 24 hours
            if user_id in task_user_ids:
                logger.info("Sending debug summary", user_id=user_id)
                try:
                    text = await get_summary_text(
                        self.mcp, user_id, timeframe="last_24h", debug=True
                    )
                    logger.info("Got summary text", 
                               user_id=user_id, 
                               text_length=len(text) if text else 0, 
                               has_text=text is not None)
                    if text:
                        await send_with_retry(
                            self.bot, user_id, text, "debug summary"
                        )
                        summary_count += 1
                    else:
                        logger.warning("No summary text to send, skipping", 
                                     user_id=user_id)
                except Exception as e:
                    logger.error("Error getting summary text", 
                               user_id=user_id, 
                               error=str(e), 
                               exc_info=True)

            # Send channel digests - one message per channel
            if user_id in channel_user_ids:
                logger.info("Sending debug digests", user_id=user_id)
                try:
                    digest_texts = await get_digest_texts(self.mcp, user_id, debug=True)
                    logger.info("Got digest texts", 
                               user_id=user_id, 
                               digest_count=len(digest_texts))
                    if digest_texts:
                        for digest_text in digest_texts:
                            if digest_text:
                                await send_with_retry(
                                    self.bot, user_id, digest_text, "debug digest"
                                )
                                digest_count += 1
                                await asyncio.sleep(0.5)
                    else:
                        logger.warning("No digest texts to send, skipping", 
                                     user_id=user_id)
                except Exception as e:
                    logger.error("Error getting digest texts", 
                               user_id=user_id, 
                               error=str(e), 
                               exc_info=True)

        logger.info("Debug notifications sent",
                   summaries_sent=summary_count,
                   digests_sent=digest_count)

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
