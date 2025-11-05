"""Post collection and retrieval tools.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database, guess_usernames_from_human_name
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.logging import get_logger
from src.presentation.mcp.tools.channels.channel_metadata import get_channel_metadata

logger = get_logger("posts_management")


@mcp.tool()
async def get_posts(
    channel_username: str,
    hours: int = 24,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """Get posts for a specific channel from MongoDB for the last N hours.

    Args:
        channel_username: Channel username without @
        hours: Lookback window in hours
        user_id: Optional user id for logging context

    Returns:
        Dict with posts_count and data list
    """
    db = await get_database()

    now = datetime.now(tz=timezone.utc)
    date_from = now - timedelta(hours=max(0, int(hours)))

    cursor = db.posts.find({
        "channel_username": channel_username.lstrip("@"),
        "date": {"$gte": date_from.isoformat()}
    }).sort("date", -1)

    posts = await cursor.to_list(length=1000)
    posts_count = len(posts)

    logger.debug(f"get_posts: channel={channel_username}, hours={hours}, posts_count={posts_count}")
    return {
        "status": "success",
        "channel_username": channel_username,
        "hours": hours,
        "posts_count": posts_count,
        "data": posts,
    }


async def _fetch_and_save_posts(
    client: "Client",  # Pyrogram Client - lazy import
    channel_username: str,
    user_id: Optional[int],
    window_hours: int
) -> int:
    """Fetch posts from Telegram and save to database.
    
    Args:
        client: Pyrogram client instance
        channel_username: Channel username
        user_id: User ID for posts
        window_hours: Hours to look back
        
    Returns:
        Number of posts saved
    """
    db = await get_database()
    repo = PostRepository(db)
    now = datetime.now(tz=timezone.utc)
    since = now - timedelta(hours=max(1, int(window_hours)))

    count = 0
    async for msg in client.get_chat_history(channel_username, limit=1000):
        try:
            msg_dt = getattr(msg, "date", None)
            if msg_dt and msg_dt.replace(tzinfo=timezone.utc) < since:
                break
            text = getattr(msg, "text", None) or getattr(msg, "caption", "") or ""
            if not text:
                continue
            post = {
                "channel_username": channel_username,
                "message_id": str(getattr(msg, "id", "")),
                "text": text,
                "user_id": user_id,
                "date": msg_dt or now,
                "views": getattr(msg, "views", None),
                "metadata": {},
            }
            post_id = await repo.save_post(post)
            if post_id:
                count += 1
        except Exception:
            continue
    return count


@mcp.tool()
async def collect_posts(
    channel_username: str,
    user_id: Optional[int] = None,
    wait_for_completion: bool = False,
    timeout_seconds: int = 30,
    hours: int = 72,
    fallback_to_7_days: bool = True,
) -> Dict[str, Any]:
    """Collect posts for a channel via Pyrogram and save them to MongoDB.

    Args:
        channel_username: Channel username without @
        user_id: Optional user id (for logging)
        wait_for_completion: If true, fetch synchronously and return result
        timeout_seconds: Max time budget for synchronous fetch
        hours: Lookback window; default 72
        fallback_to_7_days: If true and nothing fetched, retry with 168h

    Returns:
        Dict with status, collected_count, and channel_username
    """
    channel_username = channel_username.lstrip("@")
    logger.info(
        f"collect_posts invoked: channel={channel_username}, user_id={user_id}, "
        f"wait={wait_for_completion}, hours={hours}"
    )

    if not wait_for_completion:
        return {
            "status": "accepted",
            "job_id": f"collect_{channel_username}",
            "channel_username": channel_username,
            "hint": "Synchronous collection only; set wait_for_completion=true",
        }

    try:
        session_string = os.getenv("TELEGRAM_SESSION_STRING")
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")

        if not session_string or not api_id or not api_hash:
            return {
                "status": "error",
                "error": "telegram_config_missing",
                "message": "Telegram credentials not configured",
            }

        # Lazy import to avoid event loop issues at module load time
        from pyrogram import Client
        
        # Use unique client name to avoid conflicts with concurrent requests
        import uuid
        client_name = f"butler_posts_{uuid.uuid4().hex[:8]}"

        client = Client(
            client_name,
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session_string,
            no_updates=True,  # Don't process updates in background
        )

        await client.start()
        collected_total = 0
        try:
            # Resolve canonical username
            try:
                meta = await get_channel_metadata(channel_username, user_id=user_id)
                meta_username = (meta or {}).get("username")
                if meta_username:
                    channel_username = meta_username
            except Exception:
                pass

            # Try transliteration for non-ASCII usernames
            if any(ord(ch) > 127 for ch in channel_username):
                for cand in guess_usernames_from_human_name(channel_username):
                    try:
                        chat = await client.get_chat(cand)
                        channel_username = cand
                        break
                    except Exception:
                        continue

            collected = await _fetch_and_save_posts(client, channel_username, user_id, hours)
            collected_total += collected
            
            if collected == 0 and fallback_to_7_days and hours < 168:
                collected = await _fetch_and_save_posts(client, channel_username, user_id, 168)
                collected_total += collected

        finally:
            if client.is_connected:
                await client.stop()

        return {
            "status": "success",
            "channel_username": channel_username,
            "collected_count": collected_total,
            "hours": hours if collected_total else 168 if fallback_to_7_days else hours,
        }
    except Exception as e:
        logger.error(f"collect_posts failed: channel={channel_username}, error={str(e)}", exc_info=True)
        return {"status": "error", "error": str(e), "channel_username": channel_username}


@mcp.tool()
async def save_posts_to_db(posts: List[dict], channel_username: str, user_id: int) -> Dict[str, Any]:
    """Save fetched posts to MongoDB via repository with deduplication.

    Args:
        posts: List of post dictionaries with text, date, message_id, etc.
        channel_username: Channel username without @
        user_id: Telegram user ID

    Returns:
        Dict with saved, skipped, and total counts
    """
    saved_count = 0
    skipped_count = 0

    if not posts:
        return {"saved": 0, "skipped": 0, "total": 0}

    db = await get_database()
    repository = PostRepository(db)

    for post in posts:
        try:
            # Handle both "channel" and "channel_username" fields
            # Posts from telegram_utils have "channel" field with actual username
            # Posts from other sources may have "channel_username" field
            post_channel = post.get("channel") or post.get("channel_username") or channel_username
            
            post_with_metadata = {
                "channel_username": post_channel,  # Use actual username from post if available
                "message_id": post.get("message_id", ""),
                "text": post.get("text", ""),
                "user_id": user_id,
                "date": post.get("date", datetime.utcnow()),
                "views": post.get("views"),
                "metadata": post.get("metadata", {}),
            }

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
            logger.warning(f"Invalid post skipped: channel={channel_username}, error={str(e)}")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error saving post: channel={channel_username}, error={str(e)}", exc_info=True)
            skipped_count += 1

    return {"saved": saved_count, "skipped": skipped_count, "total": len(posts)}

