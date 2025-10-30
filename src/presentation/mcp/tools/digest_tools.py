"""MCP tools for channel digests backed by MongoDB."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from bson import ObjectId
from src.presentation.mcp.server import mcp
from src.infrastructure.database.mongo import get_db
from src.infrastructure.clients.telegram_utils import fetch_channel_posts
from src.infrastructure.llm.summarizer import summarize_posts


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

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with digests list
    """
    db = await _db()
    channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(length=100)
    digests = []
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    from src.infrastructure.monitoring.logger import get_logger
    logger = get_logger(name="digest_tools")
    
    for channel in channels:
        channel_name = channel["channel_username"]
        logger.debug("Processing channel", channel=channel_name, user_id=user_id)
        try:
            posts = await fetch_channel_posts(channel_name, since=cutoff_time)
            logger.debug("Fetched posts", channel=channel_name, post_count=len(posts))
            if not posts:
                logger.debug("No posts found", channel=channel_name, cutoff_time=cutoff_time.isoformat())
                continue

            # Use settings-based summarization (defaults to 1 sentence, configurable)
            from src.infrastructure.config.settings import get_settings
            settings = get_settings()
            summary = await summarize_posts(posts, max_sentences=settings.digest_summary_sentences)
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

