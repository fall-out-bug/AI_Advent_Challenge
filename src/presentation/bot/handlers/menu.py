"""Main menu handlers for bot navigation."""

from __future__ import annotations

import base64
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.infrastructure.cache.pdf_cache import get_pdf_cache
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.prometheus_metrics import (
    bot_digest_cache_hits_total,
    bot_digest_errors_total,
    bot_digest_requests_total,
)
from src.presentation.mcp.client import get_mcp_client

logger = get_logger("menu_handlers")

# Constants
MAX_ITEMS_PER_PAGE = 10


def build_main_menu() -> InlineKeyboardBuilder:
    """Build main menu inline keyboard."""
    builder = InlineKeyboardBuilder()
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
menu_router = router


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


@router.callback_query(F.data == "menu:channels")
async def callback_channels(callback: CallbackQuery) -> None:
    """Navigate to channels menu."""
    from src.presentation.bot.handlers.channels import build_channels_menu

    keyboard = build_channels_menu()
    await callback.message.edit_text("📰 Channels:", reply_markup=keyboard.as_markup())
    await callback.answer()


async def generate_pdf_digest_for_user(user_id: int, hours: int = 24) -> dict:
    """Public wrapper for PDF digest generation.

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with pdf_bytes (base64), file_size, pages, or error
    """
    client = get_mcp_client()
    return await _generate_pdf_digest(client, user_id, hours=hours)


async def _generate_pdf_digest(client, user_id: int, hours: int = 24) -> dict:
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
        posts_result = await client.call_tool(
            "get_posts_from_db", {"user_id": user_id, "hours": hours}
        )
        logger.debug("Got posts from DB", user_id=user_id, result=posts_result)

        posts_by_channel = posts_result.get("posts_by_channel", {})

        if not posts_by_channel or len(posts_by_channel) == 0:
            logger.warning("No posts found for user", user_id=user_id, hours=hours)
            return {"error": "no_posts"}

        # Step 2: Summarize each channel
        summaries = []
        for channel_name, posts in posts_by_channel.items():
            logger.debug(
                f"Summarizing channel {channel_name}",
                channel=channel_name,
                posts_count=len(posts),
            )
            summary_result = await client.call_tool(
                "summarize_posts",
                {"posts": posts, "channel_username": channel_name, "max_sentences": 5},
            )
            summaries.append(summary_result)

        # Step 3: Format as markdown
        metadata = {
            "generation_date": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "channels_count": len(summaries),
            "total_posts": posts_result.get("total_posts", 0),
        }
        markdown_result = await client.call_tool(
            "format_digest_markdown", {"summaries": summaries, "metadata": metadata}
        )

        # Step 4: Combine sections
        combined_result = await client.call_tool(
            "combine_markdown_sections",
            {"sections": [markdown_result.get("markdown", "")]},
        )

        # Step 5: Convert to PDF
        pdf_result = await client.call_tool(
            "convert_markdown_to_pdf",
            {
                "markdown": combined_result.get("combined_markdown", ""),
                "metadata": metadata,
            },
        )

        if "error" in pdf_result:
            logger.error(
                "PDF generation failed", user_id=user_id, error=pdf_result.get("error")
            )
            return {"error": "pdf_generation_failed"}

        return pdf_result
    except Exception as e:
        logger.error(
            "Error generating PDF digest", user_id=user_id, error=str(e), exc_info=True
        )
        return {"error": "generation_failed"}


@router.callback_query(F.data == "menu:summary")
async def callback_summary(call: CallbackQuery) -> None:
    """Show summary guidance aligned with digest-first scope."""
    await call.answer()
    keyboard = build_back_button()
    await call.message.edit_text(
        (
            "📊 Summaries now rely on digest history.\n\n"
            "• Use CLI `digest last` for detailed metadata.\n"
            "• Request a fresh digest via the menu if needed."
        ),
        reply_markup=keyboard.as_markup(),
    )


@router.callback_query(F.data == "menu:digest")
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
            await call.message.bot.send_chat_action(
                call.message.chat.id, ChatAction.UPLOAD_DOCUMENT
            )
    except Exception:
        pass  # Ignore errors in chat action

    try:
        client = get_mcp_client()
        logger.debug("MCPClient created", user_id=user_id)
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
        logger.info("Generating PDF digest", user_id=user_id, hours=24)
        pdf_result = await _generate_pdf_digest(client, user_id, hours=24)
        logger.debug("PDF digest result", user_id=user_id, result=pdf_result)

        if pdf_result.get("error") == "no_posts":
            await call.message.answer("📰 No new posts in last 24 hours.")
            return

        if "error" in pdf_result:
            # Fallback to text digest - show all channels, not just one
            error_type = pdf_result.get("error", "unknown")
            bot_digest_errors_total.labels(error_type=error_type).inc()
            logger.warning(
                "PDF generation failed, falling back to text digest", user_id=user_id
            )
            result = await client.call_tool(
                "get_channel_digest", {"user_id": int(user_id), "hours": 24}
            )
            digests = result.get("digests", [])
            if not digests:
                await call.message.answer("📰 No digests available yet.")
                return

            # Format all channels into a single message
            digest_parts = ["📰 Digest за последние 24 часа:\n"]
            for digest in digests:
                channel_name = digest.get("channel", "Unknown")
                summary = digest.get("summary", "")
                post_count = digest.get("post_count", 0)
                digest_parts.append(
                    f"\n📌 {channel_name} ({post_count} постов):\n{summary}"
                )

            full_digest = "\n".join(digest_parts)
            # Telegram limit is 4096 characters, split if needed
            if len(full_digest) > 4000:
                # Send first part
                await call.message.answer(full_digest[:4000])
                # Send remaining parts
                remaining = full_digest[4000:]
                while remaining:
                    await call.message.answer(remaining[:4000])
                    remaining = remaining[4000:]
            else:
                await call.message.answer(full_digest)
            return

        # Decode PDF bytes and send
        pdf_bytes_b64 = pdf_result.get("pdf_bytes", "")
        if not pdf_bytes_b64:
            bot_digest_errors_total.labels(error_type="empty_pdf").inc()
            await call.message.answer(
                "⚠️ Failed to generate PDF. Please try again later."
            )
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
        logger.error(
            "Error in callback_digest", user_id=user_id, error=str(e), exc_info=True
        )
        await call.message.answer("⚠️ Failed to fetch digest. Please try again later.")
