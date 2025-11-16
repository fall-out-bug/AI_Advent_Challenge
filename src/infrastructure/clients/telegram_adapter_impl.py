"""Telegram adapter implementation wrapping telegram_utils.

Purpose:
    Implements TelegramAdapter interface by wrapping existing telegram_utils
    functions, enabling dependency injection and testability.

Following Clean Architecture: Infrastructure adapter implementing domain interface.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from src.domain.interfaces.telegram_adapter import TelegramAdapter
from src.infrastructure.clients.telegram_utils import fetch_channel_posts as _fetch_channel_posts


class TelegramAdapterImpl(TelegramAdapter):
    """Implementation of TelegramAdapter using telegram_utils.

    Purpose:
        Wraps existing telegram_utils.fetch_channel_posts() to implement
        TelegramAdapter interface, enabling dependency injection.

    Example:
        >>> adapter = TelegramAdapterImpl()
        >>> posts = await adapter.fetch_channel_posts(
        ...     channel_username="onaboka",
        ...     since=datetime.utcnow() - timedelta(days=1)
        ... )
    """

    async def fetch_channel_posts(
        self,
        channel_username: str,
        since: datetime,
        user_id: int | None = None,
        save_to_db: bool = True,
    ) -> List[dict]:
        """Fetch recent posts from a Telegram channel.

        Purpose:
            Delegates to telegram_utils.fetch_channel_posts() while ensuring
            channel_username is in canonical form (lowercase, without @ prefix).

        Args:
            channel_username: Channel username (will be normalized to canonical form).
            since: Minimum timestamp for posts.
            user_id: Optional user ID for saving posts to database.
            save_to_db: Whether to save posts to database automatically.

        Returns:
            List of post dictionaries.

        Raises:
            ValueError: If channel_username is invalid or channel not found.
            Exception: If fetching fails due to network/auth errors.
        """
        # Normalize channel_username to canonical form (lowercase, without @)
        # This ensures E.1 policy compliance
        normalized_username = channel_username.lower().lstrip("@")

        # Delegate to telegram_utils
        return await _fetch_channel_posts(
            channel_username=normalized_username,
            since=since,
            user_id=user_id,
            save_to_db=save_to_db,
        )
