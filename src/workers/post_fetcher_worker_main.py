"""Entry point for post fetcher worker."""

from __future__ import annotations

import asyncio
import os
import sys

from src.infrastructure.logging import get_logger
from src.workers.post_fetcher_worker import PostFetcherWorker

logger = get_logger("post_fetcher_worker_main")


async def main() -> None:
    """Start the post fetcher worker."""
    mcp_url = os.getenv("MCP_SERVER_URL")
    worker = PostFetcherWorker(mcp_url=mcp_url)

    try:
        logger.info("Starting post fetcher worker...")
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

