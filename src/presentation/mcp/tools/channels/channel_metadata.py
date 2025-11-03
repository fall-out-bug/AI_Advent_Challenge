"""Channel metadata retrieval tool.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

import os
from typing import Any, Dict, Optional

from pyrogram import Client
from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database
from src.infrastructure.logging import get_logger

logger = get_logger("channel_metadata")


async def _fetch_metadata_from_telegram(channel_username: str) -> Optional[Dict[str, Any]]:
    """Fetch channel metadata from Telegram API using Pyrogram.
    
    Args:
        channel_username: Channel username without @
        
    Returns:
        Dict with title, description, or None if failed
    """
    try:
        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not session_string or not api_id or not api_hash:
            logger.debug(f"Telegram credentials not configured, skipping API fetch for {channel_username}")
            return None
        
        client = Client(
            "butler_client",
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session_string,
        )
        
        await client.start()
        try:
            chat = await client.get_chat(channel_username)
            metadata = {
                "title": getattr(chat, "title", None) or "",
                "description": getattr(chat, "description", None) or "",
            }
            logger.info(f"Fetched metadata from Telegram for {channel_username}: title={metadata.get('title')}")
            return metadata
        finally:
            if client.is_connected:
                await client.stop()
    except Exception as e:
        logger.debug(f"Failed to fetch metadata from Telegram for {channel_username}: {e}")
        return None


@mcp.tool()
async def get_channel_metadata(channel_username: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get channel metadata from database, fetching from Telegram API if needed.
    
    First tries to read metadata from MongoDB channels collection.
    If metadata not found or incomplete, fetches from Telegram API and saves to DB.
    
    Args:
        channel_username: Channel username without @ (e.g., "naboki" or "onaboka")
        user_id: Optional Telegram user ID (for filtering user's channels)
    
    Returns:
        Dict with channel metadata (title, description, etc.) or error information
    """
    channel_username = channel_username.lstrip("@")
    
    try:
        db = await get_database()
        
        # Build query: try exact match first, then case-insensitive
        query = {"channel_username": channel_username}
        if user_id is not None:
            query["user_id"] = user_id
        
        # Try exact match first
        channel = await db.channels.find_one(query)
        
        # If not found and user_id provided, try without user_id filter
        if not channel and user_id is not None:
            channel = await db.channels.find_one({"channel_username": channel_username})
        
        # If still not found, try case-insensitive match
        if not channel:
            all_channels = await db.channels.find({}).to_list(length=100)
            for ch in all_channels:
                if ch.get("channel_username", "").lower() == channel_username.lower():
                    channel = ch
                    break
        
        if not channel:
            logger.warning(f"Channel not found in database: {channel_username}")
            return {
                "success": False,
                "channel_username": channel_username,
                "error": "Channel not found in database",
                "message": f"Channel @{channel_username} not found in database"
            }
        
        # Extract metadata from channel document
        title = channel.get("title")
        description = channel.get("description")
        
        # If metadata is missing, fetch from Telegram API
        if not title:
            logger.info(f"Channel {channel_username} missing title, fetching from Telegram API...")
            telegram_metadata = await _fetch_metadata_from_telegram(channel_username)
            
            if telegram_metadata:
                title = telegram_metadata.get("title")
                description = telegram_metadata.get("description") or description
                
                # Save metadata to DB for future use
                update_result = await db.channels.update_one(
                    {"_id": channel.get("_id")},
                    {"$set": {
                        "title": title,
                        "description": description
                    }}
                )
                logger.info(f"Updated channel {channel_username} in DB with metadata from Telegram: title={title}, modified={update_result.modified_count}")
        
        # Build response metadata
        metadata = {
            "success": True,
            "channel_username": channel.get("channel_username", channel_username),
            "title": title,
            "description": description,
            "tags": channel.get("tags", []),
            "subscribed_at": channel.get("subscribed_at"),
            "active": channel.get("active", True),
        }
        
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        logger.info(
            f"Retrieved channel metadata: channel={channel_username}, title={metadata.get('title')}"
        )
        
        return metadata
            
    except Exception as e:
        logger.error(f"Error fetching channel metadata: channel={channel_username}, error={str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "channel_username": channel_username,
            "message": f"Failed to fetch metadata for channel @{channel_username}"
        }

