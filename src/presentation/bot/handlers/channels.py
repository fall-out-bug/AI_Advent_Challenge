"""Channel subscription handlers."""

from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from src.presentation.mcp.client import get_mcp_client
from src.infrastructure.logging import get_logger

logger = get_logger("butler_bot.channels")

MAX_ITEMS_PER_PAGE = 10

router = Router()
_mcp = get_mcp_client()


def build_channels_menu() -> InlineKeyboardBuilder:
    """Build channels submenu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Subscribe", callback_data="channels:add")
    builder.button(text="📋 List Channels", callback_data="channels:list")
    builder.button(text="🔙 Back", callback_data="menu:main")
    builder.adjust(2, 1)
    return builder


@router.callback_query(F.data == "channels:list")
async def callback_list_channels(callback: CallbackQuery) -> None:
    """List subscribed channels."""
    user_id = callback.from_user.id
    try:
        channels_res = await _mcp.call_tool("list_channels", {"user_id": user_id, "limit": MAX_ITEMS_PER_PAGE})
        channels = channels_res.get("channels", [])

        if not channels:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 Back", callback_data="menu:channels")
            await callback.message.edit_text("No subscribed channels.", reply_markup=keyboard.as_markup())
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()
        for channel in channels:
            username = channel.get("channel_username", "unknown")
            builder.button(text=f"📌 {username}", callback_data=f"channel:detail:{channel.get('id')}")

        builder.button(text="🔙 Back", callback_data="menu:channels")
        builder.adjust(1)

        text = f"📋 Subscribed Channels ({len(channels)}):"
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
    except Exception as e:
        logger.error("Failed to list channels", user_id=user_id, error=str(e))
        await callback.answer("❌ Failed to load channels. Please try again.", show_alert=True)


@router.callback_query(F.data == "channels:add")
async def callback_channel_add(callback: CallbackQuery) -> None:
    """Prompt user to add channel subscription."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Back", callback_data="menu:channels")
    await callback.message.edit_text(
        "Please send the channel username (without @).\nExample: tech_news",
        reply_markup=keyboard.as_markup(),
    )
    await callback.answer()


@router.message(F.text.regexp(r"^[a-zA-Z0-9_]+$"))
async def handle_channel_subscribe(message: Message) -> None:
    """Handle channel subscription from natural text input."""
    user_id = message.from_user.id
    channel_username = message.text.strip()
    
    try:
        result = await _mcp.call_tool("add_channel", {"user_id": user_id, "channel_username": channel_username})
        status = result.get("status", "unknown")
        if status == "subscribed":
            await message.answer(f"✅ Subscribed to @{channel_username}")
        elif status == "already_subscribed":
            await message.answer(f"ℹ️ Already subscribed to @{channel_username}")
        else:
            await message.answer(f"❌ Failed to subscribe to @{channel_username}")
    except Exception as e:
        logger.error("Failed to subscribe to channel", user_id=user_id, channel=channel_username, error=str(e))
        await message.answer(f"❌ Failed to subscribe to @{channel_username}. Please try again.")


@router.callback_query(F.data.startswith("channel:detail:"))
async def callback_channel_detail(callback: CallbackQuery) -> None:
    """Show channel detail with unsubscribe option."""
    channel_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    try:
        channels_res = await _mcp.call_tool("list_channels", {"user_id": user_id, "limit": 100})
        channel = next((c for c in channels_res.get("channels", []) if c.get("id") == channel_id), None)

        if not channel:
            await callback.answer("Channel not found", show_alert=True)
            return

        username = channel.get("channel_username", "unknown")
        text = f"📌 *{username}*\n\n"
        if channel.get("tags"):
            tags = ", ".join(channel.get("tags", []))
            text += f"🏷 Tags: {tags}\n"

        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 Unsubscribe", callback_data=f"channel:unsubscribe:{channel_id}")
        builder.button(text="🔙 Back", callback_data="channels:list")
        builder.adjust(1)

        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error("Failed to show channel detail", user_id=user_id, channel_id=channel_id, error=str(e))
        await callback.answer("❌ Failed to load channel. Please try again.", show_alert=True)


@router.callback_query(F.data.startswith("channel:unsubscribe:"))
async def callback_channel_unsubscribe(callback: CallbackQuery) -> None:
    """Unsubscribe from a channel."""
    channel_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    try:
        result = await _mcp.call_tool("delete_channel", {"user_id": user_id, "channel_id": channel_id})
        status = result.get("status")
        if status == "deleted":
            await callback.answer("Unsubscribed ✅", show_alert=True)
            await callback_list_channels(callback)
        else:
            await callback.answer("❌ Failed to unsubscribe", show_alert=True)
    except Exception as e:
        logger.error("Failed to unsubscribe from channel", user_id=user_id, channel_id=channel_id, error=str(e))
        await callback.answer("❌ Failed to unsubscribe", show_alert=True)

