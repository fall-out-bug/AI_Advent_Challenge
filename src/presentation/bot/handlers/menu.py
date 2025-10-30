"""Main menu handlers for bot navigation."""

from __future__ import annotations

import base64
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatAction, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.presentation.mcp.client import MCPClient
from src.infrastructure.cache.pdf_cache import get_pdf_cache
from src.infrastructure.monitoring.logger import get_logger
from src.infrastructure.monitoring.prometheus_metrics import (
    bot_digest_requests_total,
    bot_digest_cache_hits_total,
    bot_digest_errors_total,
)

logger = get_logger(name="menu_handlers")

# Constants
MAX_ITEMS_PER_PAGE = 10


def build_main_menu() -> InlineKeyboardBuilder:
    """Build main menu inline keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Tasks", callback_data="menu:tasks")
    builder.button(text="📰 Channels", callback_data="menu:channels")
    builder.button(text="📊 Summary", callback_data="menu:summary")
    builder.button(text="📮 Digest", callback_data="menu:digest")
    builder.adjust(2, 2)
    return builder


def build_back_button() -> InlineKeyboardBuilder:
    """Build back button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back", callback_data="menu:main")
    return builder


router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Show main menu."""
    keyboard = build_main_menu()
    await message.answer("📋 Main Menu:", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery) -> None:
    """Return to main menu."""
    keyboard = build_main_menu()
    await callback.message.edit_text("📋 Main Menu:", reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data == "menu:tasks")
async def callback_tasks(callback: CallbackQuery) -> None:
    """Navigate to tasks menu."""
    from src.presentation.bot.handlers.tasks import build_tasks_menu

    keyboard = build_tasks_menu()
    await callback.message.edit_text("📝 Tasks:", reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data == "menu:channels")
async def callback_channels(callback: CallbackQuery) -> None:
    """Navigate to channels menu."""
    from src.presentation.bot.handlers.channels import build_channels_menu

    keyboard = build_channels_menu()
    await callback.message.edit_text("📰 Channels:", reply_markup=keyboard.as_markup())
    await callback.answer()


@router.callback_query(F.data == "menu:summary")
async def callback_summary(callback: CallbackQuery) -> None:
    """Show task summary."""
    # Placeholder for now
    await callback.answer("Summary coming soon", show_alert=True)


@router.callback_query(F.data == "menu:digest")
async def callback_digest(callback: CallbackQuery) -> None:
    """Show channel digest."""
    # Placeholder for now
    await callback.answer("Digest coming soon", show_alert=True)


menu_router = Router()


def _build_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Summary", callback_data="menu:summary")
    kb.button(text="📰 Digest", callback_data="menu:digest")
    kb.adjust(2)
    return kb


@menu_router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Display main menu with summary and digest actions."""
    await message.answer("Select an action:", reply_markup=_build_menu_kb().as_markup())


@menu_router.callback_query(F.data == "menu:summary")
async def callback_summary(call: CallbackQuery) -> None:
    """Show a task summary via MCP tools with basic error handling."""
    await call.answer()
    user_id = call.from_user.id if call.from_user else 0
    try:
        client = MCPClient()
        # timeframe could be configurable; use 'today' default
        result = await client.call_tool("get_summary", {"user_id": int(user_id), "timeframe": "today"})
        stats = result.get("stats", {})
        total = stats.get("total", 0)
        completed = stats.get("completed", 0)
        overdue = stats.get("overdue", 0)
        high_priority = stats.get("high_priority", 0)
        await call.message.answer(
            f"📋 Summary (today)\n\nTotal: {total}\nCompleted: {completed}\nOverdue: {overdue}\nHigh priority: {high_priority}"
        )
    except Exception as e:
        await call.message.answer("⚠️ Failed to fetch summary. Please try again later.")


async def _generate_pdf_digest(client: MCPClient, user_id: int, hours: int = 24) -> dict:
    """Generate PDF digest via MCP tools.

    Purpose:
        Generate PDF digest by calling MCP tools in sequence:
        1. get_posts_from_db
        2. summarize_posts (for each channel)
        3. format_digest_markdown
        4. combine_markdown_sections
        5. convert_markdown_to_pdf

    Args:
        client: MCP client instance
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with pdf_bytes (base64), file_size, pages, or error
    """
    try:
        # Step 1: Get posts from database
        posts_result = await client.call_tool("get_posts_from_db", {"user_id": user_id, "hours": hours})
        posts_by_channel = posts_result.get("posts_by_channel", {})
        
        if not posts_by_channel:
            return {"error": "no_posts"}

        # Step 2: Summarize each channel
        summaries = []
        for channel_name, posts in posts_by_channel.items():
            summary_result = await client.call_tool(
                "summarize_posts",
                {"posts": posts, "channel_username": channel_name, "max_sentences": 5}
            )
            summaries.append(summary_result)

        # Step 3: Format as markdown
        metadata = {
            "generation_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "channels_count": len(summaries),
            "total_posts": posts_result.get("total_posts", 0)
        }
        markdown_result = await client.call_tool(
            "format_digest_markdown",
            {"summaries": summaries, "metadata": metadata}
        )

        # Step 4: Combine sections
        combined_result = await client.call_tool(
            "combine_markdown_sections",
            {"sections": [markdown_result.get("markdown", "")]}
        )

        # Step 5: Convert to PDF
        pdf_result = await client.call_tool(
            "convert_markdown_to_pdf",
            {"markdown": combined_result.get("combined_markdown", ""), "metadata": metadata}
        )

        if "error" in pdf_result:
            return {"error": "pdf_generation_failed"}

        return pdf_result
    except Exception as e:
        logger.error("Error generating PDF digest", user_id=user_id, error=str(e), exc_info=True)
        return {"error": "generation_failed"}


@menu_router.callback_query(F.data == "menu:digest")
async def callback_digest(call: CallbackQuery) -> None:
    """Generate and send PDF digest or fallback to text digest.

    Purpose:
        Generate PDF digest via MCP tools with caching support.
        Falls back to text digest if PDF generation fails.

    Flow:
        1. Show "upload_document" action immediately
        2. Check cache first (1 hour TTL)
        3. If not cached, generate PDF via MCP tools
        4. Cache PDF result
        5. Send PDF document or fallback to text digest on error
    """
    await call.answer()
    user_id = call.from_user.id if call.from_user else 0
    bot_digest_requests_total.inc()
    
    # Show upload action immediately
    try:
        if call.message and call.message.chat:
            await call.message.bot.send_chat_action(call.message.chat.id, ChatAction.UPLOAD_DOCUMENT)
    except Exception:
        pass  # Ignore errors in chat action

    try:
        client = MCPClient()
        cache = get_pdf_cache()
        
        # Generate cache key (date + hour)
        now = datetime.utcnow()
        date_hour = now.strftime("%Y-%m-%d-%H")
        
        # Check cache first
        cached_pdf = cache.get(user_id, date_hour)
        if cached_pdf:
            logger.debug(f"Cache hit for user {user_id}, date_hour {date_hour}")
            bot_digest_cache_hits_total.inc()
            filename = f"digest_{now.strftime('%Y-%m-%d')}.pdf"
            document = BufferedInputFile(cached_pdf, filename=filename)
            await call.message.answer_document(document=document)
            return

        # Generate PDF digest
        pdf_result = await _generate_pdf_digest(client, user_id, hours=24)
        
        if pdf_result.get("error") == "no_posts":
            await call.message.answer("📰 No new posts in last 24 hours.")
            return
        
        if "error" in pdf_result:
            # Fallback to text digest
            error_type = pdf_result.get("error", "unknown")
            bot_digest_errors_total.labels(error_type=error_type).inc()
            logger.warning("PDF generation failed, falling back to text digest", user_id=user_id)
            result = await client.call_tool("get_channel_digest", {"user_id": int(user_id), "hours": 24})
            digests = result.get("digests", [])
            if not digests:
                await call.message.answer("📰 No digests available yet.")
                return
            top = digests[0]
            await call.message.answer(f"📰 {top.get('channel', 'channel')}: {top.get('summary', '')}")
            return

        # Decode PDF bytes and send
        pdf_bytes_b64 = pdf_result.get("pdf_bytes", "")
        if not pdf_bytes_b64:
            bot_digest_errors_total.labels(error_type="empty_pdf").inc()
            await call.message.answer("⚠️ Failed to generate PDF. Please try again later.")
            return

        pdf_bytes = base64.b64decode(pdf_bytes_b64)
        
        # Cache PDF
        cache.set(user_id, date_hour, pdf_bytes)
        
        # Send PDF document
        filename = f"digest_{now.strftime('%Y-%m-%d')}.pdf"
        document = BufferedInputFile(pdf_bytes, filename=filename)
        await call.message.answer_document(document=document)
        
    except Exception as e:
        error_type = type(e).__name__
        bot_digest_errors_total.labels(error_type=error_type).inc()
        logger.error("Error in callback_digest", user_id=user_id, error=str(e), exc_info=True)
        await call.message.answer("⚠️ Failed to fetch digest. Please try again later.")

