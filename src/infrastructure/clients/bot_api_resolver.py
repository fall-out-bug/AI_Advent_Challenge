"""Bot API channel resolver.

Purpose:
    Resolve channel by username using Bot API (aiogram) as fallback.
    Used when channel is not found in user dialogs.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from src.infrastructure.logging import get_logger

logger = get_logger("bot_api_resolver")

# Timeout for Bot API calls
BOT_API_TIMEOUT = 3.0


class BotApiChannelResolver:
    """Resolve channels by username using Bot API.

    Purpose:
        Fallback resolver for channels not found in user dialogs.
        Uses Bot API to get channel info by username.
    """

    def __init__(self, bot_token: Optional[str] = None) -> None:
        """Initialize resolver.

        Args:
            bot_token: Telegram Bot API token (defaults to BOT_TOKEN env var)
        """
        import os
        self.bot_token = bot_token or os.getenv("BOT_TOKEN")
        if not self.bot_token:
            logger.warning("BOT_TOKEN not set, Bot API resolver will be disabled")
        self._bot: Optional[Bot] = None

    async def _get_bot(self) -> Optional[Bot]:
        """Get or create Bot instance.

        Returns:
            Bot instance or None if token is not available
        """
        if not self.bot_token:
            return None
        
        if self._bot is None:
            self._bot = Bot(token=self.bot_token)
        
        return self._bot

    async def resolve_username(self, username: str) -> Optional[dict]:
        """Resolve channel by username.

        Purpose:
            Get channel info by username using Bot API.
            Only works for public channels.

        Args:
            username: Channel username (without @)

        Returns:
            Channel dict with username, title, description, chat_id, or None if not found

        Example:
            >>> resolver = BotApiChannelResolver()
            >>> result = await resolver.resolve_username("python_daily")
            >>> result["username"]
            'python_daily'
        """
        if not self.bot_token:
            logger.debug("Bot API resolver disabled: BOT_TOKEN not set")
            return None

        username_clean = username.lstrip("@").strip()
        if not username_clean:
            logger.debug(f"Invalid username: '{username}'")
            return None

        # Check if username looks valid (latin, digits, underscore)
        if not all(c.isalnum() or c == "_" for c in username_clean):
            logger.debug(
                f"Username doesn't look like a valid Telegram username: '{username_clean}'"
            )
            return None

        bot = await self._get_bot()
        if not bot:
            return None

        try:
            logger.debug(f"Resolving channel via Bot API: username='{username_clean}'")
            
            # Use timeout to prevent hanging
            chat = await asyncio.wait_for(
                bot.get_chat(f"@{username_clean}"),
                timeout=BOT_API_TIMEOUT
            )
            
            if not chat:
                logger.debug(f"Bot API returned None for username: '{username_clean}'")
                return None

            # Extract channel info
            chat_username = getattr(chat, "username", None) or ""
            chat_title = getattr(chat, "title", None) or ""
            chat_id = getattr(chat, "id", None)
            chat_description = getattr(chat, "description", None) or ""

            # Only return if we have username and title
            if not chat_username or not chat_title:
                logger.debug(
                    f"Channel missing required fields: username='{chat_username}', "
                    f"title='{chat_title}'"
                )
                return None

            result = {
                "username": chat_username,
                "title": chat_title,
                "description": chat_description,
                "chat_id": chat_id,
                "score": 85,  # High score for direct resolve
            }

            logger.info(
                f"Resolved channel via Bot API: username='{chat_username}', "
                f"title='{chat_title}'"
            )
            return result

        except asyncio.TimeoutError:
            logger.warning(
                f"Bot API timeout after {BOT_API_TIMEOUT}s for username: '{username_clean}'"
            )
            return None
        except TelegramBadRequest as e:
            logger.debug(
                f"Channel not found via Bot API: username='{username_clean}', error={e}"
            )
            return None
        except TelegramAPIError as e:
            logger.warning(
                f"Bot API error resolving channel: username='{username_clean}', error={e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error in Bot API resolver: username='{username_clean}', error={e}",
                exc_info=True
            )
            return None

    async def close(self) -> None:
        """Close Bot instance and cleanup resources."""
        if self._bot:
            await self._bot.session.close()
            self._bot = None
            logger.debug("Bot API resolver closed")

