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
        title: Optional channel title (overrides Telegram metadata if provided)
        description: Optional channel description (overrides Telegram metadata if provided)

    Returns:
        Dict with channel_id and status
    """
    from src.presentation.mcp.tools.channels.channel_metadata import get_channel_metadata
    from src.infrastructure.logging import get_logger
    
    logger = get_logger("channel_management")
    
    db = await get_database()
    channel_username = channel_username.lstrip("@")
    
    # Check if channel already exists (only active channels)
    existing = await db.channels.find_one({
        "user_id": user_id, 
        "channel_username": channel_username,
        "active": True
    })
    if existing:
        # Always fetch fresh metadata from Telegram API if not provided
        if title is None or description is None:
            try:
                logger.info(f"Fetching fresh metadata for existing channel: {channel_username}")
                metadata = await get_channel_metadata(channel_username, user_id=user_id)
                if metadata.get("success"):
                    # Use provided values or fallback to Telegram metadata
                    final_title = title if title is not None else metadata.get("title")
                    final_description = description if description is not None else metadata.get("description")
                    
                    update_fields = {}
                    if final_title and final_title != existing.get("title"):
                        update_fields["title"] = final_title
                    if final_description is not None and final_description != existing.get("description"):
                        update_fields["description"] = final_description
                    
                    if update_fields:
                        await db.channels.update_one(
                            {"_id": existing["_id"]}, 
                            {"$set": update_fields}
                        )
                        logger.info(f"Updated existing channel metadata: {channel_username}, fields={update_fields.keys()}")
            except Exception as e:
                logger.warning(f"Failed to fetch metadata for existing channel {channel_username}: {e}")
        
        # Update metadata if explicitly provided
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

    # New channel subscription - ALWAYS validate channel exists via Telegram API
    # This ensures we don't subscribe to invalid/non-existent channels
    telegram_title = title
    telegram_description = description
    metadata_valid = False
    
    # Always fetch metadata from Telegram API to validate channel exists
    try:
        logger.info(f"Validating channel via Telegram API: {channel_username}")
        metadata = await get_channel_metadata(channel_username, user_id=user_id)
        
        logger.debug(
            f"Metadata response: success={metadata.get('success')}, "
            f"title={metadata.get('title')}, "
            f"error={metadata.get('error')}, "
            f"full_response={metadata}"
        )
        
        if metadata.get("success"):
            metadata_valid = True
            # Use provided values or fallback to Telegram metadata
            telegram_title = title if title is not None else metadata.get("title")
            telegram_description = description if description is not None else metadata.get("description")
            
            # Validate that we got a valid title (required)
            if not telegram_title or not telegram_title.strip():
                logger.warning(
                    f"Channel {channel_username} has no title, cannot subscribe. "
                    f"metadata={metadata}"
                )
                metadata_valid = False
            else:
                logger.info(
                    f"Channel validated: {channel_username}, "
                    f"title={telegram_title}, has_description={bool(telegram_description)}"
                )
        else:
            error_msg = metadata.get("error", "unknown error")
            logger.warning(
                f"Failed to validate channel via Telegram API: {channel_username}, "
                f"error={error_msg}, full_metadata={metadata}"
            )
    except Exception as e:
        logger.error(
            f"Error validating channel {channel_username}: {e}",
            exc_info=True
        )
    
    # If metadata validation failed, don't subscribe
    if not metadata_valid:
        error_message = (
            f"Не удалось подтвердить существование канала '{channel_username}'. "
            f"Проверьте правильность username канала."
        )
        logger.error(f"Cannot subscribe to invalid channel: {channel_username}")
        return {
            "status": "error",
            "error": "channel_validation_failed",
            "message": error_message
        }

    # Channel is valid, proceed with subscription
    channel_doc = {
        "user_id": user_id,
        "channel_username": channel_username,
        "tags": tags or [],
        "subscribed_at": datetime.utcnow().isoformat(),
        "last_digest": None,
        "active": True,
        "title": telegram_title,
    }
    
    if telegram_description:
        channel_doc["description"] = telegram_description
    
    result = await db.channels.insert_one(channel_doc)
    logger.info(
        f"Subscribed to validated channel: {channel_username}, title={telegram_title}"
    )
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

