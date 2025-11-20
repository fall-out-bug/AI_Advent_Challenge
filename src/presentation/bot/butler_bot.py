"""Minimal aiogram bot skeleton for Butler."""

from __future__ import annotations

import asyncio

<<<<<<< HEAD
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import Any
=======
>>>>>>> origin/master

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from src.infrastructure.logging import get_logger
from src.infrastructure.metrics import get_butler_metrics
from src.infrastructure.shutdown.graceful_shutdown import GracefulShutdown
from src.presentation.bot.handlers.butler_handler import setup_butler_handler
from src.presentation.bot.handlers.menu import router as menu_router
from src.presentation.bot.metrics_server import MetricsServer
from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware
from src.presentation.bot.orchestrator import ButlerOrchestrator

logger = get_logger("butler_bot")

<<<<<<< HEAD
=======
# Voice handler will be set up asynchronously
_voice_handler_initialized = False

>>>>>>> origin/master

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
<<<<<<< HEAD
        self._personalized_reply_use_case = None
        self._setup_handlers()
        self.dp.include_router(self.router)

=======
        self._setup_handlers()
        self.dp.include_router(self.router)

        # Voice handler will be set up asynchronously in setup_voice_handler()
        # This is done to allow async initialization of use cases

>>>>>>> origin/master
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
        from src.presentation.bot.handlers import channels, menu

        if getattr(menu.router, "_parent_router", None) is not None:
            menu.router._parent_router = None
        self.dp.include_router(menu.router)

        if getattr(channels.router, "_parent_router", None) is not None:
            channels.router._parent_router = None
        self.dp.include_router(channels.router)

<<<<<<< HEAD
        # Setup personalization if enabled
        personalized_reply_use_case = self._create_personalization_use_cases()

        # Include butler handler for natural language processing
        butler_router = setup_butler_handler(
            self.orchestrator,
            personalized_reply_use_case=personalized_reply_use_case,
        )
        self.dp.include_router(butler_router)

        # Store for voice handler setup
        self._personalized_reply_use_case = personalized_reply_use_case
=======
        # Include butler handler for natural language processing
        butler_router = setup_butler_handler(self.orchestrator)
        self.dp.include_router(butler_router)

        # Voice handler will be set up asynchronously via setup_voice_handler()
>>>>>>> origin/master

    async def cmd_start(self, message: Message) -> None:
        """Handle /start command."""
        try:
            await message.answer(
                "Hello! I'm your Butler. Use /help to see available commands."
            )
        except Exception as e:
            logger.error(
                "Failed to send start message",
                user_id=message.from_user.id,
                error=str(e),
            )

    async def cmd_help(self, message: Message) -> None:
        """Handle /help command."""
        try:
            await message.answer("Available commands: /start, /help, /menu")
        except Exception as e:
            logger.error(
                "Failed to send help message",
                user_id=message.from_user.id,
                error=str(e),
            )

    async def cmd_menu(self, message: Message) -> None:
        """Show main menu."""
        try:
            from src.presentation.bot.handlers.menu import build_main_menu

            keyboard = build_main_menu()
            await message.answer("📋 Main Menu:", reply_markup=keyboard.as_markup())
        except Exception as e:
            logger.error(
                "Failed to show menu", user_id=message.from_user.id, error=str(e)
            )
            await message.answer("❌ Sorry, I couldn't load the menu. Please try again.")

<<<<<<< HEAD
    def _create_personalization_use_cases(self) -> "Optional[Any]":
        """Create personalization use cases if enabled.

        Purpose:
            Initialize personalization use cases based on feature flag.
            Returns None if personalization is disabled or initialization fails.

        Returns:
            PersonalizedReplyUseCase instance or None.
        """
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        if not settings.personalization_enabled:
            logger.info("Personalization disabled")
            return None

        try:
            logger.info("Personalization enabled, creating use cases...")

            # Get dependencies
            from src.infrastructure.clients.llm_client import get_llm_client
            from src.infrastructure.database.mongo import get_client

            # Note: These are async, but we can't use await in sync method
            # We'll create them lazily in async setup if needed
            # For now, return None and create in async setup_voice_handler
            logger.info(
                "Personalization will be initialized asynchronously in setup_voice_handler"
            )
            return None

        except Exception as e:
            logger.error(
                "Failed to create personalization use cases",
                extra={"error": str(e)},
                exc_info=True,
            )
            return None

=======
>>>>>>> origin/master
    async def setup_voice_handler(self) -> None:
        """Setup voice handler asynchronously.

        Purpose:
            Initialize voice agent use cases and register voice handler.
            This is done asynchronously because use cases require async
            initialization (Redis connection, etc.).

        Example:
            >>> bot = ButlerBot(token, orchestrator)
            >>> await bot.setup_voice_handler()
        """
<<<<<<< HEAD
        if getattr(self, "_voice_handler_initialized", False):
=======
        global _voice_handler_initialized
        if _voice_handler_initialized:
>>>>>>> origin/master
            logger.debug("Voice handler already initialized")
            return

        try:
            from src.infrastructure.voice.factory import create_voice_use_cases
            from src.presentation.bot.handlers.voice_handler import setup_voice_handler

            # Create voice use cases
            process_uc, confirmation_uc = await create_voice_use_cases(
                orchestrator=self.orchestrator,
                bot=self.bot,
            )

<<<<<<< HEAD
            # Create personalization use cases if enabled
            personalized_reply_use_case = await self._setup_personalization()

=======
>>>>>>> origin/master
            # Setup and register voice handler
            voice_router = setup_voice_handler(
                process_use_case=process_uc,
                confirmation_use_case=confirmation_uc,
<<<<<<< HEAD
                personalized_reply_use_case=personalized_reply_use_case,
=======
>>>>>>> origin/master
            )
            self.dp.include_router(voice_router)

            logger.info("Voice handler initialized and registered")
<<<<<<< HEAD
            self._voice_handler_initialized = True
=======
            _voice_handler_initialized = True
>>>>>>> origin/master

        except Exception as e:
            logger.error(
                f"Failed to setup voice handler: {e}. "
                "Bot will continue without voice support.",
                exc_info=True,
            )
<<<<<<< HEAD
            # Don't raise - bot should work without voice support

    async def _setup_personalization(self) -> "Optional[Any]":
        """Setup personalization use cases asynchronously.

        Purpose:
            Initialize personalization use cases with async dependencies.
            Returns None if personalization is disabled or initialization fails.

        Returns:
            PersonalizedReplyUseCase instance or None.
        """
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        if not settings.personalization_enabled:
            logger.debug("Personalization disabled")
            return None

        try:
            logger.info("Creating personalization use cases...")

            # Get async dependencies
            from src.infrastructure.clients.llm_client import get_llm_client
            from src.infrastructure.database.mongo import get_client
            from src.infrastructure.personalization.factory import (
                create_personalized_use_cases,
            )

            mongo_client = await get_client()
            llm_client = get_llm_client()

            personalized_reply_use_case, _ = create_personalized_use_cases(
                settings, mongo_client, llm_client
            )

            logger.info("Personalization use cases created successfully")

            # Update butler handler with use case
            from src.presentation.bot.handlers.butler_handler import (
                setup_butler_handler,
            )

            # Re-setup butler handler with personalization
            butler_router = setup_butler_handler(
                self.orchestrator,
                personalized_reply_use_case=personalized_reply_use_case,
            )
            # Remove old router and add new one
            # Note: This is a bit hacky, but aiogram doesn't provide easy way to update routers
            # In production, this should be done during initial setup
            self._personalized_reply_use_case = personalized_reply_use_case

            return personalized_reply_use_case

        except Exception as e:
            logger.error(
                "Failed to create personalization use cases",
                extra={"error": str(e)},
                exc_info=True,
            )
            return None

=======
            # Log specific error details for debugging
            import traceback
            logger.debug(
                "Voice handler initialization traceback",
                extra={"traceback": traceback.format_exc()},
            )
            # Don't raise - bot should work without voice support

>>>>>>> origin/master
    async def run(self) -> None:
        """Start the bot polling loop with graceful shutdown."""
        try:
            # Setup voice handler (async initialization)
            await self.setup_voice_handler()

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
        close_error: Exception | None = None
        try:
            self._metrics.set_health_status(False)
            await self.metrics_server.stop()
            await self.dp.stop_polling()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Error during bot shutdown: {exc}", exc_info=True)
        finally:
            try:
                await self.bot.session.close()
            except Exception as exc:  # noqa: BLE001
                close_error = exc
                logger.error(
                    f"Failed to close bot session: {exc}", exc_info=True
                )

        if close_error is None:
            logger.info("Bot stopped successfully")


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

    dp.include_router(menu_router)

    return dp


async def main() -> None:  # pragma: no cover - manual run helper
    import os

<<<<<<< HEAD
    from src.presentation.bot.factory import create_butler_orchestrator

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
=======
    from src.infrastructure.config.settings import get_settings
    from src.presentation.bot.factory import create_butler_orchestrator

    # Try to get token from environment or Settings
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        # pydantic-settings automatically loads .env, but os.environ might not have it
        # Try loading via Settings or dotenv as fallback
        try:
            from dotenv import load_dotenv

            load_dotenv()
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        except ImportError:
            pass

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is required. "
            "Set it in environment variable or .env file."
        )
>>>>>>> origin/master

    # Create orchestrator using factory
    orchestrator = await create_butler_orchestrator()

    # Create bot with orchestrator via DI
    bot = ButlerBot(token=token, orchestrator=orchestrator)
    await bot.run()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
<<<<<<< HEAD
=======

>>>>>>> origin/master
