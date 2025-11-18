"""Confirmation gateway implementation (deprecated).

Purpose:
    Implements ConfirmationGateway protocol for sending confirmation messages.
    Deprecated in favor of immediate execution after transcription.
"""

from __future__ import annotations

from uuid import UUID

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.interfaces.voice import ConfirmationGateway
from src.infrastructure.logging import get_logger

logger = get_logger("voice.confirmation_gateway_impl")


class ConfirmationGatewayImpl:
    """Confirmation gateway implementation (deprecated).

    Purpose:
        Implements ConfirmationGateway protocol by sending Telegram messages
        with inline keyboard buttons for confirmation. Deprecated in favor
        of immediate execution after transcription.

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
        """Send confirmation message with buttons (deprecated).

        Purpose:
            Sends Telegram message with transcribed text and inline buttons
            for confirmation. Note: This method is deprecated and not used
            in immediate execution flow.

        Args:
            user_id: User identifier (Telegram user ID).
            text: Transcribed command text to confirm.
            command_id: Unique command identifier (UUID).

        Raises:
            RuntimeError: If sending fails.

        Example:
            >>> gateway = ConfirmationGatewayImpl(bot)
            >>> await gateway.send_confirmation(
            ...     user_id="123456789",
            ...     text="Привет, мир!",
            ...     command_id=UUID("12345678-1234-5678-1234-567812345678"),
            ... )
        """
        logger.debug(
            "Sending confirmation message (deprecated)",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "text_length": len(text),
            },
        )

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
                    "Confirmation message sent (deprecated)",
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
                    logger.error(
                        "All confirmation attempts failed",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                            "error": str(e),
                        },
                    )
                    # Don't raise exception - just log error
                    # The use case will continue without confirmation message
                    return

                # Not last attempt - wait before retry
                import asyncio
                await asyncio.sleep(retry_delay * attempt)  # Exponential backoff

