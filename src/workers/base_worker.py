"""Base worker class for background task processing."""

from __future__ import annotations

import asyncio
import logging
import signal
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """Base class for background workers.

    Purpose:
        Provides common functionality for all workers:
        - Signal handling for graceful shutdown
        - Running state management
        - Lifecycle hooks

    Example:
        class MyWorker(BaseWorker):
            async def process_task(self):
                # Your task processing logic
                pass

            async def run(self):
                await super().run()
                while self._running:
                    await self.process_task()
                    await asyncio.sleep(1)
    """

    def __init__(self, worker_name: str) -> None:
        """Initialize base worker.

        Args:
            worker_name: Name of the worker for logging
        """
        self.worker_name = worker_name
        self._running = False
        self._setup_signal_handlers()
        logger.info(f"{self.worker_name} initialized")

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(
                f"{self.worker_name} received shutdown signal: {signum}"
            )
            self.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def stop(self) -> None:
        """Stop worker gracefully.

        Purpose:
            Sets running flag to False, allowing worker loop to exit.
            Subclasses can override to add cleanup logic.
        """
        self._running = False
        logger.info(f"{self.worker_name} stop requested")

    def is_running(self) -> bool:
        """Check if worker is running.

        Returns:
            True if worker is running
        """
        return self._running

    async def on_start(self) -> None:
        """Hook called before worker starts.

        Purpose:
            Override in subclasses to perform initialization.
        """
        pass

    async def on_stop(self) -> None:
        """Hook called after worker stops.

        Purpose:
            Override in subclasses to perform cleanup.
        """
        pass

    @abstractmethod
    async def run(self) -> None:
        """Main worker loop.

        Purpose:
            Implement in subclasses with worker-specific logic.
            Should check self._running and call self.stop() appropriately.
        """
        raise NotImplementedError("Subclasses must implement run()")

    async def run_with_lifecycle(self) -> None:
        """Run worker with lifecycle hooks.

        Purpose:
            Wrapper that calls on_start, run, and on_stop in sequence.
            Use this instead of run() for automatic lifecycle management.

        Example:
            worker = MyWorker("my_worker")
            await worker.run_with_lifecycle()
        """
        try:
            await self.on_start()
            self._running = True
            logger.info(f"{self.worker_name} started")
            await self.run()
        except Exception as e:
            logger.error(
                f"{self.worker_name} error: {e}",
                exc_info=True,
            )
        finally:
            self._running = False
            await self.on_stop()
            logger.info(f"{self.worker_name} stopped")

