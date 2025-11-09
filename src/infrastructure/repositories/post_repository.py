"""Post repository implementation with hybrid deduplication.

Hybrid deduplication strategy:
1. Primary: message_id + channel_username (24h window) - fast lookup
2. Secondary: content_hash (SHA256) (7-day window) - catches edits/reposts
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase


class PostRepository:
    """Async repository for post documents with hybrid deduplication.

    Purpose:
        Encapsulate CRUD operations and querying logic for Telegram posts.
        Prevents duplicates using message_id (24h) and content_hash (7 days).

    Exceptions:
        ValueError: If provided inputs are invalid
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository.

        Args:
            db: MongoDB database instance
        """
        self._db = db
        self._indexes_created = False

    async def _ensure_indexes(self) -> None:
        """Create required indexes for efficient queries."""
        if self._indexes_created:
            return

        collection = self._db.posts
        await collection.create_index([("channel_username", 1), ("message_id", 1)])
        await collection.create_index([("content_hash", 1), ("date", -1)])
        await collection.create_index([("user_id", 1), ("date", -1)])
        await collection.create_index(
            [("date", 1)], expireAfterSeconds=604800
        )  # 7 days TTL
        self._indexes_created = True

    async def save_post(self, post: dict) -> str | None:
        """Save post with deduplication check.

        Args:
            post: Post dictionary with required fields:
                - channel_username: str
                - message_id: str
                - text: str
                - user_id: int
                - date: datetime

        Returns:
            Post ID if saved, None if duplicate found

        Raises:
            ValueError: If required fields are missing
        """
        await self._ensure_indexes()

        required_fields = ["channel_username", "message_id", "text", "user_id", "date"]
        missing_fields = [field for field in required_fields if field not in post]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        channel_username = post["channel_username"]
        message_id = post["message_id"]
        text = post["text"]
        content_hash = self._calculate_content_hash(text, channel_username)

        # Check duplicate by message_id (24h window)
        if await self._check_duplicate_by_message_id(channel_username, message_id):
            return None

        # Check duplicate by content_hash (7-day window)
        if await self._check_duplicate_by_content_hash(content_hash):
            return None

        # Save post
        doc: Dict[str, Any] = {
            "channel_username": channel_username,
            "message_id": message_id,
            "content_hash": content_hash,
            "user_id": post["user_id"],
            "text": text,
            "date": post["date"],
            "fetched_at": datetime.utcnow(),
            "views": post.get("views"),
            "metadata": post.get("metadata", {}),
        }

        result = await self._db.posts.insert_one(doc)
        return str(result.inserted_id)

    async def get_posts_by_user_subscriptions(
        self, user_id: int, hours: int = 24
    ) -> List[dict]:
        """Get posts for user's subscribed channels.

        Args:
            user_id: Telegram user ID
            hours: Hours to look back (default 24)

        Returns:
            List of post dictionaries
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        since.isoformat()

        # Get user's subscribed channels
        channels_cursor = self._db.channels.find({"user_id": user_id, "active": True})
        channels = await channels_cursor.to_list(length=100)
        channel_usernames = [ch["channel_username"] for ch in channels]

        if not channel_usernames:
            return []

        # Get posts from subscribed channels
        # Note: Posts may have date as datetime or ISO string, so we query without date filter
        # and filter in Python for compatibility
        query = {
            "user_id": user_id,
            "channel_username": {"$in": channel_usernames},
        }
        cursor = self._db.posts.find(query).sort("date", -1)
        all_posts = await cursor.to_list(length=1000)

        # Filter by date in Python to handle both datetime and ISO string formats
        posts = []
        for post in all_posts:
            post_date = post.get("date")
            if post_date:
                # Convert ISO string to datetime if needed
                if isinstance(post_date, str):
                    try:
                        post_date = datetime.fromisoformat(
                            post_date.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        continue

                # Compare datetime objects
                if isinstance(post_date, datetime) and post_date >= since:
                    posts.append(post)

        for post in posts:
            post["id"] = str(post.pop("_id"))
            if isinstance(post.get("date"), datetime):
                post["date"] = post["date"].isoformat()

        return posts

    async def get_posts_by_channel(
        self, channel_username: str, since: datetime, user_id: int | None = None
    ) -> List[dict]:
        """Get posts for specific channel since given date.

        Args:
            channel_username: Channel username without @
            since: Minimum timestamp for posts
            user_id: Optional user ID to filter posts (if None, returns all posts for channel)

        Returns:
            List of post dictionaries
        """
        query: Dict[str, Any] = {
            "channel_username": channel_username,
            "date": {"$gte": since},
        }
        if user_id is not None:
            query["user_id"] = user_id

        # Log query for debugging
        from src.infrastructure.logging import get_logger

        logger = get_logger("post_repository")
        logger.debug(
            f"Querying posts from database: channel={channel_username}, "
            f"user_id={user_id}, since={since.isoformat()}"
        )

        cursor = self._db.posts.find(query).sort("date", 1)  # Sort from old to new
        posts = await cursor.to_list(length=1000)

        logger.info(
            f"Found {len(posts)} posts in database: channel={channel_username}, "
            f"user_id={user_id}, since={since.isoformat()}"
        )

        for post in posts:
            post["id"] = str(post.pop("_id"))
            if isinstance(post.get("date"), datetime):
                post["date"] = post["date"].isoformat()

        return posts

    async def _check_duplicate_by_message_id(
        self, channel_username: str, message_id: str, hours: int = 24
    ) -> bool:
        """Check if message_id exists in last N hours for this channel.

        Args:
            channel_username: Channel username
            message_id: Message ID to check
            hours: Time window in hours (default 24)

        Returns:
            True if duplicate found, False otherwise
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        existing = await self._db.posts.find_one(
            {
                "channel_username": channel_username,
                "message_id": message_id,
                "date": {"$gte": since},
            }
        )
        return existing is not None

    async def _check_duplicate_by_content_hash(
        self, content_hash: str, days: int = 7
    ) -> bool:
        """Check if content_hash exists in last N days.

        Args:
            content_hash: Content hash to check
            days: Time window in days (default 7)

        Returns:
            True if duplicate found, False otherwise
        """
        since = datetime.utcnow() - timedelta(days=days)
        existing = await self._db.posts.find_one(
            {"content_hash": content_hash, "date": {"$gte": since}}
        )
        return existing is not None

    async def delete_old_posts(self, days: int = 7) -> int:
        """Cleanup old posts older than specified days.

        Args:
            days: Number of days to keep (default 7)

        Returns:
            Number of deleted posts
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self._db.posts.delete_many({"date": {"$lt": cutoff}})
        return result.deleted_count

    @staticmethod
    def _calculate_content_hash(text: str, channel_username: str) -> str:
        """Calculate SHA256 hash of text + channel_username.

        Args:
            text: Post text content
            channel_username: Channel username

        Returns:
            Hex digest of SHA256 hash
        """
        content = f"{text}{channel_username}"
        return hashlib.sha256(content.encode()).hexdigest()
