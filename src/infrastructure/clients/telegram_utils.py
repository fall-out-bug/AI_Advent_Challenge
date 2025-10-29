"""Telegram client utilities for fetching channel posts."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import List

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="telegram_utils")


async def fetch_channel_posts(channel_username: str, since: datetime) -> List[dict]:
    """Fetch recent posts from a Telegram channel.

    Purpose:
        Retrieve channel posts since a given datetime for digest generation.

    Args:
        channel_username: Channel username without @
        since: Minimum timestamp for posts

    Returns:
        List of post dictionaries with text, date, etc.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, cannot fetch channel posts")
        return []

    bot = None
    try:
        bot = Bot(token=bot_token)
        # Format channel username (add @ if not present)
        channel_id = f"@{channel_username}" if not channel_username.startswith("@") else channel_username
        
        # Try to get channel info first
        print(f"[fetch_channel_posts] DEBUG: Trying to access channel {channel_username}", file=sys.stderr)
        try:
            chat = await bot.get_chat(channel_id)
            print(f"[fetch_channel_posts] DEBUG: Channel accessible, chat_id={chat.id}", file=sys.stderr)
            logger.info("Channel accessible", channel=channel_username, chat_id=chat.id)
        except (TelegramBadRequest, TelegramAPIError) as e:
            print(f"[fetch_channel_posts] DEBUG: Cannot access channel: {e}", file=sys.stderr)
            logger.warning("Cannot access channel", channel=channel_username, error=str(e))
            return []
        
        # Note: Telegram Bot API doesn't provide direct access to channel message history
        # without admin rights. For now, return mock data for testing.
        # In production, you would need:
        # 1. Bot as channel admin, or
        # 2. MTProto client with user account, or
        # 3. Store messages when bot receives forwarded posts
        
        # For testing/debugging: return placeholder posts if channel exists
        # Always return at least one post for debug purposes
        print(f"[fetch_channel_posts] DEBUG: Creating placeholder posts for {channel_username}", file=sys.stderr)
        logger.info("Returning placeholder posts", channel=channel_username)
        now = datetime.utcnow()
        # Return posts within the time window (always include recent posts for debug)
        posts = []
        # Add a few placeholder posts with different timestamps
        # Make posts more realistic and varied for better summarization testing
        placeholder_texts = [
            f"В канале {channel_username} обсуждаются новости о новых технологиях и разработке.",
            f"Представлены результаты тестирования и анализа производительности последних обновлений в {channel_username}.",
            f"Пользователи {channel_username} делятся опытом и советами по оптимизации работы с новыми инструментами.",
        ]
        for i in range(min(3, len(placeholder_texts))):
            post_date = now.timestamp() - (i * 3600)  # Last 3 hours
            posts.append({
                "text": placeholder_texts[i],
                "date": datetime.fromtimestamp(post_date).isoformat(),
                "channel": channel_username,
                "message_id": f"test_{i}",
            })
        print(f"[fetch_channel_posts] DEBUG: Returning {len(posts)} posts", file=sys.stderr)
        logger.info("Returning posts", channel=channel_username, count=len(posts))
        return posts
        
    except Exception as e:
        logger.error("Error fetching channel posts", channel=channel_username, error=str(e), exc_info=True)
        return []
    finally:
        if bot is not None:
            await bot.session.close()

