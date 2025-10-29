"""Main menu handlers for bot navigation."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

