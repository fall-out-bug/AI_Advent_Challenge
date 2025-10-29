"""Background worker for scheduled summaries and digests."""

from __future__ import annotations

import asyncio
import signal
from datetime import datetime, timedelta, time
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.monitoring.logger import get_logger
from src.presentation.mcp.client import get_mcp_client
from src.workers.schedulers import is_quiet_hours, is_time_to_send

logger = get_logger(name="summary_worker")

# Constants
CHECK_INTERVAL_SECONDS = 60
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds


class SummaryWorker:
    """Background worker for scheduled notifications.

    Purpose:
        Send morning summaries and evening digests at configured times,
        respecting quiet hours.
    """

    def __init__(self, bot_token: str, mcp_url: Optional[str] = None) -> None:
        """Initialize worker.

        Args:
            bot_token: Telegram bot token
            mcp_url: Optional MCP server URL (defaults to stdio)
        """
        self.bot = Bot(token=bot_token)
        import os
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
                    logger.error("Worker error in main loop", error=str(e), exc_info=True)
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
                # First run: send immediately
                should_send = True
                logger.info("Debug mode: first run, sending notifications immediately", interval_minutes=debug_interval)
            elif (now - self._last_debug_send).total_seconds() >= (debug_interval * 60):
                # Interval elapsed: send now
                should_send = True
                logger.info("Debug mode: sending notifications", interval_minutes=debug_interval)
            
            if should_send:
                await self._send_debug_notifications()
                self._last_debug_send = now
            return
        
        # Normal mode: respect quiet hours and scheduled times
        if is_quiet_hours(now, self.settings.quiet_hours_start, self.settings.quiet_hours_end):
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
            await self._send_with_retry(
                user_id,
                self._get_summary_text,
                "morning summary"
            )

    async def _send_evening_digest(self) -> None:
        """Send evening channel digest to all users."""
        db = await get_db()
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        user_ids = set(doc["user_id"] for doc in channel_docs)
        logger.info("Sending evening digests", user_count=len(user_ids))

        for user_id in user_ids:
            try:
                digest_texts = await self._get_digest_texts(user_id, debug=False)
                if digest_texts:
                    # Send each channel digest as a separate message
                    for digest_text in digest_texts:
                        if digest_text:
                            await self._send_with_retry(
                                user_id,
                                digest_text,
                                "evening digest"
                            )
                            # Small delay between messages to avoid rate limiting
                            await asyncio.sleep(0.5)
            except Exception as e:
                logger.error("Error sending evening digests", user_id=user_id, error=str(e), exc_info=True)

    async def _send_debug_notifications(self) -> None:
        """Send debug notifications (summary + digest) to all users.
        
        Sends both task summary and channel digest for the last 24 hours.
        """
        db = await get_db()
        # Get all users with tasks
        task_user_ids = await db.tasks.distinct("user_id")
        # Get all users with channels
        channel_docs = await db.channels.find({"active": True}).to_list(length=None)
        channel_user_ids = set(doc["user_id"] for doc in channel_docs)
        # Combine unique user IDs
        user_ids = set(task_user_ids) | channel_user_ids
        
        logger.info("Debug mode: sending notifications", 
                   user_count=len(user_ids),
                   users_with_tasks=len(task_user_ids),
                   users_with_channels=len(channel_user_ids))
        
        summary_count = 0
        digest_count = 0
        
        for user_id in user_ids:
            logger.info("Processing user", user_id=user_id, has_tasks=user_id in task_user_ids, has_channels=user_id in channel_user_ids)
            # Send task summary for last 24 hours
            if user_id in task_user_ids:
                logger.info("Sending debug summary", user_id=user_id)
                try:
                    # Get text once and reuse it to avoid double-calling
                    text = await self._get_summary_text(user_id, timeframe="last_24h", debug=True)
                    logger.info("Got summary text", user_id=user_id, text_length=len(text) if text else 0, has_text=text is not None)
                    if text:
                        # Send the already-retrieved text directly (as string, not lambda)
                        await self._send_with_retry(
                            user_id,
                            text,  # Pass string directly
                            "debug summary"
                        )
                        summary_count += 1
                    else:
                        logger.warning("No summary text to send, skipping", user_id=user_id)
                except Exception as e:
                    logger.error("Error getting summary text", user_id=user_id, error=str(e), exc_info=True)
            
            # Send channel digests - one message per channel
            if user_id in channel_user_ids:
                logger.info("Sending debug digests", user_id=user_id)
                try:
                    digest_texts = await self._get_digest_texts(user_id, debug=True)
                    logger.info("Got digest texts", user_id=user_id, digest_count=len(digest_texts))
                    if digest_texts:
                        # Send each channel digest as a separate message
                        for digest_text in digest_texts:
                            if digest_text:
                                await self._send_with_retry(
                                    user_id,
                                    digest_text,
                                    "debug digest"
                                )
                                digest_count += 1
                                # Small delay between messages to avoid rate limiting
                                await asyncio.sleep(0.5)
                    else:
                        logger.warning("No digest texts to send, skipping", user_id=user_id)
                except Exception as e:
                    logger.error("Error getting digest texts", user_id=user_id, error=str(e), exc_info=True)
        
        logger.info("Debug notifications sent", 
                   summaries_sent=summary_count,
                   digests_sent=digest_count)

    async def _get_summary_text(self, user_id: int, timeframe: str = "today", debug: bool = False) -> Optional[str]:
        """Get summary text for user.
        
        Args:
            user_id: User ID
            timeframe: Timeframe for summary ("today", "week", "last_24h")
            debug: If True, use debug formatting
        """
        try:
            logger.info("_get_summary_text called", user_id=user_id, timeframe=timeframe, debug=debug, debug_type=type(debug))
            
            # In debug mode, ALWAYS query DB directly, skip MCP completely
            if debug:
                logger.info("🔧 DEBUG MODE: Querying DB directly, skipping MCP", user_id=user_id)
                try:
                    db = await get_db()
                    user_id_int = int(user_id)
                    logger.info("🔧 Executing DB query", user_id=user_id_int)
                    raw = await db.tasks.find({"user_id": user_id_int}).to_list(length=200)
                    logger.info("🔧 DB returned raw tasks", user_id=user_id, raw_count=len(raw))
                    
                    tasks_filtered = [t for t in raw if not t.get("completed", False)]
                    logger.info("🔧 After filter (completed=False)", user_id=user_id, filtered_count=len(tasks_filtered))
                    
                    # Normalize for formatter (id field)
                    normalized = []
                    for t in tasks_filtered:
                        td = dict(t)
                        if "_id" in td:
                            td["id"] = str(td.pop("_id"))
                        normalized.append(td)
                        logger.info("🔧 Normalized task", user_id=user_id, task_title=td.get("title", "No title")[:50])
                    
                    tasks = normalized
                    stats = {
                        "total": len(tasks),
                        "completed": 0,
                        "overdue": 0,
                        "high_priority": sum(1 for t in tasks if t.get("priority") == "high"),
                    }
                    logger.info("🔧 Final tasks and stats", user_id=user_id, task_count=len(tasks), stats=stats)
                    
                    result = self._format_summary(tasks, stats, debug=True)
                    logger.info("🔧 Formatted summary result", user_id=user_id, result_length=len(result) if result else 0)
                    return result
                except Exception as db_err:
                    logger.error("🔧 Debug DB query failed", user_id=user_id, error=str(db_err), exc_info=True)
                    import traceback
                    logger.error("🔧 Debug DB traceback", user_id=user_id, traceback=traceback.format_exc())
                    return f"🔍 *Debug Summary Error*\n\nDB query failed: {str(db_err)}\n\n_Это тестовое сообщение для отладки._"
            
            # Normal mode: use MCP
            logger.info("Calling get_summary tool", user_id=user_id, timeframe=timeframe)
            summary = await self.mcp.call_tool("get_summary", {"user_id": user_id, "timeframe": timeframe})
            tasks = summary.get("tasks", [])
            stats = summary.get("stats", {})
            logger.info("Got summary from MCP", user_id=user_id, task_count=len(tasks), stats=stats)

            result = self._format_summary(tasks, stats, debug=debug)
            logger.info("Formatted summary", user_id=user_id, result_length=len(result) if result else 0, has_result=result is not None)
            return result
        except Exception as e:
            logger.error("Error getting summary text", user_id=user_id, error=str(e), exc_info=True)
            if debug:
                # In debug mode, return placeholder even on error
                return f"🔍 *Debug Summary Error*\n\nError retrieving summary: {str(e)}\n\n_Это тестовое сообщение для отладки._"
            return None

    async def _get_digest_texts(self, user_id: int, debug: bool = False) -> list[str]:
        """Get digest texts for user - one per channel.
        
        Args:
            user_id: User ID
            debug: If True, use debug formatting and extended time window
            
        Returns:
            List of digest text messages, one per channel
        """
        try:
            # In debug mode, use extended time window (7 days) to ensure we find posts
            hours = 168 if debug else 24  # 7 days for debug, 24 hours for normal
            logger.info("Calling get_channel_digest tool", user_id=user_id, hours=hours)
            digest_data = await self.mcp.call_tool("get_channel_digest", {"user_id": user_id, "hours": hours})
            digests = digest_data.get("digests", [])
            logger.info("Got digest from MCP", user_id=user_id, digest_count=len(digests))
            if not digests:
                if debug:
                    # In debug mode, send message even if no digests
                    return [f"📰 Debug Digest (Last {hours//24} days):\n\n📌 No new posts in subscribed channels.\n\nЭто тестовое сообщение для отладки."]
                return []
            # Format each channel as a separate message
            results = []
            for digest in digests:
                formatted = self._format_single_digest(digest, debug=debug)
                if formatted:
                    results.append(formatted)
            logger.info("Formatted digest texts", user_id=user_id, message_count=len(results))
            return results
        except Exception as e:
            logger.error("Error getting digest texts", user_id=user_id, error=str(e), exc_info=True)
            if debug:
                # In debug mode, return placeholder even on error
                return [f"📰 Debug Digest Error\n\nError retrieving digest: {str(e)}\n\nЭто тестовое сообщение для отладки."]
            return []
    
    async def _get_digest_text(self, user_id: int, debug: bool = False) -> Optional[str]:
        """Get single combined digest text for user (legacy method, kept for compatibility).
        
        Args:
            user_id: User ID
            debug: If True, use debug formatting and extended time window
        """
        texts = await self._get_digest_texts(user_id, debug=debug)
        if not texts:
            return None
        # Combine all texts with separator
        return "\n\n---\n\n".join(texts)

    async def _send_with_retry(
        self,
        user_id: int,
        get_text_fn_or_str,
        notification_type: str
    ) -> None:
        """Send message with exponential backoff retry.

        Args:
            user_id: Target user ID
            get_text_fn: Async function that returns message text or None
            notification_type: Type of notification for logging
        """
        delay = INITIAL_RETRY_DELAY
        
        for attempt in range(MAX_RETRIES):
            try:
                # Handle both async function and string
                if isinstance(get_text_fn_or_str, str):
                    text = get_text_fn_or_str
                elif callable(get_text_fn_or_str):
                    # Check if it's a coroutine function (needs await) or regular function
                    import inspect
                    if inspect.iscoroutinefunction(get_text_fn_or_str):
                        text = await get_text_fn_or_str(user_id)
                    else:
                        # It's a regular function, but might return coroutine
                        result = get_text_fn_or_str(user_id)
                        if inspect.iscoroutine(result):
                            text = await result
                        else:
                            text = result
                else:
                    text = str(get_text_fn_or_str) if get_text_fn_or_str else None
                
                if not text:
                    logger.warning("No text to send, skipping", user_id=user_id, type=notification_type)
                    return  # Skip if no content
                
                # Check if this is a digest (always plain text)
                is_digest = "digest" in notification_type.lower()
                
                # For digests: AGGRESSIVE cleanup - remove ALL Markdown BEFORE logging preview
                if is_digest:
                    import re
                    # Store original for debugging
                    original_length = len(text)
                    
                    # Remove all Markdown characters multiple times to catch nested/escaped ones
                    # First pass: remove standard Markdown chars
                    text = re.sub(r'[*_`]', '', text)
                    text = re.sub(r'\[', '', text)
                    text = re.sub(r'\]', '', text)
                    text = re.sub(r'\(', '', text)
                    text = re.sub(r'\)', '', text)
                    text = re.sub(r'\\', '', text)  # Remove backslashes
                    
                    # Second pass: remove any remaining patterns
                    text = re.sub(r'\*+', '', text)  # Remove any asterisks (single or multiple)
                    text = re.sub(r'_+', '', text)   # Remove any underscores
                    text = re.sub(r'`+', '', text)   # Remove any backticks
                    
                    # Remove escaped characters explicitly
                    text = text.replace('\\*', '').replace('\\_', '').replace('\\`', '').replace('\\[', '').replace('\\]', '')
                    
                    # Preserve newlines for readability, but clean them
                    text = re.sub(r'\n\n+', '\n\n', text)  # Max 2 newlines
                    text = text.strip()
                    
                    logger.info("Cleaned digest text", user_id=user_id, original_length=original_length, cleaned_length=len(text), has_markdown=('*' in text or '_' in text or '[' in text))
                
                logger.info("Attempting to send message", user_id=user_id, type=notification_type, text_preview=text[:150] if text else None, is_digest=is_digest, text_length=len(text) if text else 0)
                
                # Check message length (Telegram limit is 4096 chars)
                if len(text) > 4000:
                    logger.warning("Message too long, truncating", user_id=user_id, type=notification_type, length=len(text))
                    text = text[:3950] + "\n...message truncated..."
                
                # For digests, always send without Markdown to avoid parsing errors
                # For summaries, try Markdown first, fallback to plain text
                sent_successfully = False
                md_parse_error = False
                
                use_markdown = not is_digest and notification_type != "debug summary"
                
                try:
                    if use_markdown:
                        await self.bot.send_message(user_id, text, parse_mode="Markdown")
                    else:
                        # Digests and debug summaries - send without Markdown (parse_mode=None is explicit)
                        await self.bot.send_message(user_id, text, parse_mode=None)
                    sent_successfully = True
                except TelegramBadRequest as md_error:
                    error_msg = str(md_error)
                    # Check if this is a Markdown parse error
                    if "can't parse entities" in error_msg.lower() or "parse" in error_msg.lower() or "entity" in error_msg.lower():
                        md_parse_error = True
                        logger.warning("Markdown parse error, retrying without formatting", user_id=user_id, type=notification_type, error=error_msg)
                        # Remove ALL Markdown formatting characters and retry
                        # Also normalize quotes and clean up
                        import re
                        plain_text = text
                        # Remove Markdown
                        plain_text = re.sub(r'[*_`\[\]()]', '', plain_text)
                        # Normalize quotes
                        plain_text = plain_text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
                        # Clean extra whitespace
                        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
                        
                        # Try sending as plain text
                        try:
                            await self.bot.send_message(user_id, plain_text, parse_mode=None)
                            sent_successfully = True
                            logger.info("Successfully sent as plain text after Markdown error", user_id=user_id, type=notification_type)
                        except Exception as plain_error:
                            logger.error("Failed to send plain text as well", user_id=user_id, type=notification_type, error=str(plain_error))
                            # Still raise to allow outer handler to see the error
                            raise
                    else:
                        # Different TelegramBadRequest error (e.g., chat not found), re-raise it
                        raise
                except Exception as other_error:
                    # Any other exception - log and re-raise
                    logger.error("Unexpected error sending message", user_id=user_id, type=notification_type, error=str(other_error))
                    raise
                
                if sent_successfully:
                    if attempt > 0:
                        logger.info("Successfully sent after retry", 
                                  user_id=user_id, 
                                  type=notification_type,
                                  attempt=attempt + 1)
                    else:
                        logger.info("Successfully sent notification",
                                  user_id=user_id,
                                  type=notification_type)
                    return
                else:
                    # If we got here and not sent, something went wrong
                    if md_parse_error:
                        # If Markdown parse error occurred but plain text also failed, try one more time in outer handler
                        raise TelegramBadRequest("Markdown parse error - plain text fallback also failed")
                    raise RuntimeError("Message not sent but no exception raised")
                    
            except TelegramBadRequest as e:
                error_msg = str(e)
                # Check if this is a Markdown parse error that we should retry without formatting
                if "can't parse entities" in error_msg.lower() or ("parse" in error_msg.lower() and "entity" in error_msg.lower()):
                    # Try plain text fallback one more time in outer handler
                    logger.warning("Markdown parse error in outer handler, trying plain text fallback", user_id=user_id, type=notification_type, error=error_msg, attempt=attempt)
                    import re
                    plain_text = re.sub(r'[*_`\[\]()]', '', text)
                    plain_text = plain_text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
                    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
                    try:
                        await self.bot.send_message(user_id, plain_text, parse_mode=None)
                        logger.info("Successfully sent as plain text after Markdown error (outer handler)", user_id=user_id, type=notification_type)
                        return
                    except Exception as plain_err:
                        logger.error("Failed to send plain text fallback in outer handler", user_id=user_id, type=notification_type, error=str(plain_err))
                        # Continue to normal error handling below
                
                logger.warning("Cannot send to user", 
                             user_id=user_id, 
                             type=notification_type, 
                             error=error_msg)
                
                # Don't retry on permanent errors (chat not found, etc.) unless it's parse error
                if "chat not found" in error_msg.lower() or "blocked" in error_msg.lower():
                    return  # Don't retry on permanent errors
            except (TelegramNetworkError, ConnectionError, TimeoutError) as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning("Network error, retrying",
                                 user_id=user_id,
                                 type=notification_type,
                                 attempt=attempt + 1,
                                 error=str(e))
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed after all retries",
                               user_id=user_id,
                               type=notification_type,
                               attempts=MAX_RETRIES,
                               error=str(e))
            except Exception as e:
                logger.error("Unexpected error sending notification",
                           user_id=user_id,
                           type=notification_type,
                           error=str(e))
                return  # Don't retry on unexpected errors

    @staticmethod
    def _parse_time(time_str: str) -> Optional[time]:
        """Parse HH:MM string to time object."""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except Exception:
            return None

    @staticmethod
    def _format_summary(tasks: list, stats: dict, debug: bool = False) -> str:
        """Format task summary message.
        
        Args:
            tasks: List of tasks
            stats: Statistics dict
            debug: If True, use debug header instead of morning greeting
        """
        # Log what we receive
        logger.info("_format_summary called", tasks_count=len(tasks) if tasks else 0, stats_total=stats.get('total', 0), debug=debug)
        
        if not tasks or len(tasks) == 0:
            if debug:
                return f"🔍 *Debug Summary (Last 24h)*\n\n📊 No active tasks found (checked {stats.get('total', 0)} tasks).\n\n_Это тестовое сообщение для отладки._"
            header = "🌅 *Good morning!*\n\n"
            return f"{header}No tasks found. Enjoy your day!"
        
        header = "🔍 *Debug Summary (Last 24h)*\n\n" if debug else "🌅 *Good morning!*\n\n"
        text = f"{header}📊 Tasks: {stats.get('total', 0)}\n"
        if stats.get("high_priority", 0) > 0:
            text += f"🔴 High priority: {stats['high_priority']}\n"
        text += "\n*Your tasks:*\n\n"
        for task in tasks[:5]:
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
            text += f"{emoji} {task.get('title', 'Untitled')}\n"
        if len(tasks) > 5:
            text += f"\n_...and {len(tasks) - 5} more_"
        return text

    @staticmethod
    def _format_single_digest(digest: dict, debug: bool = False) -> str:
        """Format single channel digest message with Russian localization.
        
        Returns a detailed, longer summary for one channel.
        
        Note: Returns text WITHOUT any Markdown formatting to avoid parsing errors.
        All Markdown characters are removed to ensure safe plain-text sending.
        
        Args:
            digest: Single digest dict with channel, summary, post_count, tags
            debug: If True, use debug header
        """
        from src.infrastructure.config.settings import get_settings
        settings = get_settings()
        import re
        
        channel = digest.get("channel", "unknown")
        summary = digest.get("summary", "")
        post_count = digest.get("post_count", 0)
        tags = digest.get("tags", [])
        
        # Aggressively clean summary - remove ALL Markdown characters
        summary_clean = re.sub(r'[*_`\[\]()\\]', '', summary)  # Remove Markdown chars
        summary_clean = re.sub(r'\*+', '', summary_clean)  # Remove any asterisks
        summary_clean = re.sub(r'_+', '', summary_clean)   # Remove any underscores
        summary_clean = summary_clean.strip()
        
        # Enforce max_chars from settings - Telegram message limit is 4096, use 2000 for safety
        max_chars = settings.digest_summary_max_chars
        # Additional safety: never exceed 2500 chars (more than half of Telegram limit)
        absolute_max = min(max_chars, 2500)
        
        if len(summary_clean) > absolute_max:
            # Try to truncate at sentence boundary
            truncated = summary_clean[:absolute_max]
            last_period = truncated.rfind('.')
            if last_period > absolute_max * 0.7:  # If period is in last 30%, use it
                summary_clean = truncated[:last_period + 1]
            else:
                summary_clean = truncated + "..."
                logger.warning("Summary truncated at hard limit", original_length=len(summary), truncated_length=len(summary_clean))
        
        # Format with tags if available (no Markdown)
        tags_str = ""
        if tags:
            tags_str = f"\nТеги: {', '.join(f'#{tag}' for tag in tags[:5])}"
        
        # Build detailed message
        header = "📰 Дайджест канала\n\n" if not debug else "📰 Debug Digest (Last 7 days)\n\n"
        text = f"{header}"
        text += f"📌 {channel}\n"
        text += f"📊 Постов: {post_count}"
        if tags_str:
            text += tags_str
        text += f"\n\n{summary_clean}\n"
        
        if debug:
            text += "\nЭто тестовое сообщение для отладки."
        
        # Final safety check - remove any Markdown that might have slipped through
        text = re.sub(r'[*_`\[\]()\\]', '', text)
        
        return text
    
    @staticmethod
    def _format_digest(digests: list, debug: bool = False) -> str:
        """Format channel digest message with Russian localization (legacy method).
        
        Note: Returns text WITHOUT any Markdown formatting to avoid parsing errors.
        All Markdown characters are removed to ensure safe plain-text sending.
        
        Args:
            digests: List of digest dicts
            debug: If True, use debug header
        """
        from src.infrastructure.config.settings import get_settings
        settings = get_settings()
        
        header = "📰 Debug Digest (Last 7 days)\n\n" if debug else "📰 Дайджест каналов\n\n"
        text = header
        
        # Use configurable max channels
        max_channels = settings.digest_max_channels
        max_chars = settings.digest_summary_max_chars
        
        # Sort by post_count descending (most active first)
        sorted_digests = sorted(digests, key=lambda x: x.get("post_count", 0), reverse=True)[:max_channels]
        
        for digest in sorted_digests:
            channel = digest.get("channel", "unknown")
            summary = digest.get("summary", "")
            post_count = digest.get("post_count", 0)
            tags = digest.get("tags", [])
            
            # Aggressively clean summary - remove ALL Markdown characters
            import re
            summary_clean = re.sub(r'[*_`\[\]()\\]', '', summary)  # Remove Markdown chars
            summary_clean = re.sub(r'\*+', '', summary_clean)  # Remove any asterisks
            summary_clean = re.sub(r'_+', '', summary_clean)   # Remove any underscores
            summary_clean = summary_clean.strip()
            
            # Truncate if too long
            if len(summary_clean) > max_chars:
                summary_clean = summary_clean[:max_chars - 3] + "..."
            
            # Format with tags if available (no Markdown)
            tags_str = ""
            if tags:
                tags_str = f" {', '.join(f'#{tag}' for tag in tags[:3])}"
            
            text += f"📌 {channel} ({post_count} постов{tags_str})\n{summary_clean}\n\n"
        
        if len(digests) > max_channels:
            remaining = len(digests) - max_channels
            text += f"...и еще {remaining} каналов\n\n"
        
        if debug and len(digests) > 0:
            text += "\nЭто тестовое сообщение для отладки."
        
        # Final safety check - remove any Markdown that might have slipped through
        text = re.sub(r'[*_`\[\]()\\]', '', text)
        
        return text

