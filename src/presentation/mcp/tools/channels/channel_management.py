"""Channel subscription management tools.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database


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
    db = await get_database()
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
    db = await get_database()
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
    db = await get_database()
    result = await db.channels.update_one(
        {"_id": ObjectId(channel_id), "user_id": user_id}, {"$set": {"active": False}}
    )
    if result.modified_count > 0:
        return {"status": "deleted", "channel_id": channel_id}
    return {"status": "not_found", "channel_id": channel_id}

