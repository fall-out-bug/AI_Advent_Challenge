"""MCP tools for channel digests backed by MongoDB."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from bson import ObjectId
from src.presentation.mcp.server import mcp
from src.infrastructure.database.mongo import get_db
from src.infrastructure.clients.telegram_utils import fetch_channel_posts
from src.infrastructure.llm.summarizer import summarize_posts
from src.infrastructure.repositories.post_repository import PostRepository


async def _db():
    """Get database handle."""
    return await get_db()


@mcp.tool()
async def add_channel(user_id: int, channel_username: str, tags: list[str] | None = None) -> Dict[str, Any]:
    """Subscribe to a Telegram channel for digest.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username without @
        tags: Optional annotation tags

    Returns:
        Dict with channel_id and status
    """
    db = await _db()
    existing = await db.channels.find_one({"user_id": user_id, "channel_username": channel_username})
    if existing:
        return {"channel_id": str(existing["_id"]), "status": "already_subscribed"}

    channel_doc = {
        "user_id": user_id,
        "channel_username": channel_username,
        "tags": tags or [],
        "subscribed_at": datetime.utcnow().isoformat(),
        "last_digest": None,
        "active": True,
    }
    result = await db.channels.insert_one(channel_doc)
    return {"channel_id": str(result.inserted_id), "status": "subscribed"}


@mcp.tool()
async def list_channels(user_id: int, limit: int = 100) -> Dict[str, Any]:
    """List user's subscribed channels.

    Args:
        user_id: Telegram user ID
        limit: Max channels to return

    Returns:
        Dict with channels list
    """
    db = await _db()
    limit = min(limit, 500)
    cursor = db.channels.find({"user_id": user_id, "active": True}).limit(limit)
    channels = await cursor.to_list(length=limit)
    for ch in channels:
        ch["id"] = str(ch.pop("_id"))
    return {"channels": channels, "total": len(channels)}


@mcp.tool()
async def delete_channel(user_id: int, channel_id: str) -> Dict[str, str]:
    """Unsubscribe from a channel.

    Args:
        user_id: Telegram user ID
        channel_id: Channel ID to delete

    Returns:
        Dict with status
    """
    db = await _db()
    result = await db.channels.update_one(
        {"_id": ObjectId(channel_id), "user_id": user_id}, {"$set": {"active": False}}
    )
    if result.modified_count > 0:
        return {"status": "deleted", "channel_id": channel_id}
    return {"status": "not_found", "channel_id": channel_id}


@mcp.tool()
async def get_channel_digest(user_id: int, hours: int = 24) -> Dict[str, Any]:
    """Generate digest from subscribed channels.

    Purpose:
        Read posts from MongoDB instead of fetching from Telegram API.
        Uses PostRepository to get posts for user's subscribed channels.

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with digests list
    """
    db = await _db()
    repository = PostRepository(db)
    channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(length=100)
    digests = []

    from src.infrastructure.monitoring.logger import get_logger
    logger = get_logger(name="digest_tools")
    
    # Get all posts for user's subscriptions from MongoDB
    try:
        all_posts = await repository.get_posts_by_user_subscriptions(user_id, hours=hours)
        logger.debug("Retrieved posts from MongoDB", user_id=user_id, post_count=len(all_posts))
    except Exception as e:
        logger.error("Error retrieving posts from MongoDB", user_id=user_id, error=str(e), exc_info=True)
        return {"digests": [], "generated_at": datetime.utcnow().isoformat()}
    
    # Group posts by channel
    posts_by_channel: Dict[str, List[dict]] = {}
    for post in all_posts:
        channel_name = post.get("channel_username")
        if channel_name:
            if channel_name not in posts_by_channel:
                posts_by_channel[channel_name] = []
            posts_by_channel[channel_name].append(post)
    
    # Process each channel
    for channel in channels:
        channel_name = channel["channel_username"]
        logger.debug("Processing channel", channel=channel_name, user_id=user_id)
        try:
            posts = posts_by_channel.get(channel_name, [])
            logger.debug("Found posts in database", channel=channel_name, post_count=len(posts))
            if not posts:
                logger.debug("No posts found", channel=channel_name)
                continue

            # Use settings-based summarization (defaults to 8 sentences, configurable)
            from src.infrastructure.config.settings import get_settings
            settings = get_settings()
            
            # Convert date strings back to datetime for summarizer if needed
            normalized_posts = []
            for post in posts:
                normalized_post = dict(post)
                if isinstance(normalized_post.get("date"), str):
                    try:
                        normalized_post["date"] = datetime.fromisoformat(normalized_post["date"].replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
                normalized_posts.append(normalized_post)
            
            summary = await summarize_posts(normalized_posts, max_sentences=settings.digest_summary_sentences)
            digests.append(
                {
                    "channel": channel_name,
                    "summary": summary,
                    "post_count": len(posts),
                    "tags": channel.get("tags", []),
                }
            )
            await db.channels.update_one({"_id": channel["_id"]}, {"$set": {"last_digest": datetime.utcnow().isoformat()}})
        except Exception as e:
            # Use standard logging formatting
            logger.error("Error processing channel %s: %s", channel_name, str(e), exc_info=True)
            # Continue with next channel even if one fails

    return {"digests": digests, "generated_at": datetime.utcnow().isoformat()}


@mcp.tool()
async def save_posts_to_db(posts: List[dict], channel_username: str, user_id: int) -> Dict[str, Any]:
    """Save fetched posts to MongoDB via repository with deduplication.

    Purpose:
        Save posts from Telegram channel to MongoDB with hybrid deduplication.
        Handles missing fields gracefully.

    Args:
        posts: List of post dictionaries with text, date, message_id, etc.
        channel_username: Channel username without @
        user_id: Telegram user ID

    Returns:
        Dict with saved, skipped, and total counts

    Example:
        >>> posts = [{"text": "Hello", "date": datetime.utcnow(), "message_id": "123"}]
        >>> result = await save_posts_to_db(posts, "test_channel", 1)
        >>> print(result)
        {"saved": 1, "skipped": 0, "total": 1}

    Raises:
        None: Errors are logged and handled gracefully
    """
    from src.infrastructure.monitoring.logger import get_logger

    logger = get_logger(name="digest_tools")
    saved_count = 0
    skipped_count = 0

    if not posts:
        return {"saved": 0, "skipped": 0, "total": 0}

    db = await _db()
    repository = PostRepository(db)

    for post in posts:
        try:
            # Ensure post has required fields
            post_with_metadata = {
                "channel_username": channel_username,
                "message_id": post.get("message_id", ""),
                "text": post.get("text", ""),
                "user_id": user_id,
                "date": post.get("date", datetime.utcnow()),
                "views": post.get("views"),
                "metadata": post.get("metadata", {}),
            }

            # Convert date string to datetime if needed
            if isinstance(post_with_metadata["date"], str):
                try:
                    post_with_metadata["date"] = datetime.fromisoformat(post_with_metadata["date"])
                except (ValueError, AttributeError):
                    post_with_metadata["date"] = datetime.utcnow()

            post_id = await repository.save_post(post_with_metadata)
            if post_id:
                saved_count += 1
            else:
                skipped_count += 1
        except ValueError as e:
            logger.warning("Invalid post skipped", error=str(e), channel=channel_username)
            skipped_count += 1
        except Exception as e:
            logger.error("Error saving post", error=str(e), channel=channel_username, exc_info=True)
            skipped_count += 1

    return {"saved": saved_count, "skipped": skipped_count, "total": len(posts)}

