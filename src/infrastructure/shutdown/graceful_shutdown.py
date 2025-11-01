"""Graceful shutdown utilities.

Following Python Zen:
- Errors should never pass silently
- Beautiful is better than ugly
"""

import asyncio
import logging
import signal
from typing import Optional, List, Callable

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Manager for graceful shutdown operations.
    
    Purpose:
        Coordinate graceful shutdown of async components.
        Handles SIGTERM/SIGINT signals and waits for tasks to complete.
    """
    
    # Default configuration constants
    DEFAULT_SHUTDOWN_TIMEOUT = 30.0  # seconds
    
    def __init__(self, shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT):
        """Initialize shutdown manager.
        
        Args:
            shutdown_timeout: Maximum time to wait for shutdown (seconds)
        """
        self.shutdown_timeout = shutdown_timeout
        self.shutdown_handlers: List[Callable] = []
        self.shutdown_event = asyncio.Event()
        self.is_shutting_down = False
    
    def register_handler(self, handler: Callable) -> None:
        """Register shutdown handler.
        
        Args:
            handler: Async function to call on shutdown
        """
        self.shutdown_handlers.append(handler)
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for SIGTERM and SIGINT."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s))
            )
    
    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal.
        
        Args:
            sig: Signal received
        """
        signal_name = signal.Signals(sig).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        await self.shutdown()
    
    async def shutdown(self) -> None:
        """Execute graceful shutdown.
        
        Runs all registered handlers and waits for completion.
        """
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        self.shutdown_event.set()
        
        logger.info(f"Shutting down {len(self.shutdown_handlers)} handlers...")
        
        tasks = []
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler()))
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {e}", exc_info=True)
        
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Shutdown timeout ({self.shutdown_timeout}s) exceeded. "
                    "Some tasks may not have completed."
                )
        
        logger.info("Shutdown complete")
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()


class AgentShutdownMixin:
    """Mixin for adding graceful shutdown to agents.
    
    Purpose:
        Provides shutdown methods for agent components.
    """
    
    def __init__(self):
        """Initialize shutdown mixin."""
        self._shutdown_event = asyncio.Event()
        self._active_tasks: List[asyncio.Task] = []
    
    async def shutdown(self) -> None:
        """Shutdown agent gracefully.
        
        Cancels active tasks and waits for completion.
        """
        logger.info("Shutting down agent...")
        self._shutdown_event.set()
        
        # Cancel all active tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        logger.info("Agent shutdown complete")
    
    def register_task(self, task: asyncio.Task) -> None:
        """Register task for shutdown tracking.
        
        Args:
            task: Task to track
        """
        self._active_tasks.append(task)
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown was requested.
        
        Returns:
            True if shutdown requested
        """
        return self._shutdown_event.is_set()

