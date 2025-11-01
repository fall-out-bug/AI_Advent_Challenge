"""Channel metadata retrieval tool.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from pathlib import Path
from typing import Any, Dict, Optional

from src.presentation.mcp.server import mcp
from src.infrastructure.logging import get_logger

logger = get_logger("channel_metadata")


@mcp.tool()
async def get_channel_metadata(channel_username: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get Telegram channel metadata (title, description, subscribers count, etc.).
    
    Args:
        channel_username: Channel username without @ (e.g., "naboki" or "onaboka")
        user_id: Optional Telegram user ID (used for logging context)
    
    Returns:
        Dict with channel metadata (title, description, member_count, etc.) or error information
    """
    channel_username = channel_username.lstrip("@")
    
    try:
        try:
            import pyrogram
        except ImportError:
            return {
                "error": "Pyrogram not available",
                "channel_username": channel_username,
                "message": "Cannot fetch channel metadata without Pyrogram"
            }
        
        import os
        from pyrogram import Client
        from pyrogram.errors import BadRequest
        
        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        
        if not session_string or not api_id or not api_hash:
            return {
                "error": "Telegram credentials not configured",
                "channel_username": channel_username
            }
        
        sessions_dir = Path("/app/sessions")
        
        client = Client(
            "butler_client",
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session_string,
            workdir=str(sessions_dir) if sessions_dir.exists() else None
        )
        
        await client.start()
        
        try:
            channel = await client.get_chat(channel_username)
            
            metadata = {
                "channel_username": channel_username,
                "title": channel.title if hasattr(channel, 'title') else None,
                "description": channel.description if hasattr(channel, 'description') else None,
                "member_count": channel.members_count if hasattr(channel, 'members_count') else None,
                "chat_id": channel.id if hasattr(channel, 'id') else None,
                "is_verified": channel.is_verified if hasattr(channel, 'is_verified') else None,
                "is_scam": channel.is_scam if hasattr(channel, 'is_scam') else None,
                "is_fake": channel.is_fake if hasattr(channel, 'is_fake') else None,
                "username": channel.username if hasattr(channel, 'username') else None,
            }
            
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            logger.info("Fetched channel metadata", channel=channel_username, title=metadata.get("title"))
            return {"success": True, **metadata}
            
        except BadRequest as e:
            logger.warning("Channel not found", channel=channel_username, error=str(e))
            return {
                "error": "Channel not found",
                "channel_username": channel_username,
                "message": f"Channel @{channel_username} not found or not accessible"
            }
        finally:
            if client.is_connected:
                await client.stop()
            
    except Exception as e:
        logger.error("Error fetching channel metadata", channel=channel_username, error=str(e), exc_info=True)
        return {
            "error": str(e),
            "channel_username": channel_username,
            "message": f"Failed to fetch metadata for channel @{channel_username}"
        }

