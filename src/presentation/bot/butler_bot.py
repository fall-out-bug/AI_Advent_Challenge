"""Minimal aiogram bot skeleton for Butler."""

from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

from src.infrastructure.logging import get_logger
from src.infrastructure.shutdown.graceful_shutdown import GracefulShutdown
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware
from src.presentation.bot.handlers.tasks import tasks_router
from src.presentation.bot.handlers.menu import router as menu_router
from src.presentation.bot.handlers.butler_handler import setup_butler_handler
from src.presentation.bot.metrics_server import MetricsServer
from src.infrastructure.metrics import get_butler_metrics


logger = get_logger("butler_bot")


class ButlerBot:
    """Telegram bot using ButlerOrchestrator for message processing.

    Purpose:
        Main Telegram bot that uses ButlerOrchestrator via Dependency Injection.
        Supports commands (/start, /help, /menu) and natural language processing.

    Args:
        token: Telegram bot token
        orchestrator: ButlerOrchestrator instance for message processing
    """

    def __init__(self, token: str, orchestrator: ButlerOrchestrator) -> None:
        """Initialize Butler bot.

        Args:
            token: Telegram bot token
            orchestrator: ButlerOrchestrator instance (injected via DI)
        """
        self.bot = Bot(token=token)
        # Initialize Dispatcher with FSM storage for state management
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.router = Router()
        self.orchestrator = orchestrator
        self._setup_handlers()
        self.dp.include_router(self.router)
        
        # Initialize metrics server
        self.metrics_server = MetricsServer()
        self._metrics = get_butler_metrics()
        self._metrics.set_health_status(True)
        
        self._shutdown_manager = GracefulShutdown()
        self._shutdown_manager.register_handler(self._shutdown_handler)

    def _setup_handlers(self) -> None:
        """Setup all bot handlers."""
        self.router.message(Command("start"))(self.cmd_start)
        self.router.message(Command("help"))(self.cmd_help)
        self.router.message(Command("menu"))(self.cmd_menu)
        
        # Include existing handler routers
        from src.presentation.bot.handlers import menu, tasks, channels

        self.dp.include_router(menu.router)
        self.dp.include_router(tasks.router)
        self.dp.include_router(channels.router)
        
        # Include butler handler for natural language processing
        butler_router = setup_butler_handler(self.orchestrator)
        self.dp.include_router(butler_router)

    async def cmd_start(self, message: Message) -> None:
        """Handle /start command."""
        try:
            await message.answer("Hello! I'm your Butler. Use /help to see available commands.")
        except Exception as e:
            logger.error("Failed to send start message", user_id=message.from_user.id, error=str(e))

    async def cmd_help(self, message: Message) -> None:
        """Handle /help command."""
        try:
            await message.answer("Available commands: /start, /help, /menu")
        except Exception as e:
            logger.error("Failed to send help message", user_id=message.from_user.id, error=str(e))

    async def cmd_menu(self, message: Message) -> None:
        """Show main menu."""
        try:
            from src.presentation.bot.handlers.menu import build_main_menu

            keyboard = build_main_menu()
            await message.answer("📋 Main Menu:", reply_markup=keyboard.as_markup())
        except Exception as e:
            logger.error("Failed to show menu", user_id=message.from_user.id, error=str(e))
            await message.answer("❌ Sorry, I couldn't load the menu. Please try again.")

    async def run(self) -> None:
        """Start the bot polling loop with graceful shutdown."""
        try:
            # Start metrics server
            await self.metrics_server.start()
            
            self._shutdown_manager.setup_signal_handlers()
            logger.info("Starting bot polling...")
            await self.dp.start_polling(self.bot)
        except asyncio.CancelledError:
            logger.info("Bot polling cancelled")
        finally:
            await self._shutdown_handler()
    
    async def _shutdown_handler(self) -> None:
        """Handle bot shutdown gracefully.
        
        Stops polling, closes bot session, and stops metrics server.
        """
        logger.info("Stopping bot...")
        try:
            self._metrics.set_health_status(False)
            
            # Stop metrics server
            await self.metrics_server.stop()
            
            await self.dp.stop_polling()
            await self.bot.session.close()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}", exc_info=True)



def create_dispatcher() -> Dispatcher:
    """Create aiogram Dispatcher with FSM storage, middleware, and routers.

    Purpose:
        Provide a configured `Dispatcher` that can be used by a runner to
        start the Telegram bot. Uses in-memory FSM storage suitable for
        development and tests.

    Returns:
        Configured `Dispatcher` instance.

    Example:
        dp = create_dispatcher()
        # runner elsewhere attaches Bot(token) and starts polling
    """
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register outer middleware explicitly for aiogram v3 compatibility
    dp.update.outer_middleware.register(StatePersistenceMiddleware())

    dp.include_router(tasks_router)
    dp.include_router(menu_router)

    return dp


async def main() -> None:  # pragma: no cover - manual run helper
    import os
    from src.presentation.bot.factory import create_butler_orchestrator

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    
    # Create orchestrator using factory
    orchestrator = await create_butler_orchestrator()
    
    # Create bot with orchestrator via DI
    bot = ButlerBot(token=token, orchestrator=orchestrator)
    await bot.run()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())


