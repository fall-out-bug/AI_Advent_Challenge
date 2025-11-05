"""Telegram notifier for sending async task results."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from src.infrastructure.logging import get_logger

logger = get_logger("telegram_notifier")


class TelegramNotifier:
    """Telegram notifier for sending messages.

    Purpose:
        Sends messages to Telegram chat by chat_id.
        Used for delivering async task results.

    Args:
        bot: aiogram Bot instance.
    """

    def __init__(self, bot: Bot) -> None:
        """Initialize notifier.

        Args:
            bot: aiogram Bot instance
        """
        self.bot = bot

    async def send_message(self, chat_id: int, text: str) -> None:
        """Send message to chat.

        Purpose:
            Sends a new message to the specified chat.
            Handles errors gracefully with logging.

        Args:
            chat_id: Telegram chat ID.
            text: Message text to send.

        Raises:
            TelegramBadRequest: If chat_id is invalid.
            TelegramAPIError: On other Telegram API errors.
        """
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Sent message to chat: chat_id={chat_id}, text_length={len(text)}")
        except TelegramBadRequest as e:
            logger.error(
                f"Failed to send message (bad request): chat_id={chat_id}, error={str(e)}"
            )
            raise
        except TelegramAPIError as e:
            logger.error(
                f"Failed to send message (API error): chat_id={chat_id}, error={str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error sending message: chat_id={chat_id}, error={str(e)}",
                exc_info=True,
            )
            raise

