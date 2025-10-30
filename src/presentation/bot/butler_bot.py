"""Minimal aiogram bot skeleton for Butler."""

from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.presentation.mcp.client import get_mcp_client
from src.infrastructure.monitoring.logger import get_logger
from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware
from src.presentation.bot.handlers.tasks import tasks_router
from src.presentation.bot.handlers.menu import router as menu_router


logger = get_logger(name="butler_bot")


class ButlerBot:
    """Minimal Telegram bot exposing /start and /help.

    Purpose:
        Provide a starting point for future handlers; supports .run().

    Args:
        token: Telegram bot token
    """

    def __init__(self, token: str) -> None:
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.router = Router()
        self._setup_handlers()
        self.dp.include_router(self.router)
        # Use HTTP client if MCP_SERVER_URL is set, otherwise stdio
        import os
        mcp_url = os.getenv("MCP_SERVER_URL")
        self._mcp = get_mcp_client(server_url=mcp_url)

    def _setup_handlers(self) -> None:
        self.router.message(Command("start"))(self.cmd_start)
        self.router.message(Command("help"))(self.cmd_help)
        self.router.message(Command("menu"))(self.cmd_menu)
        # Include handler routers
        from src.presentation.bot.handlers import menu, tasks, channels

        self.dp.include_router(menu.router)
        self.dp.include_router(tasks.router)
        self.dp.include_router(channels.router)
        # Natural language handler (lower priority, after menu commands)
        self.router.message(F.text)(self.handle_natural_language)

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
        """Start the bot polling loop."""
        await self.dp.start_polling(self.bot)

    async def handle_natural_language(self, message: Message) -> None:
        """Handle free-form text: parse intent and route to appropriate handler.
        
        Purpose:
            Parse user intent and route to:
            - Digest generation if digest intent detected
            - Task creation if task intent detected
            - Clarification if intent unclear
        """
        user_id = message.from_user.id
        text = message.text or ""
        
        try:
            # First, check if this is a digest request
            digest_intent = await self._mcp.call_tool("parse_digest_intent", {"text": text, "user_context": {"user_id": user_id}})
            
            if digest_intent.get("intent_type") == "digest" and digest_intent.get("confidence", 0) >= 0.7:
                # Handle digest request
                await self._handle_digest_intent(message, digest_intent)
                return
            
            # Otherwise, try parsing as task intent
            intent = await self._mcp.call_tool("parse_task_intent", {"text": text, "user_context": {"user_id": user_id}})
            if intent.get("needs_clarification"):
                await self._handle_clarification(message, intent)
                return
            await self._create_task_from_intent(message, intent)
        except Exception as e:
            logger.error("Failed to handle natural language", user_id=user_id, text=text[:100], error=str(e))
            await message.answer("❌ Sorry, I couldn't process that. Please try again or use /menu.")

    async def _handle_digest_intent(self, message: Message, digest_intent: dict) -> None:
        """Handle digest generation intent.
        
        Purpose:
            Generate PDF digest when user requests it via natural language.
            Uses the same logic as menu callback but triggered by intent.
        
        Args:
            message: Telegram message
            digest_intent: Parsed digest intent with mcp_tools, hours, etc.
        """
        user_id = message.from_user.id
        hours = digest_intent.get("hours", 24)
        
        logger.info("Handling digest intent", user_id=user_id, hours=hours, confidence=digest_intent.get("confidence"))
        
        # Check if clarification needed
        if digest_intent.get("needs_clarification"):
            questions = digest_intent.get("questions", [])
            if questions:
                await message.answer(f"Чтобы сгенерировать дайджест, уточните:\n\n" + "\n".join(f"• {q}" for q in questions))
            return
        
        # Show typing action
        try:
            from aiogram.enums import ChatAction
            await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
        except Exception:
            pass
        
        try:
            # Import digest generation function
            from src.presentation.bot.handlers.menu import generate_pdf_digest_for_user
            from src.infrastructure.cache.pdf_cache import get_pdf_cache
            from aiogram.types import BufferedInputFile
            from datetime import datetime
            import base64
            
            cache = get_pdf_cache()
            
            # Generate cache key
            now = datetime.utcnow()
            date_hour = now.strftime("%Y-%m-%d-%H")
            
            # Check cache first
            cached_pdf = cache.get(user_id, date_hour)
            if cached_pdf:
                logger.debug(f"Cache hit for user {user_id}, date_hour {date_hour}")
                filename = f"digest_{now.strftime('%Y-%m-%d')}.pdf"
                document = BufferedInputFile(cached_pdf, filename=filename)
                await message.answer_document(document=document)
                return
            
            # Generate PDF digest
            pdf_result = await generate_pdf_digest_for_user(user_id, hours=hours)
            
            if pdf_result.get("error") == "no_posts":
                await message.answer(f"📰 За последние {hours} часов новых постов не найдено.")
                return
            
            if "error" in pdf_result:
                # Fallback to text digest
                logger.warning("PDF generation failed, falling back to text digest", user_id=user_id)
                result = await self._mcp.call_tool("get_channel_digest", {"user_id": int(user_id), "hours": hours})
                digests = result.get("digests", [])
                if not digests:
                    await message.answer(f"📰 За последние {hours} часов постов не найдено.")
                    return
                
                # Format all channels
                digest_parts = [f"📰 Digest за последние {hours} часов:\n"]
                for digest in digests:
                    channel_name = digest.get("channel", "Unknown")
                    summary = digest.get("summary", "")
                    post_count = digest.get("post_count", 0)
                    digest_parts.append(f"\n📌 {channel_name} ({post_count} постов):\n{summary}")
                
                full_digest = "\n".join(digest_parts)
                if len(full_digest) > 4000:
                    await message.answer(full_digest[:4000])
                    remaining = full_digest[4000:]
                    while remaining:
                        await message.answer(remaining[:4000])
                        remaining = remaining[4000:]
                else:
                    await message.answer(full_digest)
                return
            
            # Decode and send PDF
            pdf_bytes_b64 = pdf_result.get("pdf_bytes", "")
            if not pdf_bytes_b64:
                await message.answer("⚠️ Не удалось сгенерировать PDF. Попробуйте позже.")
                return
            
            pdf_bytes = base64.b64decode(pdf_bytes_b64)
            
            # Cache PDF
            cache.set(user_id, date_hour, pdf_bytes)
            
            # Send PDF document
            filename = f"digest_{now.strftime('%Y-%m-%d')}.pdf"
            document = BufferedInputFile(pdf_bytes, filename=filename)
            await message.answer_document(document=document)
            
        except Exception as e:
            logger.error("Error handling digest intent", user_id=user_id, error=str(e), exc_info=True)
            await message.answer("⚠️ Не удалось сгенерировать дайджест. Попробуйте использовать кнопку в меню.")

    async def _handle_clarification(self, message: Message, intent: dict) -> None:
        """Handle clarification questions."""
        qs = intent.get("questions", [])
        if qs:
            q_texts = "\n".join(f"• {q.get('text', '')}" for q in qs)
            await message.answer(f"Please clarify:\n\n{q_texts}")
        else:
            await message.answer("I need more details.")

    async def _create_task_from_intent(self, message: Message, intent: dict) -> None:
        """Create task from parsed intent."""
        task_data = {
            "user_id": message.from_user.id,
            "title": intent.get("title", "Task"),
            "description": intent.get("description") or "",  # Convert None to empty string
            "deadline": intent.get("deadline_iso") or intent.get("deadline"),  # Support both formats
            "priority": intent.get("priority", "medium"),
            "tags": intent.get("tags", []),
        }
        result = await self._mcp.call_tool("add_task", task_data)
        if result.get("status") == "created":
            await message.answer(f"✅ Task added: {task_data['title']}")
        else:
            await message.answer("❌ Failed to create task. Please try again.")


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

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    bot = ButlerBot(token)
    await bot.run()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())


