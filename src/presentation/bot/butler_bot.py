"""Minimal aiogram bot skeleton for Butler."""

from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from src.presentation.mcp.client import get_mcp_client
from src.infrastructure.monitoring.logger import get_logger

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
        """Handle free-form text: parse intent and create a task via MCP if resolved."""
        user_id = message.from_user.id
        text = message.text or ""
        
        try:
            intent = await self._mcp.call_tool("parse_task_intent", {"text": text, "user_context": {}})
            if intent.get("needs_clarification"):
                await self._handle_clarification(message, intent)
                return
            await self._create_task_from_intent(message, intent)
        except Exception as e:
            logger.error("Failed to handle natural language", user_id=user_id, text=text[:100], error=str(e))
            await message.answer("❌ Sorry, I couldn't process that. Please try again or use /menu.")

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
            "description": intent.get("description", ""),
            "deadline": intent.get("deadline"),
            "priority": intent.get("priority", "medium"),
            "tags": intent.get("tags", []),
        }
        result = await self._mcp.call_tool("add_task", task_data)
        if result.get("status") == "created":
            await message.answer(f"✅ Task added: {task_data['title']}")
        else:
            await message.answer("❌ Failed to create task. Please try again.")


async def main() -> None:  # pragma: no cover - manual run helper
    import os

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    bot = ButlerBot(token)
    await bot.run()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())


