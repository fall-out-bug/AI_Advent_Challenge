"""Butler handler for Telegram bot using ButlerOrchestrator.

Following Clean Architecture: Presentation layer delegates to domain layer.
Following Python Zen: Simple is better than complex.
"""

import asyncio
import base64
import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import Any
else:
    Any = object

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from src.application.use_cases.resolve_channel_name import ResolveChannelNameUseCase
from src.application.use_cases.search_channel_for_subscription import (
    SearchChannelForSubscriptionUseCase,
)
from src.application.dtos.butler_dialog_dtos import DialogMode
from src.presentation.bot.orchestrator import ButlerOrchestrator
from src.infrastructure.logging import get_logger
from src.presentation.bot.states import ChannelSearchStates

logger = get_logger("butler_handler")

# Global orchestrator instance (set by setup_butler_handler)
_orchestrator: Optional[ButlerOrchestrator] = None
# Global personalized reply use case (set by setup_butler_handler)
_personalized_reply_use_case: Optional[Any] = None


def setup_butler_handler(
    orchestrator: ButlerOrchestrator,
    personalized_reply_use_case: Optional[Any] = None,
) -> Router:
    """Setup butler handler with orchestrator dependency.

    Purpose:
        Configure router with orchestrator dependency for handler functions.

    Args:
        orchestrator: ButlerOrchestrator instance for message processing
        personalized_reply_use_case: Optional PersonalizedReplyUseCase for personalization

    Returns:
        Configured aiogram Router

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> router = setup_butler_handler(orchestrator, personalized_reply_use_case)
        >>> dp.include_router(router)
    """
    global _orchestrator, _personalized_reply_use_case
    _orchestrator = orchestrator
    _personalized_reply_use_case = personalized_reply_use_case

    router = Router()
    # Register handler - FSMContext will be automatically injected by aiogram if available
    router.message.register(handle_any_message, F.text)
    return router


async def handle_any_message(message: Message, state: FSMContext | None = None) -> None:
    """Handle any text message using ButlerOrchestrator.

    Purpose:
        Main entry point for processing user messages through ButlerOrchestrator.
        Extracts user_id and message text, delegates to orchestrator,
        and sends formatted response.

    Args:
        message: Telegram message object
        state: Optional FSM context for state management

    Example:
        >>> await handle_any_message(message, state)
    """
    if not message.text or not message.from_user:
        logger.warning("Received message without text or user")
        return

    if _orchestrator is None:
        logger.error("ButlerOrchestrator not initialized")
        await _handle_error(message, RuntimeError("Orchestrator not initialized"))
        return

    user_id = str(message.from_user.id)
    session_id = f"telegram_{user_id}_{message.message_id}"
    text = message.text

    logger.info(
        f"Processing message: user_id={user_id}, message_id={message.message_id}, text_preview={text[:50]}",
        extra={"user_id": user_id, "message_id": message.message_id},
    )

    try:
        # Check if personalization is enabled and message is not a special command
        # Only route through personalization for regular text messages
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()
        is_special_command = (
            _is_list_channels_request(text)
            or _is_unsubscribe_request(text)[0]
            or _is_subscribe_request(text)[0]
            or _extract_digest_request_info(text)[0] is not None
            or _extract_commit_hash(text) is not None
            or _is_review_command(text)
        )

        if (
            settings.personalization_enabled
            and _personalized_reply_use_case is not None
            and not is_special_command
        ):
            logger.info(
                "Routing through personalized reply",
                extra={"user_id": user_id, "text_preview": text[:50]},
            )

            try:
                from src.application.personalization.dtos import (
                    PersonalizedReplyInput,
                )

                input_data = PersonalizedReplyInput(
                    user_id=user_id, text=text, source="text"
                )

                output = await _personalized_reply_use_case.execute(input_data)

                await _safe_answer(message, output.reply)

                logger.info(
                    "Personalized reply sent",
                    extra={
                        "user_id": user_id,
                        "used_persona": output.used_persona,
                        "memory_events_used": output.memory_events_used,
                        "compressed": output.compressed,
                    },
                )
                return

            except Exception as e:
                logger.error(
                    "Personalized reply failed, falling back to Butler",
                    extra={"user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                # Fall through to Butler fallback

        # Check for list channels request
        if _is_list_channels_request(text):
            logger.info(
                f"Intent detected: list_channels for user_id={user_id}",
                extra={"user_id": user_id, "intent": "list_channels"},
            )
            await _handle_list_channels(message, int(user_id))
            return

        # Check for unsubscribe request
        is_unsubscribe, unsubscribe_channel = _is_unsubscribe_request(text)
        if is_unsubscribe and unsubscribe_channel:
            logger.info(
                f"Intent detected: unsubscribe, channel='{unsubscribe_channel}', user_id={user_id}",
                extra={
                    "user_id": user_id,
                    "intent": "unsubscribe",
                    "channel_input": unsubscribe_channel,
                },
            )
            await _handle_unsubscribe_request(
                message, int(user_id), unsubscribe_channel.strip()
            )
            return

        # Check for subscribe request
        is_subscribe, subscribe_channel = _is_subscribe_request(text)
        if is_subscribe and subscribe_channel:
            logger.info(
                f"Intent detected: subscribe, channel='{subscribe_channel}', user_id={user_id}",
                extra={
                    "user_id": user_id,
                    "intent": "subscribe",
                    "channel_input": subscribe_channel,
                },
            )
            # Ensure we pass the full channel name (might contain spaces)
            await _handle_subscribe_request(
                message, int(user_id), subscribe_channel.strip(), state
            )
            return

        # Check if message contains digest request with channel name
        # For better accuracy with multi-word names and Russian declensions, prefer LLM parsing when:
        # 1. Request contains "канала" or "канал" (indicates multi-word name likely)
        # 2. Request contains "дайджест" + "по" (indicates channel name in different case/declension)
        # 3. Request contains "передай" or "передать"
        # 4. Request contains "есть ли" + "дайджест" (natural language query)
        text_lower = text.lower()
        use_llm_first = (
            "канала" in text_lower
            or "канал" in text_lower
            or "передай" in text_lower
            or "передать" in text_lower
            or ("дайджест" in text_lower and "по" in text_lower)
            or ("есть" in text_lower and "дайджест" in text_lower)
            or ("дайджет" in text_lower and "по" in text_lower)
        )

        if use_llm_first:
            # Use LLM first for better multi-word name extraction
            logger.debug(
                f"Using LLM parsing first for multi-word name extraction: {text[:50]}"
            )
            channel_name, hours = await _parse_digest_request_with_llm(text)
            # Fallback to regex if LLM fails
            if not channel_name:
                channel_name, hours = _extract_digest_request_info(text)
        else:
            # Try regex first (fast)
            channel_name, hours = _extract_digest_request_info(text)

            # If regex failed, try LLM parsing
            if not channel_name:
                logger.debug(
                    f"Regex parsing failed, trying LLM parsing for: {text[:50]}"
                )
                channel_name, hours = await _parse_digest_request_with_llm(text)
            elif channel_name:
                # Check if regex extracted name is in a declension (Russian case)
                # If so, use LLM to restore nominative case
                name_lower = channel_name.lower()
                # Common Russian declension endings that indicate non-nominative case
                declension_endings = ["е", "и", "ы", "а", "у", "ой", "ей", "ом", "ем", "ах", "ях"]
                # Check if name ends with declension ending (but not if it's a common username pattern)
                is_declension = any(
                    name_lower.endswith(ending) and len(name_lower) > len(ending)
                    for ending in declension_endings
                ) and not name_lower.endswith(("канал", "канала", "канале"))
                
                # Also check if name is single word but request has more context
                is_single_word = len(channel_name.split()) == 1
                has_digest_context = any(
                    kw in text_lower for kw in ["дайджест", "дайджет", "digest", "по", "канала", "канал"]
                )
                
                if is_declension or (is_single_word and has_digest_context):
                    # Name is in declension or might need LLM parsing, use LLM to restore nominative
                    logger.debug(
                        f"Name appears to be in declension or needs LLM parsing: "
                        f"channel_name={channel_name}, is_declension={is_declension}, "
                        f"is_single_word={is_single_word}, using LLM..."
                    )
                    llm_name, llm_hours = await _parse_digest_request_with_llm(text)
                    if llm_name:
                        # Prefer LLM result if it's different (likely better)
                        if llm_name.lower() != channel_name.lower():
                            logger.info(
                                f"LLM corrected channel name: '{channel_name}' -> '{llm_name}'"
                            )
                            channel_name = llm_name
                            hours = llm_hours or hours
                        else:
                            # LLM returned same name, but might have better case
                            channel_name = llm_name
                            hours = llm_hours or hours

        if channel_name:
            # Intercept digest request and use channel resolver
            logger.info(
                f"🔍 Intercepting digest request: channel_name={channel_name}, user_id={user_id}"
            )
            try:
                use_case = ResolveChannelNameUseCase(allow_telegram_search=True)
                resolution = await use_case.execute(
                    user_id=int(user_id),
                    input_name=channel_name,
                    allow_telegram_search=True,
                )

                logger.info(
                    f"🔍 Resolution result: found={resolution.found}, "
                    f"username={resolution.channel_username}, source={resolution.source}"
                )

                if resolution.found and resolution.channel_username:
                    # Channel resolved, proceed with digest
                    logger.info(
                        f"Channel resolved: user_id={user_id}, input={channel_name}, "
                        f"resolved={resolution.channel_username}, source={resolution.source}, "
                        f"score={resolution.confidence_score:.3f}, hours={hours}"
                    )
                    # Use resolved username in the request text
                    # This ensures we use the correct username (onaboka) instead of title (Набока)
                    resolved_username = resolution.channel_username

                    # If channel found via search (not in subscriptions), try to auto-subscribe
                    # This allows digest generation for channels found via Telegram search
                    # IMPORTANT: Check source FIRST before other conditions
                    logger.info(
                        f"CHECKING_RESOLUTION_SOURCE: source={resolution.source}, "
                        f"found={resolution.found}, username={resolved_username}, "
                        f"source_type={type(resolution.source)}, source_eq_search={resolution.source == 'search'}"
                    )
                    if resolution.source == "search":
                        logger.info(
                            f"CHANNEL_FOUND_VIA_SEARCH: attempting auto-subscription: "
                            f"username={resolved_username}, title={resolution.channel_title}, user_id={user_id}"
                        )
                        try:
                            # Try to subscribe automatically for digest requests
                            from src.presentation.mcp.tools.channels.channel_management import (
                                add_channel,
                            )

                            logger.info(
                                f"CALLING_ADD_CHANNEL: user_id={user_id}, "
                                f"channel_username={resolved_username}, title={resolution.channel_title or ''}"
                            )
                            subscribe_result = await add_channel(
                                user_id=int(user_id),
                                channel_username=resolved_username,
                                title=resolution.channel_title or "",
                            )

                            logger.info(
                                f"📝 add_channel result: {subscribe_result}, "
                                f"status={subscribe_result.get('status')}"
                            )

                            if subscribe_result.get("status") in (
                                "subscribed",
                                "already_subscribed",
                            ):
                                logger.info(
                                    f"✅ Auto-subscribed to channel for digest: "
                                    f"username={resolved_username}, user_id={user_id}, "
                                    f"status={subscribe_result.get('status')}"
                                )
                                # Small delay to ensure DB write is committed
                                # Also verify subscription was saved
                                await asyncio.sleep(1.0)  # Increased delay for MongoDB write
                                
                                # Verify subscription was saved
                                try:
                                    from src.presentation.mcp.tools.channels.channel_management import (
                                        list_channels,
                                    )
                                    verify_result = await list_channels(
                                        user_id=int(user_id)
                                    )
                                    channels = verify_result.get("channels", []) if isinstance(verify_result, dict) else []
                                    found = any(
                                        ch.get("channel_username", "").lower() == resolved_username.lower()
                                        for ch in channels
                                    )
                                    if found:
                                        logger.info(
                                            f"✅ Verified subscription saved: username={resolved_username}"
                                        )
                                        
                                        # Start automatic post collection for the new channel
                                        try:
                                            from src.presentation.mcp.tools.channels.posts_management import (
                                                collect_posts,
                                            )
                                            logger.info(
                                                f"🔄 Starting automatic post collection for channel: {resolved_username}"
                                            )
                                            collect_result = await collect_posts(
                                                channel_username=resolved_username,
                                                user_id=int(user_id),
                                                hours=168,  # Collect posts from last 7 days
                                                wait_for_completion=True,  # Wait for collection to finish
                                                timeout_seconds=60,  # Allow up to 60 seconds for collection
                                            )
                                            collected_count = collect_result.get("collected_count", 0)
                                            if collected_count > 0:
                                                logger.info(
                                                    f"✅ Collected {collected_count} posts for channel {resolved_username}"
                                                )
                                            else:
                                                logger.info(
                                                    f"ℹ️ No new posts collected for channel {resolved_username} (may be empty or already collected)"
                                                )
                                        except Exception as collect_error:
                                            logger.warning(
                                                f"Failed to start post collection: {collect_error}",
                                                exc_info=True,
                                            )
                                            # Continue anyway - posts will be collected later
                                    else:
                                        logger.warning(
                                            f"⚠️ Subscription not found after save: username={resolved_username}, "
                                            f"channels={[ch.get('channel_username') for ch in channels[:5]]}"
                                        )
                                except Exception as verify_error:
                                    logger.warning(
                                        f"Failed to verify subscription: {verify_error}",
                                        exc_info=True,
                                    )
                            else:
                                logger.warning(
                                    f"⚠️ Auto-subscription failed: status={subscribe_result.get('status')}, "
                                    f"result={subscribe_result}"
                                )
                                # Continue anyway - MCP tool will handle not_subscribed case
                        except Exception as e:
                            logger.error(
                                f"❌ Failed to auto-subscribe channel: {e}",
                                exc_info=True,
                                extra={
                                    "user_id": user_id,
                                    "channel_username": resolved_username,
                                    "error": str(e),
                                },
                            )
                            # Continue anyway - MCP tool will handle not_subscribed case

                    # After auto-subscription (if needed), proceed with digest
                    # Replace channel name in text with resolved username
                    # Also handle case where channel_name might be in different case or declension
                    text = text.replace(channel_name, resolved_username)
                    # Also replace common variations
                    text = text.replace(channel_name.lower(), resolved_username)
                    text = text.replace(channel_name.upper(), resolved_username)

                    # Add hours parameter if extracted
                    if hours:
                        # Format request with resolved username and hours
                        days = hours // 24
                        text = f"дайджест по {resolved_username} за {days} дней"
                    else:
                        # Just ensure resolved username is used
                        text = f"дайджест по {resolved_username}"
                    
                    # Check if posts exist for this channel, and collect if missing
                    # This handles cases where channel is subscribed but posts haven't been collected yet
                    logger.info(
                        f"🔍 Checking posts for channel {resolved_username} before digest generation..."
                    )
                    try:
                        from src.presentation.mcp.tools.channels.posts_management import (
                            get_posts,
                        )
                        # Quick check: are there any posts in the last 7 days?
                        logger.info(
                            f"📊 Calling get_posts for {resolved_username}, hours=168..."
                        )
                        posts_check = await get_posts(
                            channel_username=resolved_username,
                            hours=168,  # 7 days
                            user_id=int(user_id),
                        )
                        logger.info(
                            f"📊 get_posts result: {posts_check}, type={type(posts_check)}"
                        )
                        posts_count = posts_check.get("posts_count", 0) if isinstance(posts_check, dict) else 0
                        logger.info(
                            f"📊 Posts count for {resolved_username}: {posts_count}"
                        )
                        
                        if posts_count == 0:
                            logger.info(
                                f"⚠️ No posts found for channel {resolved_username}, "
                                f"starting automatic collection..."
                            )
                            # Collect posts automatically
                            from src.presentation.mcp.tools.channels.posts_management import (
                                collect_posts,
                            )
                            logger.info(
                                f"🔄 Calling collect_posts for {resolved_username}..."
                            )
                            collect_result = await collect_posts(
                                channel_username=resolved_username,
                                user_id=int(user_id),
                                hours=168,  # Collect posts from last 7 days
                                wait_for_completion=True,
                                timeout_seconds=60,
                            )
                            logger.info(
                                f"🔄 collect_posts result: {collect_result}, type={type(collect_result)}"
                            )
                            collected_count = collect_result.get("collected_count", 0) if isinstance(collect_result, dict) else 0
                            if collected_count > 0:
                                logger.info(
                                    f"✅ Collected {collected_count} posts for channel {resolved_username}"
                                )
                            else:
                                logger.info(
                                    f"ℹ️ No new posts collected for channel {resolved_username} "
                                    f"(channel may be empty or posts already collected). "
                                    f"Result status: {collect_result.get('status') if isinstance(collect_result, dict) else 'unknown'}"
                                )
                        else:
                            logger.info(
                                f"✅ Found {posts_count} existing posts for channel {resolved_username}"
                            )
                    except Exception as collect_error:
                        logger.error(
                            f"❌ Failed to check/collect posts: {collect_error}",
                            exc_info=True,
                            extra={
                                "user_id": user_id,
                                "channel_username": resolved_username,
                                "error_type": type(collect_error).__name__,
                                "error": str(collect_error),
                            },
                        )
                        # Continue anyway - digest generation will handle empty posts
                    
                    # Log that we're proceeding to orchestrator after auto-subscription
                    logger.info(
                        f"✅ Proceeding to orchestrator after channel resolution: "
                        f"username={resolved_username}, source={resolution.source}"
                    )
                elif not resolution.found and resolution.source == "subscription":
                    # Channel not found in subscriptions, try LLM search in metadata
                    logger.info(
                        f"Channel not found in subscriptions: input={channel_name}, "
                        f"top_score={resolution.confidence_score:.3f}, user_id={user_id}. "
                        f"Trying LLM search in metadata..."
                    )
                    
                    # Try to find channel using LLM in user's subscription metadata
                    llm_resolution = await _find_channel_in_metadata_with_llm(
                        user_id=int(user_id),
                        user_query=text,
                        channel_name=channel_name,
                    )
                    
                    if llm_resolution and llm_resolution.get("found"):
                        # LLM found the channel in metadata
                        resolved_username = llm_resolution.get("channel_username")
                        resolved_title = llm_resolution.get("channel_title")
                        logger.info(
                            f"✅ LLM found channel in metadata: "
                            f"input='{channel_name}' -> username='{resolved_username}', "
                            f"title='{resolved_title}', user_id={user_id}"
                        )
                        
                        # Use the found channel for digest generation
                        text = text.replace(channel_name, resolved_username)
                        text = text.replace(channel_name.lower(), resolved_username)
                        text = text.replace(channel_name.upper(), resolved_username)
                        
                        if hours:
                            days = hours // 24
                            text = f"дайджест по {resolved_username} за {days} дней"
                        else:
                            text = f"дайджест по {resolved_username}"
                        
                        logger.info(
                            f"✅ Proceeding to orchestrator after LLM metadata search: "
                            f"username={resolved_username}"
                        )
                        # Continue to orchestrator with resolved channel
                    else:
                        # LLM also didn't find the channel
                        logger.warning(
                            f"Channel not found even with LLM metadata search: "
                            f"input={channel_name}, user_id={user_id}"
                        )
                        await message.answer(
                            f"❌ Канал '{channel_name}' не найден в ваших подписках.\n\n"
                            f"Попробуйте подписаться на канал или уточните название."
                        )
                        return
                elif resolution.source == "search":
                    # Channel found via search, but we need valid username and title
                    if not resolution.channel_username or not resolution.channel_title:
                        logger.warning(
                            f"Channel search returned invalid result: "
                            f"username='{resolution.channel_username}', "
                            f"title='{resolution.channel_title}', input='{channel_name}'. "
                            f"Trying LLM search in metadata..."
                        )
                        
                        # Telegram search failed, try LLM search in subscription metadata
                        llm_resolution = await _find_channel_in_metadata_with_llm(
                            user_id=int(user_id),
                            user_query=text,
                            channel_name=channel_name,
                        )
                        
                        if llm_resolution and llm_resolution.get("found"):
                            # LLM found the channel in metadata
                            resolved_username = llm_resolution.get("channel_username")
                            resolved_title = llm_resolution.get("channel_title")
                            logger.info(
                                f"✅ LLM found channel in metadata after search failure: "
                                f"input='{channel_name}' -> username='{resolved_username}', "
                                f"title='{resolved_title}', user_id={user_id}"
                            )
                            
                            # Use the found channel for digest generation
                            text = text.replace(channel_name, resolved_username)
                            text = text.replace(channel_name.lower(), resolved_username)
                            text = text.replace(channel_name.upper(), resolved_username)
                            
                            if hours:
                                days = hours // 24
                                text = f"дайджест по {resolved_username} за {days} дней"
                            else:
                                text = f"дайджест по {resolved_username}"
                            
                            logger.info(
                                f"✅ Proceeding to orchestrator after LLM metadata search: "
                                f"username={resolved_username}"
                            )
                            # Continue to orchestrator with resolved channel
                        else:
                            # LLM also didn't find the channel
                            logger.warning(
                                f"Channel not found even with LLM metadata search: "
                                f"input={channel_name}, user_id={user_id}"
                            )
                            await message.answer(
                                f"❌ Канал '{channel_name}' не найден в подписках.\n\n"
                                f"Попробуйте подписаться на канал через команду подписки."
                            )
                            return

                    # Channel found via search, need confirmation
                    if state is None:
                        # If no FSM context, create a temporary one
                        # This should not happen in normal flow, but handle gracefully
                        logger.warning(
                            "FSM context not available for channel search confirmation"
                        )
                        await message.answer(
                            f"Найден канал: @{resolution.channel_username} - {resolution.channel_title}\n\n"
                            f"Для использования канала подпишитесь на него через /menu"
                        )
                        return

                    # Store channel data in FSM state
                    await state.update_data(
                        found_channel={
                            "username": resolution.channel_username,
                            "title": resolution.channel_title,
                        },
                        original_input=channel_name,
                        message=message,  # Store message for later use
                    )
                    await state.set_state(ChannelSearchStates.waiting_confirmation)

                    await message.answer(
                        f"Найден канал: @{resolution.channel_username} - {resolution.channel_title}\n\n"
                        f"Это правильный канал? (да/нет)"
                    )
                    return  # Don't proceed to orchestrator, wait for confirmation
            except Exception as e:
                logger.warning(
                    f"Error resolving channel: {e}, proceeding with orchestrator"
                )

        # Check if message contains commit hash - force HOMEWORK_REVIEW mode
        commit_hash = _extract_commit_hash(text)
        force_mode = None
        if commit_hash:
            force_mode = DialogMode.HOMEWORK_REVIEW
            await message.answer("⏳ Начал ревью коммита...")
        elif _is_review_command(text):
            # Also check for review keywords without hash (might be partial)
            force_mode = DialogMode.HOMEWORK_REVIEW
            await message.answer("⏳ Начал ревью коммита...")

        kwargs: dict[str, Any] = {
            "user_id": user_id,
            "message": text,
            "session_id": session_id,
        }
        if force_mode is not None:
            kwargs["force_mode"] = force_mode

        response = await _orchestrator.handle_user_message(**kwargs)
        # Check if response is a file format: "FILE:<filename>:<content>"
        if response.startswith("FILE:"):
            await _handle_file_response(message, response)
        else:
            await _safe_answer(message, response)
    except Exception as e:
        logger.error(
            f"Failed to handle message: user_id={user_id}, error={str(e)}",
            exc_info=True,
        )
        await _handle_error(message, e)


async def _safe_answer(message: Message, text: str) -> None:
    """Send response message with error handling.

    Purpose:
        Safely send Telegram message with retry logic and error handling.
        Handles message length limits and formatting.

    Args:
        message: Telegram message object
        text: Response text to send
    """
    MAX_MESSAGE_LENGTH = 4000  # Telegram limit

    try:
        if len(text) > MAX_MESSAGE_LENGTH:
            # Try to truncate at sentence boundary
            truncated = text[
                : MAX_MESSAGE_LENGTH - 50
            ]  # Reserve space for truncation marker
            # Look for last sentence boundary
            last_period = truncated.rfind(".")
            last_exclamation = truncated.rfind("!")
            last_question = truncated.rfind("?")
            last_sentence_end = max(last_period, last_exclamation, last_question)

            if last_sentence_end > MAX_MESSAGE_LENGTH * 0.8:  # If found within last 20%
                text = truncated[: last_sentence_end + 1] + "\n\n_(сообщение обрезано)_"
            else:
                # Try paragraph boundary
                last_paragraph = truncated.rfind("\n\n")
                if last_paragraph > MAX_MESSAGE_LENGTH * 0.7:
                    text = (
                        truncated[:last_paragraph].strip()
                        + "\n\n_(сообщение обрезано)_"
                    )
                else:
                    text = truncated + "\n\n_(сообщение обрезано)_"

        await message.answer(text, parse_mode="Markdown")
        logger.debug(f"Response sent successfully: user_id={message.from_user.id}")
    except Exception as e:
        logger.error(
            f"Failed to send response: user_id={message.from_user.id}, error={str(e)}"
        )
        try:
            await message.answer(
                "❌ Sorry, I encountered an error sending the response. "
                "Please try again."
            )
        except Exception:
            logger.error("Failed to send error message", user_id=message.from_user.id)


def _extract_commit_hash(message: str) -> Optional[str]:
    """Extract commit hash from message.

    Args:
        message: User message text

    Returns:
        Commit hash if found, None otherwise
    """
    # Patterns for commit hash (7-64 hex characters)
    patterns = [
        r"(?:сделай|do|make)\s+ревью\s+([a-f0-9]{7,64})",
        r"ревью\s+([a-f0-9]{7,64})",
        r"review\s+([a-f0-9]{7,64})",
        r"проверь\s+коммит\s+([a-f0-9]{7,64})",
        r"check\s+commit\s+([a-f0-9]{7,64})",
        # Also match standalone hash if it's very long (likely commit hash)
        r"\b([a-f0-9]{40,64})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _is_list_channels_request(text: str) -> bool:
    """Определяет запрос на просмотр подписок.

    Purpose:
        Проверяет, хочет ли пользователь посмотреть список своих подписок.

    Args:
        text: Текст сообщения пользователя

    Returns:
        True если это запрос на просмотр подписок

    Example:
        >>> _is_list_channels_request("/channels")
        True
        >>> _is_list_channels_request("мои подписки")
        True
    """
    patterns = [
        r"^/channels$",
        r"мои подписки",
        r"список каналов",
        r"какие каналы",
        r"покажи.*каналы",
        r"мои каналы",
        r"на что.*подписан",
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)


def _is_unsubscribe_request(text: str) -> tuple[bool, str | None]:
    """Определяет запрос на отписку и извлекает имя канала.

    Purpose:
        Проверяет, хочет ли пользователь отписаться от канала,
        и извлекает название канала из запроса.

    Args:
        text: Текст сообщения пользователя

    Returns:
        Tuple of (is_unsubscribe_request, channel_name)
        channel_name может быть None если паттерн не найден

    Example:
        >>> _is_unsubscribe_request("отпишись от onaboka")
        (True, 'onaboka')
        >>> _is_unsubscribe_request("отпишись от Набока")
        (True, 'Набока')
    """
    patterns = [
        r"отпиши[сь]?\s+(?:от|меня)\s+(.+)",
        r"unsubscribe\s+(?:from|от)\s+(.+)",
        r"удал[иь]\s+канал\s+(.+)",
        r"удали\s+подписку\s+(?:на|на\s+канал)\s+(.+)",
    ]
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            channel_name = match.group(1).strip()
            if channel_name:
                return (True, channel_name)
    return (False, None)


def _is_subscribe_request(text: str) -> tuple[bool, str | None]:
    """Определяет запрос на подписку и извлекает имя канала.

    Purpose:
        Проверяет, хочет ли пользователь подписаться на канал,
        и извлекает название канала из запроса.

    Args:
        text: Текст сообщения пользователя

    Returns:
        Tuple of (is_subscribe_request, channel_name)
        channel_name может быть None если паттерн не найден

    Example:
        >>> _is_subscribe_request("/subscribe onaboka")
        (True, 'onaboka')
        >>> _is_subscribe_request("подпишись на Набока")
        (True, 'Набока')
    """
    patterns = [
        r"^/subscribe\s+(.+)$",
        r"подпиши[сь]?\s+(?:на|меня)\s+(.+)",
        r"добавь\s+канал\s+(.+)",
        r"хочу\s+(?:читать|подписаться)\s+(.+)",
        r"подписаться\s+на\s+(.+)",
    ]
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            channel_name = match.group(1).strip()
            return True, channel_name
    return False, None


def _extract_digest_request_info(text: str) -> tuple[str | None, int | None]:
    """Extract channel name and time period from digest request using regex.

    Purpose:
        Fast regex-based parsing of digest requests.
        Extracts channel name and time period (in hours).

    Args:
        text: User message text

    Returns:
        Tuple of (channel_name, hours) or (None, None) if not found

    Example:
        >>> _extract_digest_request_info("дайджест по Набоке")
        ('Набока', None)
        >>> _extract_digest_request_info("дай дайджет Набоки за 5 дней")
        ('Набоки', 120)
    """
    text_lower = text.lower()

    # Patterns for digest requests (improved - optional 'с', flexible word order)
    # Pattern: дайджест/дайджет + optional "по" + channel_name + optional time period
    # Order matters: more specific patterns first
    # Note: [еэ] matches both 'е' and 'э' to handle "дайджет" and "дайджест"
    patterns = [
        # "дай дайджет Набоки за 5 дней" - name directly after digest word (explicit "дайджет")
        r"дай\s+дайджет\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дай дайджест Набоки за 5 дней" - explicit "дайджест"
        r"дай\s+дайджест\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дай дайджет по Набоке за 5 дней" - with "по"
        r"дай\s+дайджет\s+по\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дай дайджест по Набоке за 5 дней" - explicit "дайджест" with "по"
        r"дай\s+дайджест\s+по\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дай дайджет Набоки за 5 дней" - with character class fallback
        r"дай\s+дайдж[еэ]ст\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дайджест по Набоке за 5 дней"
        r"дайдж[еэ]ст\s+по\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дай дайджет по Набоке за 5 дней" - with character class fallback
        r"дай\s+дайдж[еэ]ст\s+по\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дайджест Набоки за 5 дней" (without "по")
        r"дайдж[еэ]ст\s+([а-яёa-z0-9_]+)\s+за\s+(\d+)\s+дн[ея]",
        # "дайджест по Набоке за неделю"
        r"дайдж[еэ]ст\s+(?:по\s+)?([а-яёa-z0-9_]+)\s+за\s+неделю",
        # "дай дайджет по Набоке за неделю"
        r"дай\s+дайдж[еэ]ст\s+(?:по\s+)?([а-яёa-z0-9_]+)\s+за\s+неделю",
        # "дайджест по Набоке" (without time period)
        r"дайдж[еэ]ст\s+по\s+([а-яёa-z0-9_]+)",
        # "дай дайджет по Набоке"
        r"дай\s+дайдж[еэ]ст\s+по\s+([а-яёa-z0-9_]+)",
        # "дайджест канала Набока"
        r"дайдж[еэ]ст\s+канала\s+([а-яёa-z0-9_]+)",
        # "дайджест Набоки" (without "по" and without time - must not be followed by "за")
        r"дайдж[еэ]ст\s+([а-яёa-z0-9_]+)(?:\s+за|$)",
        # "дай дайджет Набоки" (without "по" and without time)
        r"дай\s+дайдж[еэ]ст\s+([а-яёa-z0-9_]+)(?:\s+за|$)",
        # English patterns
        r"digest\s+for\s+@?([a-z0-9_]+)\s+for\s+(\d+)\s+days",
        r"digest\s+@?([a-z0-9_]+)\s+for\s+(\d+)\s+days",
        r"digest\s+for\s+@?([a-z0-9_]+)",
        r"digest\s+@?([a-z0-9_]+)",
    ]

    hours = None
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            channel_name = match.group(1).strip().lstrip("@")
            if channel_name:
                # Extract time period if present
                if len(match.groups()) >= 2 and match.group(2):
                    # Days to hours
                    days = int(match.group(2))
                    hours = days * 24
                elif "неделю" in pattern and "неделю" in text_lower:
                    hours = 7 * 24  # 1 week

                return (channel_name, hours)

    return (None, None)


async def _parse_digest_request_with_llm(text: str) -> tuple[str | None, int | None]:
    """Parse digest request using LLM as fallback.

    Purpose:
        Use LLM to extract channel name and time period from natural language.
        Used when regex parsing fails.

    Args:
        text: User message text

    Returns:
        Tuple of (channel_name, hours) or (None, None) if parsing fails
    """
    try:
        from src.infrastructure.di.container import SummarizationContainer

        container = SummarizationContainer()
        llm_client = container.llm_client()

        prompt = f"""Ты - парсер запросов для Telegram-бота. Извлеки из запроса пользователя:
1. Полное название канала (если есть) - ВКЛЮЧАЯ все слова (имя, фамилию, если указаны)
2. Период времени в днях или часах (если указан)

КРИТИЧЕСКИ ВАЖНО:
- Если название канала в падеже (например, "Набоке", "Набоки", "Алексея", "Гладкова"), восстанови его в именительном падеже (например, "Набока", "Алексей Гладков")
- Если в запросе указано полное имя (например, "Алексея Гладкова"), извлеки ВСЕ слова имени в именительном падеже
- Если указано одно слово в падеже (например, "Набоке"), восстанови его в именительном падеже (например, "Набока")
- Название канала должно быть в именительном падеже (как оно обычно пишется)

Запрос пользователя: "{text}"

Верни ответ ТОЛЬКО в JSON формате:
{{
  "channel_name": "полное_название_канала_в_именительном_падеже_или_null",
  "days": число_дней_или_null,
  "hours": число_часов_или_null
}}

Примеры:
Запрос: "дай дайджет Набоки за 5 дней"
Ответ: {{"channel_name": "Набока", "days": 5, "hours": 120}}

Запрос: "дайджест канала Алексея Гладкова"
Ответ: {{"channel_name": "Алексей Гладков", "days": null, "hours": null}}

Запрос: "Можешь ли передать мне дайджест канала Алексея Гладкова?"
Ответ: {{"channel_name": "Алексей Гладков", "days": null, "hours": null}}

Запрос: "дайджест по python за неделю"
Ответ: {{"channel_name": "python", "days": 7, "hours": 168}}

Запрос: "дайджест по новостям"
Ответ: {{"channel_name": "новости", "days": null, "hours": null}}

Ответ:"""

        response = await llm_client.generate(
            prompt=prompt,
            temperature=0.1,  # Low temperature for deterministic parsing
            max_tokens=256,
        )

        # Parse JSON response
        import json

        # Try to extract JSON from response
        json_match = re.search(r"\{[^}]+\}", response)
        if json_match:
            data = json.loads(json_match.group(0))
            channel_name = data.get("channel_name")
            hours = data.get("hours") or (
                data.get("days") * 24 if data.get("days") else None
            )

            if channel_name and channel_name != "null":
                return (channel_name, hours)

        return (None, None)
    except Exception as e:
        logger.warning(f"LLM parsing failed for digest request: {e}")
        return (None, None)


async def _find_channel_in_metadata_with_llm(
    user_id: int,
    user_query: str,
    channel_name: str,
) -> dict[str, any] | None:
    """Find channel in user's subscriptions using LLM.

    Purpose:
        When channel is not found via normal search, use LLM to search
        in user's subscription metadata (titles, descriptions) to find
        matching channel even if name is in declension or written differently.

    Args:
        user_id: Telegram user ID
        user_query: Original user query (full message text)
        channel_name: Extracted channel name (may be in declension)

    Returns:
        Dict with 'found', 'channel_username', 'channel_title' or None if not found

    Example:
        >>> result = await _find_channel_in_metadata_with_llm(
        ...     user_id=123,
        ...     user_query="дайджест по Набоке",
        ...     channel_name="Набоке"
        ... )
        >>> if result and result.get("found"):
        ...     print(f"Found: @{result['channel_username']}")
    """
    try:
        from src.infrastructure.database.mongo import get_db
        from src.infrastructure.di.container import SummarizationContainer

        # Get user's subscribed channels
        db = await get_db()
        channels_cursor = db.channels.find({"user_id": user_id, "active": True})
        channels_list = await channels_cursor.to_list(length=100)

        if not channels_list:
            logger.debug(f"No subscribed channels for LLM metadata search: user_id={user_id}")
            return None

        # Format channels for LLM
        channels_text = []
        for ch in channels_list:
            username = ch.get("channel_username", "")
            title = ch.get("title", "")
            description = ch.get("description", "")
            
            # Build channel description
            channel_desc = f"@{username}"
            if title:
                channel_desc += f" - {title}"
            if description:
                channel_desc += f" ({description[:100]})"  # Limit description length
            
            channels_text.append(channel_desc)

        if not channels_text:
            return None

        channels_list_text = "\n".join(f"{i+1}. {ch}" for i, ch in enumerate(channels_text))

        # Use LLM to find matching channel
        container = SummarizationContainer()
        llm_client = container.llm_client()

        prompt = f"""Ты помогаешь найти канал в списке подписок пользователя.

Запрос пользователя: "{user_query}"
Извлеченное название канала: "{channel_name}"

ВАЖНО:
- Название канала может быть в падеже (например, "Набоке", "Набоки", "Алексея", "Гладкова")
- Нужно найти канал, который соответствует этому названию, даже если оно в падеже
- Сравнивай по названию канала (title) и username
- Если название в падеже, найди канал с соответствующим именем в именительном падеже

Список подписок пользователя:
{channels_list_text}

Найди канал, который соответствует запросу пользователя. Верни ответ ТОЛЬКО в JSON формате:
{{
  "found": true/false,
  "channel_username": "username_канала_или_null",
  "channel_title": "название_канала_или_null",
  "reason": "краткое_объяснение_почему_этот_канал_подходит"
}}

Если канал не найден, верни:
{{
  "found": false,
  "channel_username": null,
  "channel_title": null,
  "reason": "канал не найден в подписках"
}}

Ответ:"""

        response = await llm_client.generate(
            prompt=prompt,
            temperature=0.1,  # Low temperature for deterministic matching
            max_tokens=256,
        )

        # Parse JSON response
        import json

        json_match = re.search(r"\{[^}]+\}", response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            found = data.get("found", False)
            
            if found:
                username = data.get("channel_username", "").strip().lstrip("@")
                title = data.get("channel_title", "").strip()
                
                if username:
                    logger.info(
                        f"LLM found channel in metadata: "
                        f"user_query='{user_query}', channel_name='{channel_name}' -> "
                        f"username='{username}', title='{title}', reason='{data.get('reason', '')}'"
                    )
                    return {
                        "found": True,
                        "channel_username": username,
                        "channel_title": title,
                        "reason": data.get("reason", ""),
                    }

        logger.debug(
            f"LLM did not find channel in metadata: "
            f"user_query='{user_query}', channel_name='{channel_name}'"
        )
        return None

    except Exception as e:
        logger.warning(
            f"LLM metadata search failed: {e}",
            exc_info=True,
            extra={
                "user_id": user_id,
                "user_query": user_query,
                "channel_name": channel_name,
                "error": str(e),
            },
        )
        return None


def _extract_channel_name_from_digest_request(text: str) -> str | None:
    """Extract channel name from digest request (backward compatibility).

    Purpose:
        Legacy function for backward compatibility.
        Uses improved regex parsing.

    Args:
        text: User message text

    Returns:
        Channel name if found, None otherwise
    """
    channel_name, _ = _extract_digest_request_info(text)
    return channel_name


def _is_review_command(message: str) -> bool:
    """Check if message is a review command.

    Args:
        message: User message text

    Returns:
        True if message is a review command
    """
    message_lower = message.lower()
    review_keywords = [
        "сделай ревью",
        "do review",
        "review",
        "ревью",
        "проверь коммит",
        "check commit",
    ]
    return any(keyword in message_lower for keyword in review_keywords)


async def _handle_file_response(message: Message, file_response: str) -> None:
    """Handle file response from handler.

    Purpose:
        Parse FILE: format and send as document.

    Args:
        message: Telegram message object
        file_response: Response in format "FILE:<filename>:<content>"
    """
    try:
        # Parse format: FILE:<filename>:<content>
        if not file_response.startswith("FILE:"):
            logger.error(f"Invalid file response format: {file_response[:100]}")
            await message.answer("❌ Ошибка обработки файла.")
            return

        parts = file_response[5:].split(":", 1)  # Remove "FILE:" prefix
        if len(parts) != 2:
            logger.error(f"Invalid file response format: {file_response[:100]}")
            await message.answer("❌ Ошибка обработки файла.")
            return

        filename = parts[0]
        content_b64 = parts[1]

        # Decode base64 content
        try:
            content_bytes = base64.b64decode(content_b64)
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            await message.answer("❌ Ошибка декодирования файла.")
            return

        # Send as document
        document = BufferedInputFile(content_bytes, filename=filename)
        await message.answer_document(document=document)
        logger.debug(
            f"File sent successfully: {filename}, size: {len(content_bytes)} bytes"
        )

    except Exception as e:
        logger.error(
            f"Failed to send file: user_id={message.from_user.id}, error={str(e)}",
            exc_info=True,
        )
        try:
            await message.answer("❌ Ошибка при отправке файла. Попробуйте позже.")
        except Exception:
            logger.error("Failed to send error message", user_id=message.from_user.id)


async def _handle_list_channels(message: Message, user_id: int) -> None:
    """Обработать запрос на просмотр подписок.

    Purpose:
        Получает список подписок пользователя и отправляет их в Telegram.

    Args:
        message: Telegram message object
        user_id: User ID
    """
    try:
        from src.presentation.mcp.tools.channels.channel_management import list_channels

        result = await list_channels(user_id=user_id)

        channels = result.get("channels", [])
        if not channels:
            await message.answer("У вас пока нет подписок на каналы.")
            return

        response = "📋 Ваши подписки:\n\n"
        for idx, ch in enumerate(channels, 1):
            username = ch.get("channel_username", "unknown")
            # Use title if available, fallback to username
            # Make sure we use title, not description
            title = ch.get("title") or username
            # If title looks like description (too long), use username
            if len(title) > 50 or title == ch.get("description"):
                title = username
            response += f"✅ {idx}. {username}, {title}\n"

        await message.answer(response)
        logger.info(f"Listed {len(channels)} channels for user_id={user_id}")
    except Exception as e:
        logger.error(f"Error listing channels: {e}", exc_info=True)
        await message.answer("Ошибка при получении списка каналов.")


async def _handle_subscribe_request(
    message: Message, user_id: int, channel_input: str, state: FSMContext | None
) -> None:
    """Обработать запрос на подписку с проверкой существования.

    Purpose:
        Разрешает название канала, проверяет его существование,
        и подписывает пользователя на канал.

    Args:
        message: Telegram message object
        user_id: User ID
        channel_input: Введенное пользователем название канала (может быть название или username)
        state: Optional FSM context for state management
    """
    # Log full channel_input to debug truncation issues
    logger.info(
        f"Processing subscribe request: user_id={user_id}, "
        f"channel_input='{channel_input}' (len={len(channel_input)})"
    )

    try:
        # First, try to resolve from subscriptions
        resolve_use_case = ResolveChannelNameUseCase(allow_telegram_search=False)
        resolution = await resolve_use_case.execute(
            user_id=user_id,
            input_name=channel_input,
            allow_telegram_search=False,
        )

        logger.info(
            f"Resolution result: found={resolution.found}, "
            f"username='{resolution.channel_username}', "
            f"title='{resolution.channel_title}', "
            f"source='{resolution.source}', "
            f"confidence={resolution.confidence_score}, "
            f"input='{channel_input}'"
        )

        # If found in subscriptions, subscribe directly
        # But only if we have high confidence (user is already subscribed)
        # Low confidence means it might be a false match - use search instead
        if (
            resolution.found
            and resolution.channel_username
            and resolution.confidence_score >= 0.7
        ):
            from src.presentation.mcp.tools.channels.channel_management import (
                add_channel,
            )

            result = await add_channel(
                user_id=user_id,
                channel_username=resolution.channel_username,
            )

            status = result.get("status")
            if status == "subscribed":
                await message.answer(
                    f"✅ Вы подписались на канал {resolution.channel_title} "
                    f"(@{resolution.channel_username})"
                )
                logger.info(
                    f"User subscribed to channel",
                    extra={
                        "user_id": user_id,
                        "channel_username": resolution.channel_username,
                        "channel_title": resolution.channel_title,
                        "score": resolution.confidence_score,
                    },
                )
            elif status == "already_subscribed":
                await message.answer(
                    f"ℹ️ Вы уже подписаны на {resolution.channel_title} "
                    f"(@{resolution.channel_username})"
                )
            elif status == "error":
                error_msg = result.get(
                    "message", "Не удалось подтвердить существование канала"
                )
                logger.warning(
                    f"Channel validation failed: user_id={user_id}, "
                    f"channel_input='{channel_input}', "
                    f"resolved_username='{resolution.channel_username}', "
                    f"resolved_title='{resolution.channel_title}', "
                    f"error={result.get('error')}, "
                    f"result={result}"
                )
                await message.answer(
                    f"❌ {error_msg}\n\n"
                    f"Проверьте правильность username канала или попробуйте поиск."
                )
            else:
                # Unknown status - log for debugging
                logger.error(
                    f"Unknown subscription status: status='{status}', "
                    f"result={result}, channel_input='{channel_input}', "
                    f"resolved_username='{resolution.channel_username if resolution else 'N/A'}'"
                )
                error_msg = result.get(
                    "message",
                    f"Не удалось подписаться на канал {resolution.channel_username if resolution and resolution.channel_username else channel_input}",
                )
                await message.answer(f"❌ {error_msg}\n\n" f"Статус: {status}")
            return

        # Not found in subscriptions, search Telegram
        search_use_case = SearchChannelForSubscriptionUseCase()
        search_results = await search_use_case.execute(
            user_id=user_id, query=channel_input
        )

        if not search_results:
            await message.answer(
                f"❌ Канал '{channel_input}' не найден.\n\n"
                f"Проверьте правильность написания или используйте username канала "
                f"(например: @channel_name)"
            )
            logger.info(
                f"Channel not found in search",
                extra={"user_id": user_id, "query": channel_input},
            )
            return

        # Take top 3 candidates for cycling
        top_candidates = search_results[:3]
        if not top_candidates:
            await message.answer(f"❌ Канал '{channel_input}' не найден.")
            return

        # Show first candidate for confirmation
        top_result = top_candidates[0]

        logger.debug(
            f"Top search result: username='{top_result.username}', "
            f"title='{top_result.title}', query='{channel_input}'",
            extra={
                "user_id": user_id,
                "query": channel_input,
                "username": top_result.username,
                "title": top_result.title,
            },
        )

        # Validate that we have valid username and title
        if not top_result.username or not top_result.title:
            logger.error(
                f"Invalid search result: username='{top_result.username}', "
                f"title='{top_result.title}', query='{channel_input}', "
                f"results_count={len(search_results)}",
                extra={
                    "user_id": user_id,
                    "query": channel_input,
                    "username": top_result.username,
                    "title": top_result.title,
                },
            )
            await message.answer(
                f"❌ Не удалось получить информацию о канале '{channel_input}'.\n\n"
                f"Попробуйте использовать точный username канала "
                f"(например: @channel_name)."
            )
            return
        if state:
            # Store all candidates for cycling (convert to dict for FSM storage)
            candidates_data = [
                {
                    "username": candidate.username,
                    "title": candidate.title,
                    "description": candidate.description,
                    "chat_id": candidate.chat_id,
                }
                for candidate in top_candidates
            ]

            await state.set_data(
                {
                    "candidates": candidates_data,
                    "cycler_index": 0,  # Start with first candidate
                    "found_channel": {
                        "username": top_result.username,
                        "title": top_result.title,
                    },
                    "original_input": channel_input,
                    "original_message": message,
                }
            )
            await state.set_state(ChannelSearchStates.waiting_confirmation)

            await message.answer(
                f"🔍 Найден канал: {top_result.title} (@{top_result.username})\n\n"
                f"Подписаться на него? (да/нет)"
            )
            logger.info(
                f"Channel found via search, waiting confirmation",
                extra={
                    "user_id": user_id,
                    "channel_username": top_result.username,
                    "channel_title": top_result.title,
                    "query": channel_input,
                },
            )
        else:
            logger.warning("FSM context not available for channel search confirmation")
            await message.answer(
                f"🔍 Найден канал: {top_result.title} (@{top_result.username})\n\n"
                f"Попробуйте подписаться через команду: /subscribe {top_result.username}"
            )

    except Exception as e:
        logger.error(
            f"Error subscribing to channel: {e}",
            extra={"user_id": user_id, "channel_input": channel_input},
            exc_info=True,
        )
        await message.answer("Ошибка при подписке на канал.")


async def _handle_unsubscribe_request(
    message: Message, user_id: int, channel_input: str
) -> None:
    """Обработать запрос на отписку.

    Purpose:
        Разрешает название канала, проверяет подписку,
        и отписывает пользователя от канала.

    Args:
        message: Telegram message object
        user_id: User ID
        channel_input: Введенное пользователем название канала
    """
    logger.info(
        f"Processing unsubscribe request: user_id={user_id}, "
        f"channel_input='{channel_input}'"
    )

    try:
        # Resolve channel name
        resolve_use_case = ResolveChannelNameUseCase(allow_telegram_search=False)
        resolution = await resolve_use_case.execute(
            user_id=user_id,
            input_name=channel_input,
            allow_telegram_search=False,
        )

        if not resolution.found or not resolution.channel_username:
            await message.answer(
                f"❌ Канал '{channel_input}' не найден в ваших подписках.\n\n"
                f"Проверьте правильность названия канала."
            )
            logger.info(
                f"Channel not found for unsubscribe: user_id={user_id}, input='{channel_input}'"
            )
            return

        # Delete channel subscription
        from src.presentation.mcp.tools.channels.channel_management import (
            delete_channel,
        )
        from src.presentation.mcp.tools.channels.utils import get_database

        # Find channel by username to get ID
        db = await get_database()
        channel = await db.channels.find_one(
            {
                "user_id": user_id,
                "channel_username": resolution.channel_username,
                "active": True,
            }
        )

        if not channel:
            await message.answer(
                f"❌ Канал '{channel_input}' не найден в ваших подписках."
            )
            return

        result = await delete_channel(
            user_id=user_id,
            channel_id=str(channel["_id"]),
        )

        status = result.get("status")
        if status == "deleted":
            await message.answer(
                f"✅ Вы отписались от канала {resolution.channel_title} "
                f"(@{resolution.channel_username})"
            )
            logger.info(
                f"User unsubscribed from channel",
                extra={
                    "user_id": user_id,
                    "channel_username": resolution.channel_username,
                    "channel_title": resolution.channel_title,
                },
            )
        elif status == "not_found":
            await message.answer(
                f"ℹ️ Канал {resolution.channel_title} (@{resolution.channel_username}) "
                f"не найден в ваших подписках."
            )
        else:
            error_msg = result.get("message", "Не удалось отписаться от канала")
            await message.answer(f"❌ {error_msg}")
            logger.warning(
                f"Failed to unsubscribe: user_id={user_id}, "
                f"channel_username={resolution.channel_username}, "
                f"status={status}, result={result}"
            )

    except Exception as e:
        logger.error(
            f"Error unsubscribing from channel: {e}",
            extra={"user_id": user_id, "channel_input": channel_input},
            exc_info=True,
        )
        await message.answer("❌ Ошибка при отписке от канала.")


async def _handle_error(message: Message, error: Exception) -> None:
    """Handle errors gracefully with user-friendly message.

    Purpose:
        Send error message to user when processing fails.

    Args:
        message: Telegram message object
        error: Exception that occurred
    """
    try:
        await message.answer(
            "❌ Sorry, I encountered an error processing your message. "
            "Please try again or use /menu for available commands."
        )
    except Exception as e:
        user_id = message.from_user.id if message.from_user else None
        logger.error(f"Failed to send error message: user_id={user_id}, error={str(e)}")
