"""Channel subscription handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.infrastructure.logging import get_logger
from src.presentation.bot.states import ChannelSearchStates
from src.presentation.mcp.client import get_mcp_client

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
        channels_res = await _mcp.call_tool(
            "list_channels", {"user_id": user_id, "limit": MAX_ITEMS_PER_PAGE}
        )
        channels = channels_res.get("channels", [])

        if not channels:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 Back", callback_data="menu:channels")
            await callback.message.edit_text(
                "No subscribed channels.", reply_markup=keyboard.as_markup()
            )
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()
        for channel in channels:
            username = channel.get("channel_username", "unknown")
            builder.button(
                text=f"📌 {username}",
                callback_data=f"channel:detail:{channel.get('id')}",
            )

        builder.button(text="🔙 Back", callback_data="menu:channels")
        builder.adjust(1)

        text = f"📋 Subscribed Channels ({len(channels)}):"
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
    except Exception as e:
        logger.error("Failed to list channels", user_id=user_id, error=str(e))
        await callback.answer(
            "❌ Failed to load channels. Please try again.", show_alert=True
        )


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


@router.message(ChannelSearchStates.waiting_confirmation)
async def handle_channel_search_confirmation(
    message: Message, state: FSMContext
) -> None:
    """Handle user confirmation of found channel (Yes/No) with candidate cycling.

    Purpose:
        Process user's confirmation (да/yes/нет/no) for a found channel.
        On decline, cycle to next candidate if available.

    Args:
        message: Telegram message with confirmation
        state: FSM context with channel search data
    """
    message.from_user.id
    text = message.text.strip().lower()

    # Parse confirmation (да/yes/нет/no)
    is_confirmed = text in ("да", "yes", "y", "давай", "ок", "ok")

    if not is_confirmed and text not in ("нет", "no", "n", "отмена", "cancel"):
        await message.answer("Пожалуйста, ответьте 'да' или 'нет'")
        return

    # Get data from state
    data = await state.get_data()
    candidates = data.get("candidates", [])
    cycler_index = data.get("cycler_index", 0)

    # If declined, try next candidate
    if not is_confirmed:
        # Check if there are more candidates
        if candidates and cycler_index < len(candidates) - 1:
            # Advance to next candidate
            next_index = cycler_index + 1
            next_candidate = candidates[next_index]

            await state.update_data(
                {
                    "cycler_index": next_index,
                    "found_channel": {
                        "username": next_candidate["username"],
                        "title": next_candidate["title"],
                    },
                }
            )

            await message.answer(
                f"🔍 Найден канал: {next_candidate['title']} (@{next_candidate['username']})\n\n"
                f"Подписаться на него? (да/нет)"
            )
            return
        else:
            # No more candidates, cancel search
            await state.clear()
            await message.answer("❌ Канал не найден. Попробуйте уточнить название.")
            return

    # Get channel data from state
    data = await state.get_data()
    found_channel = data.get("found_channel")
    original_input = data.get("original_input", "")

    if not found_channel:
        await state.clear()
        await message.answer("❌ Ошибка: данные о канале не найдены.")
        return

    channel_username = found_channel.get("username")
    channel_title = found_channel.get("title", channel_username)

    # Check if user provided exact username match - if so, subscribe directly
    normalized_input = original_input.lstrip("@").lower().strip()
    normalized_username = channel_username.lower().strip()
    is_exact_match = normalized_input == normalized_username

    from src.infrastructure.logging import get_logger

    logger = get_logger("channels")
    logger.info(
        f"Confirmation received: input='{original_input}', "
        f"found_username='{channel_username}', is_exact_match={is_exact_match}"
    )

    # If exact match, subscribe directly without asking for action choice
    if is_exact_match:
        logger.info(
            f"Exact username match in confirmation, subscribing directly: "
            f"user_id={message.from_user.id}, channel={channel_username}"
        )
        await _handle_subscribe_action(
            user_id=message.from_user.id,
            channel_username=channel_username,
            state=state,
            message=message,
        )
        return

    # Ask for action choice (subscribe or subscribe-and-digest)
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="✅ Подписаться", callback_data=f"channel:subscribe:{channel_username}"
    )
    keyboard.button(
        text="📄 Подписаться и сделать дайджест",
        callback_data=f"channel:subscribe_and_digest:{channel_username}",
    )
    keyboard.button(text="❌ Отмена", callback_data="channel:search_cancel")
    keyboard.adjust(1, 1, 1)

    await message.answer(
        f"Найден канал: @{channel_username} - {channel_title}\n\n"
        f"Что вы хотите сделать?",
        reply_markup=keyboard.as_markup(),
    )

    await state.set_state(ChannelSearchStates.waiting_action_choice)


@router.message(ChannelSearchStates.waiting_action_choice)
async def handle_channel_action_choice(message: Message, state: FSMContext) -> None:
    """Handle user action choice (subscribe/subscribe-and-digest) via text.

    Purpose:
        Process user's text response for action choice.

    Args:
        message: Telegram message with action choice
        state: FSM context
    """
    # Action choice is primarily handled via callback buttons,
    # but we can handle text input as fallback
    text = message.text.strip().lower()

    if "подписа" in text or "subscribe" in text:
        # Extract channel from state
        data = await state.get_data()
        found_channel = data.get("found_channel")
        if found_channel:
            channel_username = found_channel.get("username")
            # Trigger subscription
            await _handle_subscribe_action(
                message.from_user.id, channel_username, state, message
            )
        else:
            await message.answer("❌ Ошибка: данные о канале не найдены.")
            await state.clear()
    elif "дайджест" in text or "digest" in text:
        # Extract channel from state
        data = await state.get_data()
        found_channel = data.get("found_channel")
        if found_channel:
            channel_username = found_channel.get("username")
            # Trigger subscribe-and-digest action
            await _handle_subscribe_and_digest_action(
                message.from_user.id, channel_username, state, message
            )
        else:
            await message.answer("❌ Ошибка: данные о канале не найдены.")
            await state.clear()
    else:
        await message.answer(
            "Пожалуйста, выберите действие кнопками или напишите 'подписаться' или 'подписаться и сделать дайджест'"
        )


@router.callback_query(F.data.startswith("channel:subscribe:"))
async def callback_subscribe_channel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Handle subscribe action from callback button."""
    channel_username = callback.data.split(":")[-1]
    await _handle_subscribe_action(
        callback.from_user.id, channel_username, state, callback.message
    )
    await callback.answer()


@router.callback_query(F.data.startswith("channel:subscribe_and_digest:"))
async def callback_subscribe_and_digest(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Handle subscribe-and-digest action from callback button."""
    channel_username = callback.data.split(":")[-1]
    await _handle_subscribe_and_digest_action(
        callback.from_user.id, channel_username, state, callback.message
    )
    await callback.answer()


@router.callback_query(F.data == "channel:search_cancel")
async def callback_search_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle search cancellation."""
    await state.clear()
    await callback.message.edit_text("Поиск отменен.")
    await callback.answer()


async def _handle_subscribe_action(
    user_id: int,
    channel_username: str,
    state: FSMContext,
    message: Message | None = None,
) -> None:
    """Handle subscribe action with immediate post collection.

    Purpose:
        Subscribe user to channel, collect posts immediately, and clear FSM state.
        Uses SubscribeToChannelWithCollectionUseCase for subscription + collection.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username
        state: FSM context
        message: Optional message object (if not provided, will try to get from state)
    """
    try:
        # Get message from state if not provided
        if message is None:
            data = await state.get_data()
            message = data.get("original_message") or data.get("message")

        # Use SubscribeToChannelWithCollectionUseCase for subscription + collection
        from src.application.use_cases.subscribe_with_collection import (
            SubscribeToChannelWithCollectionUseCase,
        )

        use_case = SubscribeToChannelWithCollectionUseCase(mcp_client=_mcp)
        result = await use_case.execute(
            user_id=user_id,
            channel_username=channel_username,
            hours=72,
            fallback_to_7_days=True,
        )

        status = result.status

        if status == "subscribed":
            collection_msg = ""
            if result.collected_count > 0:
                collection_msg = f"\n\n📥 Собрано постов: {result.collected_count}"
            elif result.error:
                collection_msg = "\n\n⚠️ Посты собираются в фоне"

            if message:
                await message.answer(
                    f"✅ Подписался на @{channel_username}{collection_msg}"
                )
            await state.clear()
        elif status == "already_subscribed":
            if message:
                await message.answer(f"ℹ️ Уже подписан на @{channel_username}")
            await state.clear()
        else:
            error_msg = result.error or "Неизвестная ошибка"
            if message:
                await message.answer(
                    f"❌ Не удалось подписаться на @{channel_username}\n\n{error_msg}"
                )
            await state.clear()
    except Exception as e:
        error_msg = str(e)
        # Extract more detailed error message if available
        if "MCP tool" in error_msg:
            # Try to extract the actual error from the message
            if ":" in error_msg:
                error_msg = error_msg.split(":", 1)[-1].strip()

        logger.error(
            f"Error subscribing to channel: user_id={user_id}, "
            f"channel={channel_username}, error={e}",
            exc_info=True,
        )
        if message is None:
            data = await state.get_data()
            message = data.get("original_message") or data.get("message")
        if message:
            await message.answer(
                f"❌ Не удалось подписаться на @{channel_username}\n\n"
                f"Ошибка: {error_msg}"
            )
        await state.clear()


async def _handle_subscribe_and_digest_action(
    user_id: int,
    channel_username: str,
    state: FSMContext,
    message: Message | None = None,
) -> None:
    """Handle subscribe-and-digest action.

    Purpose:
        Subscribe to channel, collect posts, and generate digest in one flow.
        Uses SubscribeAndGenerateDigestUseCase.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username
        state: FSM context
        message: Optional message object (if not provided, will try to get from state)
    """
    # Get message from state if not provided
    if message is None:
        data = await state.get_data()
        message = data.get("original_message") or data.get("message")

    try:
        # Use SubscribeAndGenerateDigestUseCase
        from src.application.use_cases.subscribe_and_generate_digest import (
            SubscribeAndGenerateDigestUseCase,
        )

        use_case = SubscribeAndGenerateDigestUseCase(mcp_client=_mcp)
        result = await use_case.execute(
            user_id=user_id,
            channel_username=channel_username,
            hours=72,
        )

        if result.status == "success":
            collection_msg = ""
            if result.collected_count > 0:
                collection_msg = f"\n\n📥 Собрано постов: {result.collected_count}"

            if result.summary and message:
                await message.answer(
                    f"✅ Подписался на @{channel_username}{collection_msg}\n\n"
                    f"📄 Дайджест:\n\n{result.summary}"
                )
            elif message:
                await message.answer(
                    f"✅ Подписался на @{channel_username}{collection_msg}\n\n"
                    f"{result.summary or 'Постов не найдено, попробуйте позже.'}"
                )
            await state.clear()
        else:
            error_msg = result.error or "Неизвестная ошибка"
            if message:
                await message.answer(
                    f"❌ Не удалось подписаться и получить дайджест по @{channel_username}\n\n{error_msg}"
                )
            await state.clear()
    except Exception as e:
        logger.error(
            f"Error in subscribe and digest: user_id={user_id}, "
            f"channel={channel_username}, error={e}",
            exc_info=True,
        )
        if message is None:
            data = await state.get_data()
            message = data.get("original_message") or data.get("message")
        if message:
            await message.answer("❌ Ошибка при генерации дайджеста")
        await state.clear()


@router.message(F.text.regexp(r"^[a-zA-Z0-9_]+$"))
async def handle_channel_subscribe(message: Message) -> None:
    """Handle channel subscription from natural text input."""
    user_id = message.from_user.id
    channel_username = message.text.strip()

    try:
        result = await _mcp.call_tool(
            "add_channel", {"user_id": user_id, "channel_username": channel_username}
        )
        status = result.get("status", "unknown")
        if status == "subscribed":
            await message.answer(f"✅ Subscribed to @{channel_username}")
        elif status == "already_subscribed":
            await message.answer(f"ℹ️ Already subscribed to @{channel_username}")
        else:
            await message.answer(f"❌ Failed to subscribe to @{channel_username}")
    except Exception as e:
        logger.error(
            "Failed to subscribe to channel",
            user_id=user_id,
            channel=channel_username,
            error=str(e),
        )
        await message.answer(
            f"❌ Failed to subscribe to @{channel_username}. Please try again."
        )


@router.callback_query(F.data.startswith("channel:detail:"))
async def callback_channel_detail(callback: CallbackQuery) -> None:
    """Show channel detail with unsubscribe option."""
    channel_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    try:
        channels_res = await _mcp.call_tool(
            "list_channels", {"user_id": user_id, "limit": 100}
        )
        channel = next(
            (c for c in channels_res.get("channels", []) if c.get("id") == channel_id),
            None,
        )

        if not channel:
            await callback.answer("Channel not found", show_alert=True)
            return

        username = channel.get("channel_username", "unknown")
        # Use title if available, fallback to username
        channel_title = channel.get("title") or username
        text = f"📌 *{channel_title}*\n\n"
        if channel.get("tags"):
            tags = ", ".join(channel.get("tags", []))
            text += f"🏷 Tags: {tags}\n"

        builder = InlineKeyboardBuilder()
        builder.button(
            text="🗑 Unsubscribe", callback_data=f"channel:unsubscribe:{channel_id}"
        )
        builder.button(text="🔙 Back", callback_data="channels:list")
        builder.adjust(1)

        await callback.message.edit_text(
            text, reply_markup=builder.as_markup(), parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(
            "Failed to show channel detail",
            user_id=user_id,
            channel_id=channel_id,
            error=str(e),
        )
        await callback.answer(
            "❌ Failed to load channel. Please try again.", show_alert=True
        )


@router.callback_query(F.data.startswith("channel:unsubscribe:"))
async def callback_channel_unsubscribe(callback: CallbackQuery) -> None:
    """Unsubscribe from a channel."""
    channel_id = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    try:
        result = await _mcp.call_tool(
            "delete_channel", {"user_id": user_id, "channel_id": channel_id}
        )
        status = result.get("status")
        if status == "deleted":
            await callback.answer("Unsubscribed ✅", show_alert=True)
            await callback_list_channels(callback)
        else:
            await callback.answer("❌ Failed to unsubscribe", show_alert=True)
    except Exception as e:
        logger.error(
            "Failed to unsubscribe from channel",
            user_id=user_id,
            channel_id=channel_id,
            error=str(e),
        )
        await callback.answer("❌ Failed to unsubscribe", show_alert=True)
