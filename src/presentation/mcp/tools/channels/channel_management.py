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
async def add_channel(
    user_id: int, 
    channel_username: str, 
    tags: list[str] | None = None,
    title: str | None = None,
    description: str | None = None
) -> Dict[str, Any]:
    """Subscribe to a Telegram channel for digest.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username without @
        tags: Optional annotation tags
        title: Optional channel title (metadata)
        description: Optional channel description (metadata)

    Returns:
        Dict with channel_id and status
    """
    db = await get_database()
    existing = await db.channels.find_one({"user_id": user_id, "channel_username": channel_username})
    if existing:
        # Update metadata if provided
        update_fields = {}
        if title is not None:
            update_fields["title"] = title
        if description is not None:
            update_fields["description"] = description
        if update_fields:
            await db.channels.update_one(
                {"_id": existing["_id"]}, 
                {"$set": update_fields}
            )
        return {"channel_id": str(existing["_id"]), "status": "already_subscribed"}

    channel_doc = {
        "user_id": user_id,
        "channel_username": channel_username,
        "tags": tags or [],
        "subscribed_at": datetime.utcnow().isoformat(),
        "last_digest": None,
        "active": True,
    }
    
    # Add metadata if provided
    if title is not None:
        channel_doc["title"] = title
    if description is not None:
        channel_doc["description"] = description
    
    result = await db.channels.insert_one(channel_doc)
    return {"channel_id": str(result.inserted_id), "status": "subscribed"}


@mcp.tool()
async def list_channels(user_id: int, limit: int = 100) -> Dict[str, Any]:
    """List user's subscribed channels with metadata (title, description).

    Args:
        user_id: Telegram user ID
        limit: Max channels to return

    Returns:
        Dict with channels list (including title from metadata)
    """
    db = await get_database()
    limit = min(limit, 500)
    cursor = db.channels.find({"user_id": user_id, "active": True}).limit(limit)
    channels = await cursor.to_list(length=limit)
    
    # Enrich channels with metadata (title) if not present
    from src.presentation.mcp.tools.channels.channel_metadata import get_channel_metadata
    from src.infrastructure.logging import get_logger
    
    logger = get_logger("channel_management")
    
    for ch in channels:
        # Save _id before converting to string
        channel_id = ch.pop("_id")
        ch["id"] = str(channel_id)
        
        channel_username = ch.get("channel_username")
        current_title = ch.get("title")
        logger.info(f"Processing channel {channel_username}, has_title={bool(current_title)}, title={current_title}")
        
        # If channel doesn't have title (None, empty string, or missing), try to get it from metadata
        if not current_title or not current_title.strip():
            if channel_username:
                try:
                    logger.info(f"Channel {channel_username} missing title, calling get_channel_metadata...")
                    metadata = await get_channel_metadata(channel_username, user_id=user_id)
                    logger.info(f"get_channel_metadata result for {channel_username}: success={metadata.get('success')}, title={metadata.get('title')}")
                    if metadata.get("success") and metadata.get("title"):
                        # Update channel document with metadata
                        new_title = metadata.get("title", "").strip()
                        new_description = metadata.get("description", "").strip() if metadata.get("description") else ""
                        ch["title"] = new_title
                        ch["description"] = new_description
                        
                        # Also update in DB for future use (use original ObjectId)
                        update_result = await db.channels.update_one(
                            {"_id": channel_id, "user_id": user_id},
                            {"$set": {
                                "title": new_title,
                                "description": new_description
                            }}
                        )
                        logger.info(f"Updated channel {channel_username} in DB with metadata: title={new_title}, modified={update_result.modified_count}")
                    else:
                        logger.warning(f"get_channel_metadata failed for {channel_username}: success={metadata.get('success')}, error={metadata.get('error')}")
                except Exception as e:
                    logger.error(f"Failed to get metadata for {channel_username}: {e}", exc_info=True)
                    # Continue without metadata
        else:
            logger.debug(f"Channel {channel_username} already has title: {current_title}")
    
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

