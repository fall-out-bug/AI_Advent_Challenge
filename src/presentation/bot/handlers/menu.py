"""Main menu handlers for bot navigation."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.presentation.mcp.client import MCPClient

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


@menu_router.callback_query(F.data == "menu:digest")
async def callback_digest(call: CallbackQuery) -> None:
    """Show a channel digest via MCP tools with basic error handling."""
    await call.answer()
    user_id = call.from_user.id if call.from_user else 0
    try:
        client = MCPClient()
        result = await client.call_tool("get_channel_digest", {"user_id": int(user_id), "hours": 24})
        digests = result.get("digests", [])
        if not digests:
            await call.message.answer("📰 No digests available yet.")
            return
        top = digests[0]
        await call.message.answer(f"📰 {top.get('channel', 'channel')}: {top.get('summary', '')}")
    except Exception:
        await call.message.answer("⚠️ Failed to fetch digest. Please try again later.")

