"""Minimal aiogram bot skeleton for Butler."""

from __future__ import annotations

import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiohttp import ClientConnectorError
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.presentation.mcp.client import get_mcp_client
from src.infrastructure.logging import get_logger
from src.infrastructure.shutdown.graceful_shutdown import GracefulShutdown
from src.infrastructure.database.mongo import get_db
from src.infrastructure.dialogs.dialog_manager import DialogManager
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.domain.agents.mcp_aware_agent import MCPAwareAgent
from src.domain.agents.schemas import AgentRequest
from src.presentation.bot.middleware.state_middleware import StatePersistenceMiddleware
from src.presentation.bot.handlers.tasks import tasks_router
from src.presentation.bot.handlers.menu import router as menu_router


logger = get_logger("butler_bot")


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
        base_mcp_client = get_mcp_client(server_url=mcp_url)
        self._mcp = RobustMCPClient(base_client=base_mcp_client)
        
        # Will be initialized in run()
        self._agent = None
        self._dialog_manager = None
        
        self._shutdown_manager = GracefulShutdown()
        self._shutdown_manager.register_handler(self._shutdown_handler)
    
    async def _init_agent(self) -> None:
        """Initialize MCP-aware agent asynchronously.
        
        Creates agent with LLM client and MongoDB dialog manager.
        """
        from src.infrastructure.utils.path_utils import ensure_shared_in_path
        
        ensure_shared_in_path()
        from shared_package.clients.unified_client import UnifiedModelClient
        
        llm_client = UnifiedModelClient()
        mongodb = await get_db()
        dialog_manager = DialogManager(mongodb=mongodb, llm_client=llm_client)
        
        self._agent = MCPAwareAgent(
            mcp_client=self._mcp,
            llm_client=llm_client,
            model_name="mistral"
        )
        self._dialog_manager = dialog_manager

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
        """Start the bot polling loop with graceful shutdown."""
        # Initialize agent asynchronously
        await self._init_agent()
        
        try:
            self._shutdown_manager.setup_signal_handlers()
            await self.dp.start_polling(self.bot)
        except asyncio.CancelledError:
            logger.info("Bot polling cancelled")
        finally:
            await self._shutdown_handler()
    
    async def _shutdown_handler(self) -> None:
        """Handle bot shutdown gracefully.
        
        Stops polling and closes bot session.
        """
        logger.info("Stopping bot...")
        try:
            await self.dp.stop_polling()
            await self.bot.session.close()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}", exc_info=True)

    async def handle_natural_language(self, message: Message) -> None:
        """Handle free-form text using MCP-aware agent.
        
        Purpose:
            Use MCP-aware agent to process user requests.
            Agent automatically discovers and uses available tools.
        """
        user_id = message.from_user.id
        text = message.text or ""
        session_id = f"telegram_{user_id}"
        
        # Ensure agent is initialized
        if not self._agent:
            await self._init_agent()
        
        try:
            # Get dialog context
            context = ""
            if self._dialog_manager:
                context = await self._dialog_manager.get_context(session_id)
            
            # Create agent request
            request = AgentRequest(
                user_id=user_id,
                message=text,
                session_id=session_id,
                context={"dialog_context": context} if context else {}
            )
            
            # Process with agent
            response = await self._agent.process(request)
            
            # Save dialog messages
            if self._dialog_manager:
                await self._dialog_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=text
                )
                await self._dialog_manager.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response.text
                )
            
            # Send response
            if response.success:
                # Telegram has a 4096 character limit per message
                # If response is too long, generate PDF instead
                response_text = response.text
                MAX_MESSAGE_LENGTH = 4000  # Leave some margin
                
                if len(response_text) > MAX_MESSAGE_LENGTH:
                    # Generate PDF for long responses
                    await self._send_long_response_as_pdf(message, response_text, user_id)
                else:
                    await self._safe_answer(message, response_text)
                
                # Send reasoning report as second message if available
                if response.reasoning:
                    await self._safe_answer(message, f"📊 Отчет о выполнении:\n\n{response.reasoning}")
            else:
                await self._safe_answer(
                    message,
                    f"❌ {response.text}\n\n"
                    "Попробуйте еще раз или используйте /menu для списка команд."
                )
                # Send error reasoning if available
                if response.reasoning:
                    await self._safe_answer(message, f"📊 Отчет об ошибке:\n\n{response.reasoning}")
        
        except Exception as e:
            logger.error(
                "Failed to handle natural language",
                user_id=user_id,
                text=text[:100],
                error=str(e)
            )
            await self._safe_answer(
                message,
                "❌ Произошла ошибка при обработке запроса. "
                "Попробуйте еще раз или используйте /menu."
            )

    async def _safe_answer(self, message: Message, text: str) -> None:
        """Send a text message with small retry/backoff to survive Bot API hiccups.

        Retries on network-related errors without crashing the handler.
        """
        delays = [0, 0.8, 2.0]
        last_err: Exception | None = None
        for delay in delays:
            if delay:
                try:
                    await asyncio.sleep(delay)
                except Exception:
                    pass
            try:
                await message.answer(text)
                return
            except (ClientConnectorError, TelegramBadRequest) as e:
                last_err = e
                logger.warning("send answer failed, retrying", user_id=message.from_user.id, error=str(e))
                continue
            except Exception as e:
                last_err = e
                logger.error("send answer failed (non-retryable)", user_id=message.from_user.id, error=str(e))
                break
        # Give up silently but log
        if last_err:
            logger.error("send answer gave up after retries", user_id=message.from_user.id, error=str(last_err))

    async def _send_long_response_as_pdf(self, message: Message, text: str, user_id: int) -> None:
        """Generate PDF from long text response and send it.
        
        Purpose:
            Convert long text response to PDF format and send as document.
            Uses MCP tools to convert markdown to PDF.
        
        Args:
            message: Telegram message object
            text: Long text response to convert
            user_id: Telegram user ID
        """
        try:
            # Show typing action
            from aiogram.enums import ChatAction
            await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
        except Exception:
            pass
        
        try:
            from src.infrastructure.cache.pdf_cache import get_pdf_cache
            from aiogram.types import BufferedInputFile
            from datetime import datetime
            import base64
            
            # Format text as markdown
            # Add title and metadata
            now = datetime.utcnow()
            title = f"# Ответ от бота\n\n*Дата:* {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
            markdown_content = title + text
            
            # Convert to PDF using MCP tool
            metadata = {
                "generation_date": now.isoformat(),
                "user_id": user_id,
                "title": "Ответ от бота"
            }
            
            pdf_result = await self._mcp.call_tool(
                "convert_markdown_to_pdf",
                {"markdown": markdown_content, "metadata": metadata}
            )
            
            if "error" in pdf_result:
                logger.warning("PDF generation failed, falling back to text", user_id=user_id, error=pdf_result.get("error"))
                # Fallback: split into chunks
                MAX_CHUNK = 4000
                chunks = []
                remaining = text
                while remaining:
                    chunk = remaining[:MAX_CHUNK]
                    if len(remaining) > MAX_CHUNK:
                        last_break = max(
                            chunk.rfind('\n\n'),
                            chunk.rfind('\n'),
                            chunk.rfind('. ')
                        )
                        if last_break > MAX_CHUNK * 0.7:
                            chunk = chunk[:last_break + 1]
                            remaining = remaining[last_break + 1:].lstrip()
                        else:
                            remaining = remaining[MAX_CHUNK:]
                    else:
                        remaining = ""
                    chunks.append(chunk)
                
                for i, chunk in enumerate(chunks, 1):
                    if len(chunks) > 1:
                        chunk_with_header = f"[{i}/{len(chunks)}]\n\n{chunk}"
                    else:
                        chunk_with_header = chunk
                    await message.answer(chunk_with_header)
                return
            
            # Decode PDF bytes
            pdf_bytes_b64 = pdf_result.get("pdf_bytes", "")
            if not pdf_bytes_b64:
                logger.warning("PDF bytes not found in result", user_id=user_id)
                await message.answer("⚠️ Не удалось сгенерировать PDF. Ответ слишком длинный для отправки текстом.")
                return
            
            pdf_bytes = base64.b64decode(pdf_bytes_b64)
            
            # Send PDF document
            filename = f"response_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            document = BufferedInputFile(pdf_bytes, filename=filename)
            await message.answer_document(document=document)
            
            logger.info("Sent long response as PDF", user_id=user_id, size=len(pdf_bytes))
            
        except Exception as e:
            logger.error("Error generating PDF from response", user_id=user_id, error=str(e), exc_info=True)
            # Fallback to text chunks
            try:
                MAX_CHUNK = 4000
                chunks = []
                remaining = text
                while remaining:
                    chunk = remaining[:MAX_CHUNK]
                    if len(remaining) > MAX_CHUNK:
                        last_break = max(
                            chunk.rfind('\n\n'),
                            chunk.rfind('\n'),
                            chunk.rfind('. ')
                        )
                        if last_break > MAX_CHUNK * 0.7:
                            chunk = chunk[:last_break + 1]
                            remaining = remaining[last_break + 1:].lstrip()
                        else:
                            remaining = remaining[MAX_CHUNK:]
                    else:
                        remaining = ""
                    chunks.append(chunk)
                
                for i, chunk in enumerate(chunks, 1):
                    if len(chunks) > 1:
                        chunk_with_header = f"[{i}/{len(chunks)}]\n\n{chunk}"
                    else:
                        chunk_with_header = chunk
                    await message.answer(chunk_with_header)
            except Exception as fallback_error:
                logger.error("Fallback text splitting also failed", user_id=user_id, error=str(fallback_error))
                await message.answer("⚠️ Ответ слишком длинный и не удалось создать PDF. Попробуйте позже.")
    
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


