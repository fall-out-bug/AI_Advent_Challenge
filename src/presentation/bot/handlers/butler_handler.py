"""Butler handler for Telegram bot using ButlerOrchestrator.

Following Clean Architecture: Presentation layer delegates to domain layer.
Following Python Zen: Simple is better than complex.
"""

import base64
import logging
import re
from typing import Optional

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.services.mode_classifier import DialogMode
from src.application.use_cases.resolve_channel_name import ResolveChannelNameUseCase
from src.application.use_cases.search_channel_for_subscription import (
    SearchChannelForSubscriptionUseCase,
)
from src.presentation.bot.states import ChannelSearchStates
from src.infrastructure.logging import get_logger

logger = get_logger("butler_handler")

# Global orchestrator instance (set by setup_butler_handler)
_orchestrator: Optional[ButlerOrchestrator] = None


def setup_butler_handler(orchestrator: ButlerOrchestrator) -> Router:
    """Setup butler handler with orchestrator dependency.

    Purpose:
        Configure router with orchestrator dependency for handler functions.

    Args:
        orchestrator: ButlerOrchestrator instance for message processing

    Returns:
        Configured aiogram Router

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> router = setup_butler_handler(orchestrator)
        >>> dp.include_router(router)
    """
    global _orchestrator
    _orchestrator = orchestrator

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
            await _handle_unsubscribe_request(message, int(user_id), unsubscribe_channel.strip())
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
        # Try regex first (fast)
        channel_name, hours = _extract_digest_request_info(text)

        # If regex failed, try LLM parsing (slower but more reliable)
        if not channel_name:
            logger.debug(f"Regex parsing failed, trying LLM parsing for: {text[:50]}")
            channel_name, hours = await _parse_digest_request_with_llm(text)

        if channel_name:
            # Intercept digest request and use channel resolver
            try:
                use_case = ResolveChannelNameUseCase(allow_telegram_search=True)
                resolution = await use_case.execute(
                    user_id=int(user_id),
                    input_name=channel_name,
                    allow_telegram_search=True,
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
                elif not resolution.found and resolution.source == "subscription":
                    # Channel not found in subscriptions, try search
                    logger.info(
                        f"Channel not found in subscriptions: input={channel_name}, "
                        f"top_score={resolution.confidence_score:.3f}, user_id={user_id}"
                    )
                    # If confidence is low, channel might not be in subscriptions
                    # For digest requests, we can't proceed without a channel
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
                            f"title='{resolution.channel_title}', input='{channel_name}'",
                            extra={
                                "user_id": user_id,
                                "input": channel_name,
                                "username": resolution.channel_username,
                                "title": resolution.channel_title,
                            },
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

        response = await _orchestrator.handle_user_message(
            user_id=user_id, message=text, session_id=session_id, force_mode=force_mode
        )
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
    MAX_MESSAGE_LENGTH = 4096  # Telegram limit

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
1. Название канала (если есть)
2. Период времени в днях или часах (если указан)

Запрос пользователя: "{text}"

Верни ответ ТОЛЬКО в JSON формате:
{{
  "channel_name": "название_канала_или_null",
  "days": число_дней_или_null,
  "hours": число_часов_или_null
}}

Примеры:
Запрос: "дай дайджет Набоки за 5 дней"
Ответ: {{"channel_name": "Набока", "days": 5, "hours": 120}}

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
        if resolution.found and resolution.channel_username and resolution.confidence_score >= 0.7:
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
                    f"Не удалось подписаться на канал {resolution.channel_username if resolution and resolution.channel_username else channel_input}"
                )
                await message.answer(
                    f"❌ {error_msg}\n\n"
                    f"Статус: {status}"
                )
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
            await message.answer(
                f"❌ Канал '{channel_input}' не найден."
            )
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
