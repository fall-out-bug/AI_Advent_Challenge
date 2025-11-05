"""Channel metadata retrieval tool.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

import os
from typing import Any, Dict, Optional

from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database
from src.infrastructure.logging import get_logger

logger = get_logger("channel_metadata")


def _looks_like_title(text: str) -> bool:
    """Check if text looks like a title rather than username."""
    if not text:
        return False
    has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in text)
    has_spaces = " " in text
    is_long = len(text) > 20
    return has_cyrillic or has_spaces or is_long


async def _search_channel_in_db(
    db, channel_username: str, user_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Search channel in database by username or title.
    
    Purpose:
        Search for channel in MongoDB using multiple strategies:
        1. Exact username match
        2. Case-insensitive username match
        3. Title match (if input looks like a title)
        4. Partial title match
    
    Args:
        db: MongoDB database instance
        channel_username: Channel username or title to search
        user_id: Optional user ID to filter by subscription
    
    Returns:
        Channel document if found, None otherwise
    """
    input_is_title = _looks_like_title(channel_username)
    channel = None

    # Build query: try exact match first, then case-insensitive
    query = {"channel_username": channel_username}
    if user_id is not None:
        query["user_id"] = user_id

    # If input looks like a title, search by title first
    if input_is_title and user_id is not None:
        all_channels = await db.channels.find(
            {"user_id": user_id, "active": True}
        ).to_list(length=100)
        input_lower = channel_username.lower().strip()
        for ch in all_channels:
            ch_title = ch.get("title", "").lower().strip()
            ch_username = ch.get("channel_username", "").lower().strip()
            if ch_title == input_lower or ch_username == input_lower:
                channel = ch
                if _looks_like_title(ch.get("channel_username", "")):
                    channel = None
                    break
                logger.info(
                    f"Found channel by title match: input='{channel_username}', "
                    f"found_username='{ch.get('channel_username')}'"
                )
                break

    # Try exact match by username
    if not channel:
        channel = await db.channels.find_one(query)

    # If not found and user_id provided, try without user_id filter
    if not channel and user_id is not None:
        channel = await db.channels.find_one({"channel_username": channel_username})

    # If still not found, try case-insensitive match by username
    if not channel:
        all_channels = await db.channels.find({}).to_list(length=100)
        for ch in all_channels:
            if ch.get("channel_username", "").lower() == channel_username.lower():
                channel = ch
                break

    # If still not found, try searching by title (exact or prefix match)
    if not channel and user_id is not None:
        all_channels = await db.channels.find(
            {"user_id": user_id, "active": True}
        ).to_list(length=100)
        input_lower = channel_username.lower().strip()
        for ch in all_channels:
            ch_title = ch.get("title", "").lower().strip()
            if ch_title:
                if ch_title == input_lower:
                    channel = ch
                    logger.info(
                        f"Found channel by exact title match: input='{channel_username}', "
                        f"found_username='{channel.get('channel_username')}', "
                        f"title='{channel.get('title')}'"
                    )
                    break
                if (
                    ch_title.startswith(input_lower)
                    and len(ch_title) - len(input_lower) < 20
                ):
                    channel = ch
                    logger.info(
                        f"Found channel by prefix title match: input='{channel_username}', "
                        f"found_username='{channel.get('channel_username')}', "
                        f"title='{channel.get('title')}'"
                    )
                    break

    return channel


async def _fetch_metadata_from_telegram(
    channel_username: str,
) -> Optional[Dict[str, Any]]:
    """Fetch channel metadata from Telegram API using Pyrogram.

    Args:
        channel_username: Channel username without @

    Returns:
        Dict with title, description, or None if failed
    """
    try:
        # Lazy import to avoid event loop issues at module load time
        from pyrogram import Client
        from pyrogram.errors import BadRequest, FloodWait, UsernameNotOccupied

        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")

        if not session_string or not api_id or not api_hash:
            logger.debug(
                f"Telegram credentials not configured, skipping API fetch for {channel_username}"
            )
            return None

        # Use unique client name to avoid conflicts with concurrent requests
        import uuid

        client_name = f"butler_metadata_{uuid.uuid4().hex[:8]}"

        client = Client(
            client_name,
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session_string,
            no_updates=True,  # Don't process updates in background
        )

        await client.start()
        try:
            chat = await client.get_chat(channel_username)

            # Validate that we got a valid channel/group
            if not hasattr(chat, "title") or not chat.title:
                logger.warning(
                    f"Channel {channel_username} has no title, might be invalid"
                )
                return None

            # Validate username matches (if channel has username)
            if hasattr(chat, "username") and chat.username:
                if chat.username.lower() != channel_username.lower():
                    logger.warning(
                        f"Username mismatch: requested '{channel_username}', "
                        f"got '{chat.username}'"
                    )

            metadata = {
                "title": getattr(chat, "title", None) or "",
                "description": getattr(chat, "description", None) or "",
                "username": getattr(chat, "username", None) or "",
            }

            logger.info(
                f"Fetched metadata from Telegram for {channel_username}: "
                f"title={metadata.get('title')}, username={metadata.get('username')}"
            )
            return metadata
        except UsernameNotOccupied:
            logger.warning(f"Channel username not occupied: {channel_username}")
            return None
        except BadRequest as e:
            logger.warning(
                f"Bad request for channel {channel_username}: {e}", exc_info=True
            )
            return None
        except FloodWait as e:
            logger.warning(
                f"FloodWait for channel {channel_username}: wait {e.value} seconds"
            )
            return None
        except Exception as e:
            logger.warning(
                f"Failed to fetch metadata from Telegram for {channel_username}: {e}",
                exc_info=True,
            )
            return None
        finally:
            if client.is_connected:
                await client.stop()
    except Exception as e:
        logger.warning(
            f"Failed to initialize Pyrogram client for {channel_username}: {e}",
            exc_info=True,
        )
        return None


@mcp.tool()
async def get_channel_metadata(
    channel_username: str, user_id: Optional[int] = None
) -> Dict[str, Any]:
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

        # Search channel in database using helper function
        channel = await _search_channel_in_db(db, channel_username, user_id)

        # If still not found, try to search via Telegram API (input might be a title)
        if not channel:
            logger.info(
                f"Channel not found in database by username or title, searching Telegram: {channel_username}"
            )
            try:
                from src.infrastructure.clients.telegram_utils import (
                    search_channels_by_name,
                )

                search_results = await search_channels_by_name(
                    channel_username, limit=1
                )
                if search_results:
                    # Found via Telegram search - use the username from search result
                    found_username = search_results[0]["username"]
                    # Try to find in database by the found username
                    if user_id is not None:
                        channel = await db.channels.find_one(
                            {"channel_username": found_username, "user_id": user_id}
                        )
                    if not channel:
                        channel = await db.channels.find_one(
                            {"channel_username": found_username}
                        )

                    if channel:
                        logger.info(
                            f"Found channel via Telegram search: input='{channel_username}', "
                            f"found_username='{found_username}'"
                        )
                    else:
                        # Channel exists in Telegram but not in our database
                        # Return the search result metadata
                        return {
                            "success": True,
                            "channel_username": found_username,
                            "title": search_results[0]["title"],
                            "description": search_results[0].get("description", ""),
                            "message": f"Channel found in Telegram but not in database: @{found_username}",
                        }
            except Exception as search_error:
                logger.debug(
                    f"Telegram search failed for '{channel_username}': {search_error}"
                )

        if not channel:
            logger.warning(
                f"Channel not found in database or Telegram: {channel_username}"
            )
            return {
                "success": False,
                "channel_username": channel_username,
                "error": "Channel not found in database or Telegram",
                "message": f"Channel @{channel_username} not found in database or Telegram",
            }

        # Extract metadata from channel document
        title = channel.get("title")
        description = channel.get("description")
        db_username = channel.get("channel_username", "")

        # Check if channel_username in DB looks like a title (not a valid username)
        # If so, we need to search Telegram to find the real username
        db_username_is_title = _looks_like_title(db_username)

        # If DB username is a title, we can't use it for Telegram API
        # Need to search Telegram by title to find real username
        if db_username_is_title:
            logger.warning(
                f"Channel username in DB looks like a title: '{db_username}', "
                f"searching Telegram for real username"
            )
            try:
                from src.infrastructure.clients.telegram_utils import (
                    search_channels_by_name,
                )

                # Use title from DB or input as search query
                search_query = title or db_username or channel_username
                search_results = await search_channels_by_name(search_query, limit=1)
                if search_results:
                    found_username = search_results[0]["username"]
                    found_title = search_results[0]["title"]
                    found_description = search_results[0].get("description", "")

                    # Update DB with correct username and metadata
                    await db.channels.update_one(
                        {"_id": channel.get("_id")},
                        {
                            "$set": {
                                "channel_username": found_username,
                                "title": found_title,
                                "description": found_description,
                            }
                        },
                    )
                    logger.info(
                        f"Updated channel in DB: old_username='{db_username}', "
                        f"new_username='{found_username}'"
                    )

                    # Return updated metadata
                    return {
                        "success": True,
                        "channel_username": found_username,
                        "title": found_title,
                        "description": found_description,
                        "message": f"Updated channel username from '{db_username}' to '{found_username}'",
                    }
                else:
                    # Search didn't find channel - can't return valid username
                    logger.error(
                        f"Channel username in DB is a title '{db_username}', but Telegram search "
                        f"didn't find matching channel. Cannot return valid username."
                    )
                    return {
                        "success": False,
                        "channel_username": db_username,  # Keep original for reference
                        "error": "channel_username_is_title_and_search_failed",
                        "message": (
                            f"Channel username in database is a title ('{db_username}'), "
                            f"but Telegram search didn't find matching channel. "
                            f"Please update channel_username manually."
                        ),
                    }
            except Exception as e:
                logger.error(
                    f"Failed to search Telegram for channel with title '{db_username}': {e}",
                    exc_info=True,
                )
                # Return error - can't proceed with title as username
                return {
                    "success": False,
                    "channel_username": db_username,
                    "error": "telegram_search_failed",
                    "message": (
                        f"Channel username in database is a title ('{db_username}'), "
                        f"but failed to search Telegram for real username: {e}"
                    ),
                }

        # Validate title is not actually description (too long or contains description-like text)
        if title and len(title) > 100:
            # Likely description, not title - fetch fresh metadata
            logger.warning(
                f"Channel {db_username} title looks like description (too long), "
                f"fetching fresh metadata"
            )
            title = None

        # If metadata is missing, fetch from Telegram API
        # But only if we have a valid username (not a title)
        if not title and not db_username_is_title:
            logger.info(
                f"Channel {db_username} missing title, fetching from Telegram API..."
            )
            telegram_metadata = await _fetch_metadata_from_telegram(db_username)

            if telegram_metadata:
                title = telegram_metadata.get("title")
                description = telegram_metadata.get("description") or description

                # Save metadata to DB for future use
                update_result = await db.channels.update_one(
                    {"_id": channel.get("_id")},
                    {"$set": {"title": title, "description": description}},
                )
                logger.info(
                    f"Updated channel {channel_username} in DB with metadata from Telegram: title={title}, modified={update_result.modified_count}"
                )

        # Build response metadata
        # Use corrected username from DB (may have been updated above)
        final_username = channel.get("channel_username", channel_username)
        metadata = {
            "success": True,
            "channel_username": final_username,
            "title": title or "",
            "description": description or "",
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
        logger.error(
            f"Error fetching channel metadata: channel={channel_username}, error={str(e)}",
            exc_info=True,
        )
        return {
            "success": False,
            "error": str(e),
            "channel_username": channel_username,
            "message": f"Failed to fetch metadata for channel @{channel_username}",
        }
