"""Entry point for unified task worker (summarization + code review)."""

from __future__ import annotations

import asyncio
import os
import sys

from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.worker_metrics import start_worker_metrics_server
from src.workers.summary_worker import SummaryWorker

logger = get_logger("unified_task_worker_main")


async def main() -> None:
    """Start the unified task worker."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    metrics_port = int(os.getenv("WORKER_METRICS_PORT", "9092"))
    start_worker_metrics_server(metrics_port)
    logger.info("Unified worker metrics server listening", extra={"port": metrics_port})

    mcp_url = os.getenv("MCP_SERVER_URL")
    worker = SummaryWorker(bot_token=bot_token, mcp_url=mcp_url)

    try:
        logger.info("Starting unified task worker...")
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:  # noqa: BLE001 - we want to log and exit
        logger.error("Worker crashed", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
