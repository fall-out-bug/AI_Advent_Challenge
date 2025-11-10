"""Message sending utilities with retry logic and error handling."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError

from src.infrastructure.logging import get_logger
from src.workers.formatters import clean_markdown

logger = get_logger("message_sender")

# Constants
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
SAFE_MESSAGE_LIMIT = 4000


async def send_with_retry(
    bot: Bot,
    user_id: int,
    get_text_fn_or_str: Union[str, Callable[..., Any]],
    notification_type: str,
) -> None:
    """Send message with exponential backoff retry.

    Purpose:
        Send Telegram message with automatic retry on network errors.
        Handles Markdown parse errors by falling back to plain text.
        Supports both string messages and async functions that return text.

    Args:
        bot: Telegram bot instance
        user_id: Target user ID
        get_text_fn_or_str: Message text (str) or async function that returns text
        notification_type: Type of notification for logging

    Returns:
        None (raises exception if all retries fail)
    """
    delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RETRIES):
        try:
            text = await _resolve_text(get_text_fn_or_str, user_id)

            if not text:
                logger.warning(
                    "No text to send, skipping", user_id=user_id, type=notification_type
                )
                return

            # Check if this is a digest (always plain text)
            is_digest = "digest" in notification_type.lower()

            # For digests: clean Markdown before sending
            if is_digest:
                original_length = len(text)
                text = clean_markdown(text)
                logger.info(
                    "Cleaned digest text",
                    user_id=user_id,
                    original_length=original_length,
                    cleaned_length=len(text),
                )

            logger.info(
                "Attempting to send message",
                user_id=user_id,
                type=notification_type,
                text_preview=text[:150] if text else None,
                is_digest=is_digest,
                text_length=len(text) if text else 0,
            )

            # Check message length (Telegram limit is 4096 chars)
            if len(text) > SAFE_MESSAGE_LIMIT:
                logger.warning(
                    "Message too long, truncating",
                    user_id=user_id,
                    type=notification_type,
                    length=len(text),
                )
                text = text[:3950] + "\n...message truncated..."

            # Send message with appropriate parse mode
            use_markdown = not is_digest and notification_type != "debug summary"
            await _send_message_safe(
                bot, user_id, text, use_markdown, notification_type
            )

            if attempt > 0:
                logger.info(
                    "Successfully sent after retry",
                    user_id=user_id,
                    type=notification_type,
                    attempt=attempt + 1,
                )
            else:
                logger.info(
                    "Successfully sent notification",
                    user_id=user_id,
                    type=notification_type,
                )
            return

        except TelegramBadRequest as e:
            if not await _handle_telegram_error(
                bot, user_id, text, e, notification_type, attempt
            ):
                return  # Permanent error, don't retry

        except (TelegramNetworkError, ConnectionError, TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "Network error, retrying",
                    user_id=user_id,
                    type=notification_type,
                    attempt=attempt + 1,
                    error=str(e),
                )
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    "Failed after all retries",
                    user_id=user_id,
                    type=notification_type,
                    attempts=MAX_RETRIES,
                    error=str(e),
                )
                raise

        except Exception as e:
            logger.error(
                "Unexpected error sending notification",
                user_id=user_id,
                type=notification_type,
                error=str(e),
            )
            return  # Don't retry on unexpected errors


async def _resolve_text(
    get_text_fn_or_str: Union[str, Callable[..., Any]], user_id: int
) -> str | None:
    """Resolve text from string or callable.

    Args:
        get_text_fn_or_str: Text string or callable
        user_id: User ID for function calls

    Returns:
        Resolved text or None
    """
    if isinstance(get_text_fn_or_str, str):
        return get_text_fn_or_str

    if not callable(get_text_fn_or_str):
        return str(get_text_fn_or_str) if get_text_fn_or_str else None

    # Check if it's a coroutine function (needs await) or regular function
    if inspect.iscoroutinefunction(get_text_fn_or_str):
        return await get_text_fn_or_str(user_id)

    # It's a regular function, but might return coroutine
    result = get_text_fn_or_str(user_id)
    if inspect.iscoroutine(result):
        return await result

    return result


async def _send_message_safe(
    bot: Bot, user_id: int, text: str, use_markdown: bool, notification_type: str
) -> None:
    """Send message with Markdown error handling.

    Args:
        bot: Telegram bot instance
        user_id: Target user ID
        text: Message text
        use_markdown: If True, try Markdown formatting
        notification_type: Type for logging

    Raises:
        TelegramBadRequest: If sending fails
    """
    try:
        if use_markdown:
            await bot.send_message(user_id, text, parse_mode="Markdown")
        else:
            await bot.send_message(user_id, text, parse_mode=None)
    except TelegramBadRequest as md_error:
        error_msg = str(md_error)
        if _is_markdown_parse_error(error_msg):
            logger.warning(
                "Markdown parse error, retrying without formatting",
                user_id=user_id,
                type=notification_type,
                error=error_msg,
            )
            plain_text = _normalize_text(text)
            await bot.send_message(user_id, plain_text, parse_mode=None)
        else:
            raise


def _is_markdown_parse_error(error_msg: str) -> bool:
    """Check if error is a Markdown parse error.

    Args:
        error_msg: Error message string

    Returns:
        True if Markdown parse error
    """
    error_lower = error_msg.lower()
    return "can't parse entities" in error_lower or (
        "parse" in error_lower and "entity" in error_lower
    )


def _normalize_text(text: str) -> str:
    """Normalize text by removing Markdown and cleaning.

    Args:
        text: Text to normalize

    Returns:
        Normalized plain text
    """
    import re

    # Remove Markdown
    plain_text = clean_markdown(text)

    # Normalize quotes
    plain_text = plain_text.replace('"', '"').replace('"', '"')
    plain_text = plain_text.replace(""", "'").replace(""", "'")

    # Clean extra whitespace
    plain_text = re.sub(r"\s+", " ", plain_text).strip()

    return plain_text


async def _handle_telegram_error(
    bot: Bot,
    user_id: int,
    text: str,
    error: TelegramBadRequest,
    notification_type: str,
    attempt: int,
) -> bool:
    """Handle Telegram errors and decide if retry is needed.

    Args:
        bot: Telegram bot instance
        user_id: Target user ID
        text: Message text
        error: Telegram error exception
        notification_type: Type for logging
        attempt: Current attempt number

    Returns:
        True if should retry, False if permanent error
    """
    error_msg = str(error)

    # Check if this is a Markdown parse error
    if _is_markdown_parse_error(error_msg):
        logger.warning(
            "Markdown parse error in outer handler, trying plain text fallback",
            user_id=user_id,
            type=notification_type,
            error=error_msg,
            attempt=attempt,
        )
        plain_text = _normalize_text(text)
        try:
            await bot.send_message(user_id, plain_text, parse_mode=None)
            logger.info(
                "Successfully sent as plain text after Markdown error (outer handler)",
                user_id=user_id,
                type=notification_type,
            )
            return False  # Success, don't retry
        except Exception as plain_err:
            logger.error(
                "Failed to send plain text fallback in outer handler",
                user_id=user_id,
                type=notification_type,
                error=str(plain_err),
            )

    logger.warning(
        "Cannot send to user", user_id=user_id, type=notification_type, error=error_msg
    )

    # Don't retry on permanent errors
    if "chat not found" in error_msg.lower() or "blocked" in error_msg.lower():
        return False  # Permanent error, don't retry

    return True  # May retry
