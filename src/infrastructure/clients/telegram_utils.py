"""Telegram client utilities for fetching channel posts.

Supports two methods:
1. Bot API (aiogram) - only works if bot is channel admin
2. MTProto client (Pyrogram) - works with user account for any public channel
"""

from __future__ import annotations

import os
import sys
import shutil
from datetime import datetime
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="telegram_utils")

# Try to import Pyrogram for MTProto access
try:
    from pyrogram import Client
    from pyrogram.errors import BadRequest, FloodWait
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logger.debug("Pyrogram not available, will use Bot API only")


async def _fetch_with_pyrogram(
    channel_username: str, 
    since: datetime,
    api_id: Optional[str] = None,
    api_hash: Optional[str] = None,
    session_string: Optional[str] = None
) -> List[dict]:
    """Fetch channel posts using Pyrogram (MTProto) with user account.
    
    Args:
        channel_username: Channel username without @
        since: Minimum timestamp for posts
        api_id: Telegram API ID (from https://my.telegram.org)
        api_hash: Telegram API hash
        session_string: Pyrogram session string (if session already exists)
        
    Returns:
        List of post dictionaries
    """
    if not PYROGRAM_AVAILABLE:
        raise ImportError("Pyrogram not installed. Install with: pip install pyrogram")
    
    api_id = api_id or os.getenv("TELEGRAM_API_ID")
    api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for Pyrogram")
    # Try to get session string from env or use existing session file
    session_string = session_string or os.getenv("TELEGRAM_SESSION_STRING")
    session_name = "telegram_channel_reader"
    
    # Only look for session file if session_string is not available
    session_file = None
    if not session_string:
        # Check multiple possible locations for session file
        possible_session_paths = [
            f"{session_name}.session",
            f"sessions/{session_name}.session",
            f"/app/sessions/{session_name}.session",
            os.path.expanduser(f"~/{session_name}.session"),
        ]
        
        for path in possible_session_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                session_file = abs_path
                logger.info("Found existing Pyrogram session file", session_file=session_file)
                break
    
    if not session_string and not session_file:
        logger.warning("No Pyrogram session found. Placeholder posts will be used.")
    
    posts = []
    client = None
    
    try:
        # Format channel username
        channel_id = channel_username if channel_username.startswith("@") else f"@{channel_username}"
        
        # Create client (will use existing session if available)
        # If session_string is available, use it directly (no file needed)
        # Otherwise, copy session file to temp directory for write access
        temp_session_path = None
        original_cwd = None
        
        if session_string:
            # Use session string directly - no file needed
            logger.info("Using Pyrogram session string (no file needed)", has_string=bool(session_string), channel=channel_username)
            client_session_name = session_name  # Name doesn't matter when using session_string
        elif session_file and os.path.exists(session_file):
            # Copy session file to current working directory so Pyrogram can write to it
            # Pyrogram SQLite needs write access for WAL files
            try:
                original_cwd = os.getcwd()
                # Use /tmp or current directory for temporary session copy
                temp_session_dir = "/tmp" if os.path.exists("/tmp") else original_cwd
                temp_session_path = os.path.join(temp_session_dir, f"{session_name}.session")
                
                # Copy session file if it doesn't exist or is older
                if not os.path.exists(temp_session_path) or os.path.getmtime(session_file) > os.path.getmtime(temp_session_path):
                    shutil.copy2(session_file, temp_session_path)
                    logger.debug(f"Copied session file to {temp_session_path}")
                else:
                    logger.debug(f"Using existing session file at {temp_session_path}")
                
                # Change to temp directory so Pyrogram can find the file
                os.chdir(temp_session_dir)
                logger.debug(f"Changed working directory to {temp_session_dir}")
                client_session_name = session_name
            except Exception as e:
                logger.warning(f"Failed to copy session file: {e}, trying direct path")
                client_session_name = session_name
                original_cwd = None
        else:
            client_session_name = session_name
        
        client = Client(
            client_session_name,
            api_id=int(api_id),
            api_hash=api_hash,
            session_string=session_string,
            no_updates=True,  # Don't process updates in background
        )
        
        # Try to start client (will use existing session if available)
        try:
            await client.start()
            logger.info("Pyrogram client started successfully", channel=channel_username)
        except Exception as start_error:
            # If session doesn't exist and no session_string provided, log error
            if "phone number" in str(start_error).lower() or "verification code" in str(start_error).lower():
                logger.error(
                    "Pyrogram session not initialized. Please run init_pyrogram.py script first.",
                    channel=channel_username,
                    error=str(start_error)
                )
                raise ValueError(
                    "Pyrogram session not initialized. "
                    "Set TELEGRAM_SESSION_STRING env var or run scripts/init_pyrogram.py"
                ) from start_error
            raise
        
        # Get channel entity
        try:
            channel = await client.get_chat(channel_id)
            logger.info("Channel found via Pyrogram", channel=channel_username, chat_id=channel.id)
        except BadRequest as e:
            logger.warning("Channel not found via Pyrogram", channel=channel_username, error=str(e))
            return []
        
        # Fetch messages (limit to last 100 messages for performance)
        messages = []
        try:
            logger.debug("Starting to fetch messages", channel=channel_username, since=since.isoformat(), limit=100)
            async for message in client.get_chat_history(channel.id, limit=100):
                if message.date >= since:
                    messages.append(message)
                else:
                    break  # Messages are in reverse chronological order
            logger.debug("Finished fetching messages", channel=channel_username, messages_fetched=len(messages))
        except FloodWait as e:
            logger.warning(f"FloodWait: need to wait {e.value} seconds", channel=channel_username)
            # Return what we have so far
            pass
        except Exception as fetch_error:
            error_msg = str(fetch_error)
            logger.error(
                "Error fetching messages from channel",
                channel=channel_username,
                error=error_msg,
                error_type=type(fetch_error).__name__,
                exc_info=True
            )
            # If session is invalid, log it clearly
            if "EOF" in error_msg or "session" in error_msg.lower() or "auth" in error_msg.lower():
                logger.error(
                    "Pyrogram session appears to be invalid or expired",
                    channel=channel_username,
                    session_file=session_file,
                    has_session_string=bool(session_string)
                )
            # Return empty list - don't raise, let caller handle it
            pass
        
        # Convert messages to our format
        logger.debug("Converting messages to post format", channel=channel_username, message_count=len(messages))
        for msg in messages:
            text = ""
            if msg.text:
                text = msg.text
            elif msg.caption:
                text = msg.caption
            elif msg.photo or msg.video or msg.document:
                text = f"[Media: {msg.media.__class__.__name__}]"
            
            if text:
                posts.append({
                    "text": text,
                    "date": msg.date.isoformat(),
                    "channel": channel_username,
                    "message_id": str(msg.id),
                    "views": getattr(msg, "views", None),
                })
        
        logger.info("Fetched posts via Pyrogram", channel=channel_username, count=len(posts), since=since.isoformat())
        if len(posts) == 0:
            logger.info("No posts found in time window", channel=channel_username, since=since.isoformat(), now=datetime.utcnow().isoformat())
            logger.debug("Messages fetched but no posts converted", channel=channel_username, messages_fetched=len(messages))
        return posts
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Error fetching posts via Pyrogram", channel=channel_username, error=error_msg, error_type=type(e).__name__, exc_info=True)
        # If session error, log it clearly
        if "phone number" in error_msg.lower() or "verification code" in error_msg.lower() or "session" in error_msg.lower():
            logger.error(
                "Pyrogram session invalid - need to reinitialize",
                channel=channel_username,
                session_file=session_file,
                has_session_string=bool(session_string)
            )
        return []
    finally:
        if client and client.is_connected:
            await client.stop()
        
        # Restore original working directory if changed
        if original_cwd:
            try:
                os.chdir(original_cwd)
                logger.debug(f"Restored working directory to {original_cwd}")
            except Exception as e:
                logger.warning(f"Failed to restore working directory: {e}")
        
        # Copy updated session file back to original location if it was copied
        if temp_session_path and os.path.exists(temp_session_path) and session_file:
            try:
                # Copy back updated session file
                shutil.copy2(temp_session_path, session_file)
                logger.debug(f"Copied updated session file back to {session_file}")
            except Exception as e:
                logger.warning(f"Failed to copy session file back: {e}")


async def fetch_channel_posts(channel_username: str, since: datetime, user_id: int | None = None, save_to_db: bool = True) -> List[dict]:
    """Fetch recent posts from a Telegram channel.
    
    Tries multiple methods:
    1. Pyrogram (MTProto) - if API credentials are available
    2. Bot API (aiogram) - if bot is channel admin
    3. Placeholder posts - fallback for testing

    Purpose:
        Retrieve channel posts since a given datetime for digest generation.
        Optionally saves posts to MongoDB if save_to_db is True and user_id is provided.

    Args:
        channel_username: Channel username without @
        since: Minimum timestamp for posts
        user_id: Optional user ID for saving posts to database
        save_to_db: Whether to automatically save posts to database (default True)

    Returns:
        List of post dictionaries with text, date, etc.
    """
    posts = []
    
    # Try Pyrogram first (works for any public channel with user account)
    if PYROGRAM_AVAILABLE and os.getenv("TELEGRAM_API_ID") and os.getenv("TELEGRAM_API_HASH"):
        try:
            posts = await _fetch_with_pyrogram(channel_username, since)
            # Return posts even if empty - Pyrogram worked, just no posts found
            logger.info("Pyrogram fetch completed", channel=channel_username, count=len(posts), since=since.isoformat())
        except Exception as e:
            logger.warning(f"Pyrogram fetch failed: {e}, trying Bot API", channel=channel_username, exc_info=True)
    
    # Fallback to Bot API only if Pyrogram is not available
    # Bot API cannot fetch message history, so we return empty list instead of placeholder
    if not posts:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set, cannot fetch channel posts")
            return []
        
        # Bot API doesn't provide direct message history access
        # Only admins can access messages, but there's no direct API method
        # So we can't fetch real posts via Bot API without admin rights
        logger.info("Pyrogram not available or failed, Bot API cannot fetch posts", channel=channel_username)
        logger.info("Returning empty list - no real posts can be fetched without Pyrogram", channel=channel_username)
        return []
    
    # Save posts to database if requested
    if save_to_db and user_id is not None and posts:
        await _save_posts_to_db(posts, channel_username, user_id)
    
    return posts


async def _save_posts_to_db(posts: List[dict], channel_username: str, user_id: int) -> None:
    """Save posts to database via repository.

    Purpose:
        Helper function to save fetched posts to MongoDB.

    Args:
        posts: List of post dictionaries
        channel_username: Channel username
        user_id: User ID

    Raises:
        None: Errors are logged and handled gracefully
    """
    try:
        from src.presentation.mcp.tools.digest_tools import save_posts_to_db
        
        result = await save_posts_to_db(posts, channel_username, user_id)
        logger.debug(
            "Saved posts to database",
            channel=channel_username,
            saved=result["saved"],
            skipped=result["skipped"],
            total=result["total"]
        )
    except Exception as e:
        logger.warning(
            "Failed to save posts to database",
            channel=channel_username,
            error=str(e),
            exc_info=True
        )

