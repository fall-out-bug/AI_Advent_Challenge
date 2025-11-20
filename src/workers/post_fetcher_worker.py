"""Background worker for hourly post collection from Telegram channels.

Purpose:
    Collect posts from all subscribed channels hourly and save them to MongoDB.
    Uses hybrid deduplication to prevent duplicates.
"""

from __future__ import annotations

import asyncio
import os
import signal
import time
from datetime import datetime, timedelta
from typing import Optional

from src.domain.interfaces.telegram_adapter import TelegramAdapter
from src.infrastructure.clients.telegram_adapter_impl import TelegramAdapterImpl

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.prometheus_metrics import (
    post_fetcher_channels_processed_total,
    post_fetcher_duration_seconds,
    post_fetcher_errors_total,
    post_fetcher_last_run_timestamp,
    post_fetcher_posts_saved_total,
    post_fetcher_posts_skipped_total,
    post_fetcher_worker_running,
)
from src.presentation.mcp.client import get_mcp_client

logger = get_logger("post_fetcher_worker")

# Constants
CHECK_INTERVAL_SECONDS = 60


class PostFetcherWorker:
    """Background worker for hourly post collection.

    Purpose:
        Collect posts from all subscribed channels hourly and save them to MongoDB.
        Processes channels independently, continuing on errors.
    """

    def __init__(
        self,
        mcp_url: Optional[str] = None,
        telegram_adapter: Optional[TelegramAdapter] = None,
    ) -> None:
        """Initialize worker.

        Args:
            mcp_url: Optional MCP server URL (defaults to stdio)
            telegram_adapter: Optional Telegram adapter for fetching posts.
                Defaults to TelegramAdapterImpl if not provided.
        """
        mcp_url = mcp_url or os.getenv("MCP_SERVER_URL")
        self.mcp = get_mcp_client(server_url=mcp_url)
        self.settings = get_settings()
        self.telegram_adapter = telegram_adapter or TelegramAdapterImpl()
        logger.info(
            f"Post fetcher worker initialized: interval_hours={self.settings.post_fetch_interval_hours}, "
            f"ttl_days={self.settings.post_ttl_days}"
        )
        self._running = False
        self._last_run: Optional[datetime] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received shutdown signal: signal={signum}")
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def run(self) -> None:
        """Main worker loop."""
        self._running = True
        post_fetcher_worker_running.set(1)
        logger.info("Post fetcher worker started")
        try:
            while self._running:
                try:
                    if self._should_run():
                        await self._process_all_channels()
                        self._last_run = datetime.utcnow()
                        if self._last_run:
                            post_fetcher_last_run_timestamp.set(
                                self._last_run.timestamp()
                            )
                    await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                except Exception as e:
                    logger.error(
                        "Worker error in main loop", error=str(e), exc_info=True
                    )
                    post_fetcher_errors_total.labels(error_type="main_loop").inc()
                    await asyncio.sleep(300)  # Wait 5 min on error
        finally:
            post_fetcher_worker_running.set(0)
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up post fetcher worker resources")

    def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping post fetcher worker")
        self._running = False

    def _should_run(self) -> bool:
        """Check if it's time to run post collection.

        Returns:
            True if should run now
        """
        if self._last_run is None:
            return True

        interval_seconds = self.settings.post_fetch_interval_hours * 3600
        elapsed = (datetime.utcnow() - self._last_run).total_seconds()
        return elapsed >= interval_seconds

    async def _process_all_channels(self) -> None:
        """Process all active channels.

        Purpose:
            Query MongoDB for all active channels and process each one.
            Logs statistics after completion.
        """
        start_time = time.time()
        try:
            db = await get_db()
            channels_cursor = db.channels.find({"active": True})
            channels = await channels_cursor.to_list(length=1000)

            if not channels:
                logger.info("No active channels to process")
                return

            logger.info(f"Processing channels: channel_count={len(channels)}")

            stats = {
                "channels_processed": 0,
                "channels_failed": 0,
                "total_posts_saved": 0,
                "total_posts_skipped": 0,
            }

            for channel in channels:
                try:
                    result = await self._process_channel(channel, db)
                    stats["channels_processed"] += 1
                    stats["total_posts_saved"] += result.get("saved", 0)
                    stats["total_posts_skipped"] += result.get("skipped", 0)

                    # Record metrics per channel
                    channel_username = channel.get("channel_username", "unknown")
                    post_fetcher_posts_saved_total.labels(
                        channel_username=channel_username
                    ).inc(result.get("saved", 0))
                    post_fetcher_posts_skipped_total.labels(
                        channel_username=channel_username
                    ).inc(result.get("skipped", 0))
                except Exception as e:
                    stats["channels_failed"] += 1
                    await self._handle_channel_error(channel, e)

            # Record metrics
            post_fetcher_channels_processed_total.inc(stats["channels_processed"])
            duration = time.time() - start_time
            post_fetcher_duration_seconds.observe(duration)

            logger.info(f"Channel processing completed: statistics={stats}")

        except Exception as e:
            logger.error(f"Error processing channels: error={str(e)}", exc_info=True)
            post_fetcher_errors_total.labels(error_type="process_channels").inc()

    async def _process_channel(self, channel: dict, db) -> dict[str, int]:
        """Process a single channel.

        Purpose:
            Fetch posts from channel, save to database, update last_fetch timestamp.
            Ensures channel_username is valid (not a title) by fetching metadata if needed.

        Args:
            channel: Channel document from MongoDB
            db: MongoDB database instance

        Returns:
            Dict with saved and skipped counts

        Raises:
            Exception: If channel processing fails
        """
        channel_username = channel.get("channel_username", "")
        user_id = channel.get("user_id")

        # Validate channel_username: ensure it's a valid username (not a title)
        # If channel_username looks like a title (contains Cyrillic, spaces, etc.),
        # fetch metadata to get the real username
        if not channel_username or self._looks_like_title(channel_username):
            logger.warning(
                f"Channel username looks like a title: '{channel_username}', "
                f"fetching metadata to get real username"
            )
            try:
                from src.presentation.mcp.tools.channels.channel_metadata import (
                    get_channel_metadata,
                )

                metadata = await get_channel_metadata(channel_username, user_id=user_id)
                if metadata.get("success") and metadata.get("channel_username"):
                    # Update channel document with correct username
                    correct_username = metadata["channel_username"]
                    if correct_username != channel_username:
                        await db.channels.update_one(
                            {"_id": channel["_id"]},
                            {"$set": {"channel_username": correct_username}},
                        )
                        logger.info(
                            f"Updated channel username in database: "
                            f"from '{channel_username}' to '{correct_username}'"
                        )
                        channel_username = correct_username
                        channel["channel_username"] = correct_username
                else:
                    # Metadata fetch failed or didn't return username
                    # Skip this channel to avoid errors in fetch_channel_posts
                    logger.error(
                        f"Cannot process channel with title-like username '{channel_username}': "
                        f"failed to get correct username from metadata. "
                        f"Metadata result: success={metadata.get('success')}, "
                        f"username={metadata.get('channel_username')}"
                    )
                    raise ValueError(
                        f"Channel username '{channel_username}' looks like a title "
                        f"but metadata fetch failed or returned no username. "
                        f"Please update channel_username in database manually."
                    )
            except ValueError:
                # Re-raise ValueError (our own validation error)
                raise
            except Exception as e:
                # For other exceptions, also skip the channel
                logger.error(
                    f"Failed to fetch metadata for channel '{channel_username}': {e}. "
                    f"Skipping channel to avoid errors in fetch_channel_posts."
                )
                raise ValueError(
                    f"Failed to resolve title-like username '{channel_username}': {e}"
                )

        # Determine since timestamp
        # For first fetch or if channel was never fetched, use 7 days lookback
        # For regular fetches, use configured interval (at least 24 hours)
        last_fetch = channel.get("last_fetch")

        if not last_fetch:
            # First fetch: get posts from last 7 days to ensure we don't miss anything
            lookback_hours = 7 * 24  # 168 hours (7 days)
            since = datetime.utcnow() - timedelta(hours=lookback_hours)
            logger.info(
                f"First fetch for channel {channel_username}: collecting posts from last 7 days"
            )
        else:
            # Regular fetch: use configured interval, but at least 24 hours
            lookback_hours = max(self.settings.post_fetch_interval_hours, 24)
            since = datetime.utcnow() - timedelta(hours=lookback_hours)

            try:
                if isinstance(last_fetch, str):
                    last_fetch_dt = datetime.fromisoformat(
                        last_fetch.replace("Z", "+00:00")
                    )
                else:
                    last_fetch_dt = last_fetch

                # Use last_fetch only if it's more recent than our lookback window
                # Otherwise use lookback window to ensure we get all posts
                hours_since_last_fetch = (
                    datetime.utcnow() - last_fetch_dt
                ).total_seconds() / 3600
                if hours_since_last_fetch < lookback_hours:
                    # If last fetch was recent, use it to avoid duplicates
                    # But still ensure we get at least 24 hours of posts
                    since = max(last_fetch_dt, since)
                elif hours_since_last_fetch > 7 * 24:
                    # If worker was down for more than 7 days, extend lookback to 7 days
                    # to ensure we don't miss posts
                    lookback_hours = 7 * 24
                    since = datetime.utcnow() - timedelta(hours=lookback_hours)
                    logger.warning(
                        f"Worker was down for {hours_since_last_fetch:.1f} hours, "
                        f"extending lookback to 7 days for channel {channel_username}"
                    )
            except (ValueError, AttributeError):
                # If last_fetch parsing fails, use extended lookback window (7 days)
                lookback_hours = 7 * 24
                since = datetime.utcnow() - timedelta(hours=lookback_hours)
                logger.warning(
                    f"Failed to parse last_fetch for channel {channel_username}, "
                    f"using 7-day lookback"
                )

        logger.debug(
            f"Processing channel: channel={channel_username}, user_id={user_id}, "
            f"since={since.isoformat()}"
        )

        # Fetch posts from Telegram via adapter
        posts = await self.telegram_adapter.fetch_channel_posts(
            channel_username=channel_username,
            since=since,
            user_id=user_id,
            save_to_db=True,  # Automatically save via repository
        )

        # Log if no posts found (might be normal if channel doesn't exist or has no posts)
        if not posts:
            logger.debug(
                f"No posts found for channel: channel={channel_username}, "
                f"since={since.isoformat()}"
            )

        # Save posts via MCP tool for statistics
        result = {"saved": 0, "skipped": 0}
        if posts:
            try:
                save_result = await self.mcp.call_tool(
                    "save_posts_to_db",
                    {
                        "posts": posts,
                        "channel_username": channel_username,
                        "user_id": user_id,
                    },
                )
                result["saved"] = save_result.get("saved", 0)
                result["skipped"] = save_result.get("skipped", 0)
            except Exception as e:
                logger.warning(
                    f"Failed to save posts via MCP tool: channel={channel_username}, "
                    f"error={str(e)}"
                )

        # Update last_fetch timestamp
        await db.channels.update_one(
            {"_id": channel["_id"]},
            {"$set": {"last_fetch": datetime.utcnow().isoformat()}},
        )

        logger.debug(
            f"Channel processed: channel={channel_username}, posts_fetched={len(posts)}, "
            f"saved={result['saved']}, skipped={result['skipped']}"
        )

        return result

    def _looks_like_title(self, text: str) -> bool:
        """Check if text looks like a channel title rather than username.

        Purpose:
            Detect if channel_username is actually a title (e.g., "Набока")
            instead of a username (e.g., "onaboka").

        Args:
            text: Text to check

        Returns:
            True if text looks like a title (contains Cyrillic, spaces, etc.)
        """
        if not text:
            return True

        # Usernames are typically lowercase ASCII letters, numbers, underscores
        # They don't contain spaces, Cyrillic, or special characters
        has_cyrillic = any("\u0400" <= char <= "\u04FF" for char in text)
        has_spaces = " " in text
        has_uppercase = any(c.isupper() for c in text if c.isalpha())

        # If contains Cyrillic, spaces, or uppercase (and not all uppercase), it's likely a title
        if has_cyrillic or has_spaces:
            return True

        # If has uppercase letters in the middle (not just at start), might be a title
        if has_uppercase and not (text[0].isupper() and text[1:].islower()):
            return True

        return False

    async def _handle_channel_error(self, channel: dict, error: Exception) -> None:
        """Handle error during channel processing.

        Purpose:
            Log error and continue processing other channels.

        Args:
            channel: Channel document that failed
            error: Exception that occurred
        """
        error_type = type(error).__name__
        post_fetcher_errors_total.labels(error_type=error_type).inc()
        logger.error(
            f"Error processing channel: channel={channel.get('channel_username')}, "
            f"user_id={channel.get('user_id')}, error={str(error)}",
            exc_info=True,
        )
