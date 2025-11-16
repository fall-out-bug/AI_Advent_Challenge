"""Telegram adapter interface for fetching channel posts.

Purpose:
    Defines the canonical interface for Telegram operations,
    enabling dependency injection and testability.

Following Clean Architecture: Domain interface for infrastructure adapters.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class TelegramAdapter(Protocol):
    """Interface for Telegram channel post fetching operations.

    Purpose:
        Provides a stable interface for fetching Telegram channel posts,
        enabling dependency injection and testability.

    Note:
        Channel username should be in canonical form (lowercase, without @ prefix)
        per E.1 policy. The adapter may normalize input internally.

    Example:
        >>> adapter = TelegramAdapterImpl()
        >>> posts = await adapter.fetch_channel_posts(
        ...     channel_username="onaboka",
        ...     since=datetime.utcnow() - timedelta(days=1),
        ...     user_id=12345
        ... )
        >>> len(posts) >= 0
        True
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
            Retrieve channel posts since a given datetime.
            Optionally saves posts to MongoDB if save_to_db is True.

        Args:
            channel_username: Channel username in canonical form
                (lowercase, without @ prefix per E.1 policy).
                Example: "onaboka" (not "@onaboka").
            since: Minimum timestamp for posts.
            user_id: Optional user ID for saving posts to database.
            save_to_db: Whether to save posts to database automatically.

        Returns:
            List of post dictionaries with keys:
            - text: Post text content
            - date: ISO format datetime string
            - channel: Channel username (canonical form)
            - message_id: Telegram message ID
            - views: Optional view count
            - metadata: Optional metadata dict

        Raises:
            ValueError: If channel_username is invalid or channel not found.
            Exception: If fetching fails due to network/auth errors.

        Example:
            >>> posts = await adapter.fetch_channel_posts(
            ...     channel_username="onaboka",
            ...     since=datetime.utcnow() - timedelta(hours=24),
            ...     user_id=12345
            ... )
            >>> for post in posts:
            ...     assert "text" in post
            ...     assert "date" in post
            ...     assert "channel" in post
        """
        ...
