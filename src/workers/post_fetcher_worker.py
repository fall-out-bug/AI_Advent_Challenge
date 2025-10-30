"""Background worker for hourly post collection from Telegram channels.

Purpose:
    Collect posts from all subscribed channels hourly and save them to MongoDB.
    Uses hybrid deduplication to prevent duplicates.
"""

from __future__ import annotations

import asyncio
import os
import signal
from datetime import datetime, timedelta
from typing import Optional

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.monitoring.logger import get_logger
from src.infrastructure.clients.telegram_utils import fetch_channel_posts
from src.presentation.mcp.client import get_mcp_client

logger = get_logger(name="post_fetcher_worker")

# Constants
CHECK_INTERVAL_SECONDS = 60


class PostFetcherWorker:
    """Background worker for hourly post collection.

    Purpose:
        Collect posts from all subscribed channels hourly and save them to MongoDB.
        Processes channels independently, continuing on errors.
    """

    def __init__(self, mcp_url: Optional[str] = None) -> None:
        """Initialize worker.

        Args:
            mcp_url: Optional MCP server URL (defaults to stdio)
        """
        mcp_url = mcp_url or os.getenv("MCP_SERVER_URL")
        self.mcp = get_mcp_client(server_url=mcp_url)
        self.settings = get_settings()
        logger.info("Post fetcher worker initialized",
                   interval_hours=self.settings.post_fetch_interval_hours,
                   ttl_days=self.settings.post_ttl_days)
        self._running = False
        self._last_run: Optional[datetime] = None
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
        logger.info("Post fetcher worker started")
        try:
            while self._running:
                try:
                    if self._should_run():
                        await self._process_all_channels()
                        self._last_run = datetime.utcnow()
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
        try:
            db = await get_db()
            channels_cursor = db.channels.find({"active": True})
            channels = await channels_cursor.to_list(length=1000)
            
            if not channels:
                logger.info("No active channels to process")
                return

            logger.info("Processing channels", channel_count=len(channels))
            
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
                except Exception as e:
                    stats["channels_failed"] += 1
                    await self._handle_channel_error(channel, e)
            
            logger.info("Channel processing completed", statistics=stats)
            
        except Exception as e:
            logger.error("Error processing channels",
                       error=str(e),
                       exc_info=True)

    async def _process_channel(
        self, channel: dict, db
    ) -> dict[str, int]:
        """Process a single channel.

        Purpose:
            Fetch posts from channel, save to database, update last_fetch timestamp.

        Args:
            channel: Channel document from MongoDB
            db: MongoDB database instance

        Returns:
            Dict with saved and skipped counts

        Raises:
            Exception: If channel processing fails
        """
        channel_username = channel["channel_username"]
        user_id = channel["user_id"]
        
        # Determine since timestamp
        last_fetch = channel.get("last_fetch")
        if last_fetch:
            try:
                if isinstance(last_fetch, str):
                    since = datetime.fromisoformat(last_fetch.replace("Z", "+00:00"))
                else:
                    since = last_fetch
            except (ValueError, AttributeError):
                since = datetime.utcnow() - timedelta(hours=self.settings.post_fetch_interval_hours)
        else:
            since = datetime.utcnow() - timedelta(hours=self.settings.post_fetch_interval_hours)
        
        logger.debug("Processing channel",
                    channel=channel_username,
                    user_id=user_id,
                    since=since.isoformat())
        
        # Fetch posts from Telegram
        posts = await fetch_channel_posts(
            channel_username=channel_username,
            since=since,
            user_id=user_id,
            save_to_db=True  # Automatically save via repository
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
                    }
                )
                result["saved"] = save_result.get("saved", 0)
                result["skipped"] = save_result.get("skipped", 0)
            except Exception as e:
                logger.warning("Failed to save posts via MCP tool",
                             channel=channel_username,
                             error=str(e))
        
        # Update last_fetch timestamp
        await db.channels.update_one(
            {"_id": channel["_id"]},
            {"$set": {"last_fetch": datetime.utcnow().isoformat()}}
        )
        
        logger.debug("Channel processed",
                    channel=channel_username,
                    posts_fetched=len(posts),
                    saved=result["saved"],
                    skipped=result["skipped"])
        
        return result

    async def _handle_channel_error(self, channel: dict, error: Exception) -> None:
        """Handle error during channel processing.

        Purpose:
            Log error and continue processing other channels.

        Args:
            channel: Channel document that failed
            error: Exception that occurred
        """
        logger.error("Error processing channel",
                   channel=channel.get("channel_username"),
                   user_id=channel.get("user_id"),
                   error=str(error),
                   exc_info=True)

