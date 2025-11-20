"""Confirmation gateway implementation.

Purpose:
    Implements ConfirmationGateway Protocol by wrapping Telegram Bot API
    for sending confirmation messages with inline buttons.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from uuid import UUID

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.interfaces import ConfirmationGateway
from src.infrastructure.logging import get_logger

logger = get_logger("voice.confirmation_gateway_impl")


class ConfirmationGatewayImpl:
    """Confirmation gateway implementation using Telegram Bot API.

    Purpose:
        Sends confirmation messages with inline buttons ("Подтвердить", "Повторить")
        to users for transcribed voice commands. Implements ConfirmationGateway
        Protocol for testability.

    Args:
        bot: Aiogram Bot instance (injected via DI).
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_confirmation(
        self,
        user_id: str,
        text: str,
        command_id: UUID,
    ) -> None:
        """Send confirmation message to user with inline buttons.

        Purpose:
            Sends a message to the user showing the transcribed text
            and inline buttons for confirmation ("Подтвердить", "Повторить").

        Args:
            user_id: Telegram user identifier.
            text: Recognized transcription text to display.
            command_id: Voice command UUID for callback payload.

        Example:
            >>> gateway = ConfirmationGatewayImpl(bot)
            >>> await gateway.send_confirmation(
            ...     user_id="123456789",
            ...     text="Сделай дайджест по каналу X",
            ...     command_id=UUID("12345678-1234-5678-1234-567812345678")
            ... )
        """
        logger.info(
            "Sending confirmation message",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "text_length": len(text),
            },
        )

        # Format confirmation message (Russian)
        # Truncate text if too long for Telegram (4096 chars max)
        max_text_length = 3800  # Reserve space for formatting
        display_text = text[:max_text_length] + ("..." if len(text) > max_text_length else "")
        message_text = (
            f"🎤 Распознала: «{display_text}»\n\n"
            "Подтвердить выполнение команды?"
        )

        # Create inline keyboard with buttons
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"voice_confirm:{command_id}",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Повторить",
                        callback_data=f"voice_reject:{command_id}",
                    ),
                ],
            ]
        )

        # Retry sending confirmation message (up to 3 attempts)
        max_retries = 3
        retry_delay = 2.0  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                await self.bot.send_message(
                    chat_id=int(user_id),
                    text=message_text,
                    reply_markup=keyboard,
                    request_timeout=60.0,  # Increase timeout to avoid disconnections
                )

                logger.info(
                    "Confirmation message sent",
                    extra={
                        "user_id": user_id,
                        "command_id": str(command_id),
                        "attempt": attempt,
                    },
                )
                return  # Success - exit retry loop

            except Exception as e:
                error_type = type(e).__name__
                is_last_attempt = attempt == max_retries

                logger.warning(
                    f"Failed to send confirmation message (attempt {attempt}/{max_retries})",
                    extra={
                        "user_id": user_id,
                        "command_id": str(command_id),
                        "error_type": error_type,
                        "error": str(e),
                        "attempt": attempt,
                    },
                )

                if is_last_attempt:
                    # Last attempt failed - try sending plain text without keyboard as fallback
                    logger.warning(
                        "All retry attempts failed, trying fallback (plain text without keyboard)",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                        },
                    )
                    try:
                        # Fallback: send simple text message without keyboard
                        fallback_message = (
                            f"🎤 Распознала: «{text}»\n\n"
                            "⚠️ Команда сохранена, но кнопки подтверждения не работают. "
                            "Пожалуйста, отправьте текст команды повторно."
                        )
                        await self.bot.send_message(
                            chat_id=int(user_id),
                            text=fallback_message,
                        )
                        logger.info(
                            "Fallback confirmation message sent (plain text)",
                            extra={
                                "user_id": user_id,
                                "command_id": str(command_id),
                            },
                        )
                        return  # Fallback succeeded
                    except Exception as fallback_error:
                        logger.error(
                            "Fallback message also failed",
                            extra={
                                "user_id": user_id,
                                "command_id": str(command_id),
                                "error": str(fallback_error),
                            },
                        )
                        # All attempts failed including fallback
                        # Don't raise exception - just log error
                        # The use case will continue without confirmation message
                        logger.error(
                            "All confirmation attempts failed, including fallback",
                            extra={
                                "user_id": user_id,
                                "command_id": str(command_id),
                                "original_error": str(e),
                                "fallback_error": str(fallback_error),
                            },
                        )
                        # Return None instead of raising to avoid breaking the flow
                        return

                # Not last attempt - wait before retry
                await asyncio.sleep(retry_delay * attempt)  # Exponential backoff
