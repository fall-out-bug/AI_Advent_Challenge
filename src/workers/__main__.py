"""Entry point for summary worker."""

from __future__ import annotations

import asyncio
import os
import sys

from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.workers.summary_worker import SummaryWorker

logger = get_logger("worker_main")


async def main() -> None:
    """Start the summary worker."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    mcp_url = os.getenv("MCP_SERVER_URL")
    worker = SummaryWorker(bot_token=bot_token, mcp_url=mcp_url)

    try:
        logger.info("Starting summary worker...")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error("Worker crashed", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())

