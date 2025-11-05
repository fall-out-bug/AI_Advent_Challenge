"""Background worker for daily dialogs cache refresh.

Purpose:
    Refresh public channels cache from user dialogs once per day.
    Filters out private chats, groups, bots, and DMs.
"""

from __future__ import annotations

import asyncio
import os
import signal
from datetime import datetime, timedelta
from typing import Optional

from pyrogram import Client

from src.infrastructure.cache.dialogs_cache import PublicChannelsCache
from src.infrastructure.logging import get_logger

logger = get_logger("cache_refresh_worker")

# Constants
CHECK_INTERVAL_SECONDS = 3600  # Check every hour
CACHE_REFRESH_INTERVAL_HOURS = 24  # Refresh cache every 24 hours


class CacheRefreshWorker:
    """Background worker for daily dialogs cache refresh.

    Purpose:
        Refreshes public channels cache from user dialogs once per day.
        Ensures cache is up-to-date for fast channel search.
    """

    def __init__(self) -> None:
        """Initialize worker."""
        self.cache = PublicChannelsCache()
        logger.info(
            f"Cache refresh worker initialized: "
            f"refresh_interval_hours={CACHE_REFRESH_INTERVAL_HOURS}"
        )
        self._running = False
        self._last_refresh: Optional[datetime] = None
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
        logger.info("Cache refresh worker started")
        
        try:
            while self._running:
                try:
                    if self._should_refresh():
                        await self._refresh_cache()
                        self._last_refresh = datetime.utcnow()
                    
                    await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                except Exception as e:
                    logger.error(
                        "Worker error in main loop",
                        error=str(e),
                        exc_info=True
                    )
                    await asyncio.sleep(300)  # Wait 5 min on error
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        logger.info("Cleaning up cache refresh worker resources")

    def stop(self) -> None:
        """Stop the worker."""
        logger.info("Stopping cache refresh worker")
        self._running = False

    def _should_refresh(self) -> bool:
        """Check if cache should be refreshed.

        Purpose:
            Determine if cache refresh is needed based on last refresh time
            or cache age.

        Returns:
            True if cache should be refreshed
        """
        # If never refreshed, do it now
        if not self._last_refresh:
            return True
        
        # Check if 24 hours have passed
        hours_since_refresh = (
            (datetime.utcnow() - self._last_refresh).total_seconds() / 3600
        )
        
        if hours_since_refresh >= CACHE_REFRESH_INTERVAL_HOURS:
            logger.info(
                f"Cache refresh needed: hours_since_refresh={hours_since_refresh:.1f}"
            )
            return True
        
        # Note: Cache age check is done in async context in _refresh_cache
        # This method is called from async context, so we rely on _last_refresh
        
        return False

    async def _refresh_cache(self) -> None:
        """Refresh the cache by fetching dialogs from Pyrogram.

        Purpose:
            Initialize Pyrogram client, fetch dialogs, and update cache.
        """
        logger.info("Starting cache refresh")
        
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        
        if not api_id or not api_hash:
            logger.warning(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for cache refresh"
            )
            return
        
        if not session_string:
            logger.warning("TELEGRAM_SESSION_STRING must be set for cache refresh")
            return
        
        client = None
        try:
            import uuid
            client_name = f"cache_refresh_{uuid.uuid4().hex[:8]}"
            
            client = Client(
                client_name,
                api_id=int(api_id),
                api_hash=api_hash,
                session_string=session_string,
                no_updates=True,
            )
            
            await client.start()
            logger.info("Pyrogram client started for cache refresh")
            
            # Check cache age before refreshing
            cache_age = await self.cache.get_cache_age()
            if cache_age is not None and cache_age < CACHE_REFRESH_INTERVAL_HOURS:
                logger.info(
                    f"Cache is still fresh: age={cache_age:.1f} hours, skipping refresh"
                )
                return
            
            # Refresh cache
            count = await self.cache.refresh_cache(client)
            
            logger.info(
                f"Cache refresh completed: channels_cached={count}, "
                f"timestamp={datetime.utcnow().isoformat()}"
            )
            
        except Exception as e:
            logger.error(
                f"Error refreshing cache: {e}",
                exc_info=True
            )
        finally:
            if client and client.is_connected:
                await client.stop()
                logger.debug("Pyrogram client stopped")


async def main():
    """Main entry point for cache refresh worker."""
    worker = CacheRefreshWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

