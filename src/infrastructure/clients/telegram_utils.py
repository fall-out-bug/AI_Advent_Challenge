"""Telegram client utilities for fetching channel posts.

Supports two methods:
1. Bot API (aiogram) - only works if bot is channel admin
2. MTProto client (Pyrogram) - works with user account for any public channel
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import List, Optional

from src.infrastructure.logging import get_logger

logger = get_logger("telegram_utils")

# Pyrogram will be imported lazily inside functions to avoid event loop issues
PYROGRAM_AVAILABLE = None  # Will be set on first import attempt


def _check_pyrogram_available() -> bool:
    """Check if Pyrogram is available (lazy import to avoid event loop issues).

    Note: This only checks if the package is installed, not if it can be imported.
    Actual import happens in _fetch_with_pyrogram() after event loop is created.
    """
    global PYROGRAM_AVAILABLE
    if PYROGRAM_AVAILABLE is not None:
        return PYROGRAM_AVAILABLE

    # Check if pyrogram package is installed without importing it
    # (to avoid event loop issues at module load time)
    import importlib.util

    spec = importlib.util.find_spec("pyrogram")
    if spec is None:
        PYROGRAM_AVAILABLE = False
        logger.debug("Pyrogram package not installed, will use Bot API only")
        return False

    # Package exists, mark as available
    # Actual import will happen in _fetch_with_pyrogram() when event loop exists
    PYROGRAM_AVAILABLE = True
    return True


async def _fetch_with_pyrogram(
    channel_username: str,
    since: datetime,
    api_id: Optional[str] = None,
    api_hash: Optional[str] = None,
    session_string: Optional[str] = None,
    user_id: Optional[int] = None,
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
    # Lazy import Pyrogram to avoid event loop issues
    if not _check_pyrogram_available():
        raise ImportError("Pyrogram not installed. Install with: pip install pyrogram")

    # Import Pyrogram classes only when needed (after event loop is created)
    from pyrogram import Client  # noqa: F401
    from pyrogram.errors import BadRequest, FloodWait  # noqa: F401

    api_id = api_id or os.getenv("TELEGRAM_API_ID")
    api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise ValueError(
            "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for Pyrogram"
        )

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
                logger.info(
                    f"Found existing Pyrogram session file: session_file={session_file}"
                )
                break

    if not session_string and not session_file:
        logger.warning("No Pyrogram session found. Placeholder posts will be used.")

    posts = []
    client = None

    try:
        # Format channel username
        channel_id = (
            channel_username
            if channel_username.startswith("@")
            else f"@{channel_username}"
        )

        # Create client (will use existing session if available)
        # If session_string is available, use it directly (no file needed)
        # Otherwise, copy session file to temp directory for write access
        temp_session_path = None
        original_cwd = None

        if session_string:
            # Use session string directly - no file needed
            logger.info(
                f"Using Pyrogram session string (no file needed): has_string={bool(session_string)}, channel={channel_username}"
            )
            client_session_name = (
                session_name  # Name doesn't matter when using session_string
            )
        elif session_file and os.path.exists(session_file):
            # Copy session file to current working directory so Pyrogram can write to it
            # Pyrogram SQLite needs write access for WAL files
            try:
                original_cwd = os.getcwd()
                # Use /tmp or current directory for temporary session copy
                temp_session_dir = "/tmp" if os.path.exists("/tmp") else original_cwd
                temp_session_path = os.path.join(
                    temp_session_dir, f"{session_name}.session"
                )

                # Copy session file if it doesn't exist or is older
                if not os.path.exists(temp_session_path) or os.path.getmtime(
                    session_file
                ) > os.path.getmtime(temp_session_path):
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
            logger.info(
                f"Pyrogram client started successfully: channel={channel_username}"
            )
        except Exception as start_error:
            # If session doesn't exist and no session_string provided, log error
            if (
                "phone number" in str(start_error).lower()
                or "verification code" in str(start_error).lower()
            ):
                logger.error(
                    f"Pyrogram session not initialized. Please run init_pyrogram.py script first. "
                    f"channel={channel_username}, error={str(start_error)}"
                )
                raise ValueError(
                    "Pyrogram session not initialized. "
                    "Set TELEGRAM_SESSION_STRING env var or run scripts/init_pyrogram.py"
                ) from start_error
            raise

        # Get channel entity - try multiple methods
        channel = None
        actual_username = channel_username.lstrip("@")

        # Method 1: Try direct username lookup
        try:
            channel = await client.get_chat(channel_id)
            if channel.username:
                actual_username = channel.username
            logger.info(
                f"Channel found via direct username: input={channel_username}, "
                f"actual_username={actual_username}, chat_id={channel.id}, title={channel.title}"
            )
        except BadRequest:
            # Method 2: Try to find channel by title (in case input is a title, not username)
            logger.debug(
                f"Channel not found by username '{channel_username}', "
                f"trying to find by title in dialogs..."
            )
            try:
                async for dialog in client.get_dialogs():
                    if dialog.chat and dialog.chat.title:
                        # Check if title matches (case-insensitive)
                        if dialog.chat.title.lower() == channel_username.lower():
                            channel = dialog.chat
                            if channel.username:
                                actual_username = channel.username
                            logger.info(
                                f"Channel found by title: input={channel_username}, "
                                f"actual_username={actual_username}, chat_id={channel.id}, title={channel.title}"
                            )
                            break

                if not channel:
                    logger.warning(
                        f"Channel not found by title either: input={channel_username}. "
                        f"Make sure the channel username (not title) is stored in database."
                    )
            except Exception as search_error:
                logger.debug(f"Error searching channel by title: {search_error}")

        if not channel:
            logger.warning(
                f"Channel not found via Pyrogram: input={channel_username}. "
                f"Tried username lookup and title search. "
                f"Make sure channel exists and is accessible."
            )
            return []

        # If channel was found by title and actual_username differs, update database
        # This ensures we store the correct username for future fetches
        if actual_username != channel_username.lstrip("@") and user_id:
            try:
                from src.infrastructure.database.mongo import get_db

                db = await get_db()

                # Extract title and description from channel object
                channel_title = (
                    channel.title
                    if hasattr(channel, "title") and channel.title
                    else None
                )
                channel_description = (
                    channel.description
                    if hasattr(channel, "description") and channel.description
                    else None
                )

                update_fields = {
                    "channel_username": actual_username,
                }

                # Always update title from real Telegram metadata
                if channel_title:
                    update_fields["title"] = channel_title

                # Always update description from real Telegram metadata
                if channel_description:
                    update_fields["description"] = channel_description

                update_result = await db.channels.update_one(
                    {
                        "user_id": user_id,
                        "$or": [
                            {"channel_username": channel_username},
                            {"channel_username": channel_username.lstrip("@")},
                            {"title": channel_username},
                        ],
                        "active": True,
                    },
                    {"$set": update_fields},
                )
                if update_result.modified_count > 0:
                    logger.info(
                        f"Updated channel metadata in database: "
                        f"from '{channel_username}' to '{actual_username}' for user_id={user_id}, "
                        f"title={channel_title}, has_description={bool(channel_description)}"
                    )
            except Exception as update_error:
                logger.warning(
                    f"Failed to update channel metadata in database: "
                    f"from '{channel_username}' to '{actual_username}', error={update_error}"
                )

        # Fetch messages (limit to last 10000 messages to catch more posts)
        # Telegram API allows up to 100 messages per request, but we iterate to get more
        # Increased limit to ensure we get all posts from the lookback period
        messages = []
        try:
            logger.debug(
                f"Starting to fetch messages: channel={channel_username}, since={since.isoformat()}, limit=10000"
            )
            messages_before_date = (
                0  # Count how many messages we've seen before 'since'
            )
            # Increase limit to 10000 to ensure we get posts from 7-day lookback period
            async for message in client.get_chat_history(channel.id, limit=10000):
                if message.date >= since:
                    messages.append(message)
                    messages_before_date = (
                        0  # Reset counter when we find a matching message
                    )
                else:
                    messages_before_date += 1
                    # Stop if we've seen 500 consecutive messages before 'since'
                    # This handles cases where there are gaps in message history
                    # Increased threshold to allow deeper search through history
                    if messages_before_date > 500:
                        logger.debug(
                            f"Stopping fetch: found 500 consecutive messages before 'since' date for channel {channel_username}"
                        )
                        break
            logger.debug(
                f"Finished fetching messages: channel={channel_username}, messages_fetched={len(messages)}, since={since.isoformat()}"
            )
        except FloodWait as e:
            logger.warning(
                f"FloodWait: need to wait {e.value} seconds: channel={channel_username}"
            )
            # Return what we have so far
        except Exception as fetch_error:
            error_msg = str(fetch_error)
            logger.error(
                f"Error fetching messages from channel: channel={channel_username}, "
                f"error={error_msg}, error_type={type(fetch_error).__name__}",
                exc_info=True,
            )
            # If session is invalid, log it clearly
            if (
                "EOF" in error_msg
                or "session" in error_msg.lower()
                or "auth" in error_msg.lower()
            ):
                logger.error(
                    f"Pyrogram session appears to be invalid or expired: "
                    f"channel={channel_username}, session_file={session_file}, "
                    f"has_session_string={bool(session_string)}"
                )
            # Return empty list - don't raise, let caller handle it

        # Convert messages to our format
        # Use actual_username for saving posts (important for database consistency)
        logger.debug(
            f"Converting messages to post format: input={channel_username}, "
            f"actual_username={actual_username}, message_count={len(messages)}"
        )
        for msg in messages:
            text = ""
            if msg.text:
                text = msg.text
            elif msg.caption:
                text = msg.caption
            elif msg.photo or msg.video or msg.document:
                text = f"[Media: {msg.media.__class__.__name__}]"

            if text:
                posts.append(
                    {
                        "text": text,
                        "date": msg.date.isoformat(),
                        "channel": actual_username,  # Use actual username from Telegram
                        "message_id": str(msg.id),
                        "views": getattr(msg, "views", None),
                        "metadata": {
                            "original_input": channel_username,  # Keep original for reference
                        },
                    }
                )

        logger.info(
            f"Fetched posts via Pyrogram: input={channel_username}, "
            f"actual_username={actual_username}, count={len(posts)}, since={since.isoformat()}"
        )
        if len(posts) == 0:
            logger.info(
                f"No posts found in time window: input={channel_username}, "
                f"actual_username={actual_username}, since={since.isoformat()}, "
                f"now={datetime.utcnow().isoformat()}"
            )
            logger.debug(
                f"Messages fetched but no posts converted: input={channel_username}, "
                f"actual_username={actual_username}, messages_fetched={len(messages)}"
            )
        return posts

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Error fetching posts via Pyrogram: channel={channel_username}, "
            f"error={error_msg}, error_type={type(e).__name__}",
            exc_info=True,
        )
        # If session error, log it clearly
        if (
            "phone number" in error_msg.lower()
            or "verification code" in error_msg.lower()
            or "session" in error_msg.lower()
        ):
            logger.error(
                f"Pyrogram session invalid - need to reinitialize: "
                f"channel={channel_username}, session_file={session_file}, "
                f"has_session_string={bool(session_string)}"
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


async def search_channels_by_name(query: str, limit: int = 5) -> List[dict]:
    """Search public channels by name using Pyrogram.

    Purpose:
        Search for channels in user's dialogs by matching title/username.
        Also attempts direct resolve if query might be a username.

    Args:
        query: Search query (channel name, title, or username)
        limit: Maximum number of results to return

    Returns:
        List of channel dictionaries with username, title, description, chat_id

    Example:
        >>> results = await search_channels_by_name("python")
        >>> results[0]["username"]
        'python_daily'

    Note:
        Searches in user's dialogs first. If not found and query looks like
        a username, tries direct resolve via Telegram API.
    """
    if not _check_pyrogram_available():
        logger.warning("Pyrogram not available for channel search")
        return []

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_string = os.getenv("TELEGRAM_SESSION_STRING")

    if not api_id or not api_hash:
        logger.warning(
            "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set for channel search"
        )
        return []

    if not session_string:
        logger.warning("TELEGRAM_SESSION_STRING must be set for channel search")
        return []

    # Lazy import Pyrogram
    from pyrogram import Client
    from pyrogram.errors import FloodWait

    # Normalize query: replace underscores with spaces, strip
    # This helps with queries like "крупнокалиберный_переполох" -> "крупнокалиберный переполох"
    query_normalized = query.replace("_", " ").replace("-", " ").strip()
    query_lower = query_normalized.lower()
    results = []
    dialog_count = 0  # Initialize counter for logging
    channels_processed = 0  # Initialize counter for channels processed
    matching_attempts = 0  # Initialize counter for matching attempts

    # Try MongoDB cache first (fast path)
    try:
        from src.infrastructure.cache.dialogs_cache import PublicChannelsCache

        cache = PublicChannelsCache()
        cached_channels = await cache.get_cached()

        if cached_channels:
            logger.debug(
                f"Searching in cache: {len(cached_channels)} channels available"
            )
            cache_results = []

            for channel in cached_channels:
                title = channel.get("title", "") or ""
                username = channel.get("username", "") or ""

                if not title or not username:
                    continue

                title_lower = title.lower()
                username_lower = username.lower()
                title_normalized = title_lower.replace("_", " ").replace("-", " ")
                username_normalized = username_lower.replace("_", " ").replace("-", " ")

                # Calculate score using same logic as dialogs search
                score = 0

                if query_lower == title_lower:
                    score = 100
                elif query_lower == username_lower:
                    score = 90
                elif query_lower:
                    query_tokens = set(query_lower.split())
                    title_tokens = (
                        set(title_normalized.split()) if title_normalized else set()
                    )
                    username_tokens = (
                        set(username_normalized.split())
                        if username_normalized
                        else set()
                    )

                    if query_tokens:
                        title_match = (
                            query_tokens.issubset(title_tokens)
                            if title_tokens
                            else False
                        )
                        username_match = (
                            query_tokens.issubset(username_tokens)
                            if username_tokens
                            else False
                        )

                        if title_match:
                            score = 80
                        elif username_match:
                            score = 70
                        else:
                            title_ratio = (
                                len(query_tokens & title_tokens) / len(query_tokens)
                                if query_tokens
                                else 0
                            )
                            username_ratio = (
                                len(query_tokens & username_tokens) / len(query_tokens)
                                if query_tokens
                                else 0
                            )

                            if title_ratio >= 0.5:
                                score = 60
                            elif username_ratio >= 0.5:
                                score = 50
                            else:
                                if (
                                    query_lower in title_lower
                                    or query_lower in username_lower
                                    or query_lower in title_normalized
                                    or query_lower in username_normalized
                                ):
                                    score = 40

                if score > 0:
                    cache_results.append(
                        {
                            "username": username,
                            "title": title,
                            "description": channel.get("description", "") or "",
                            "chat_id": channel.get("chat_id"),
                            "score": score,
                        }
                    )

            if cache_results:
                # Sort by score and take top-N
                cache_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                cache_results = cache_results[:limit]

                logger.info(
                    f"Found {len(cache_results)} results from cache for query='{query}'"
                )
                return cache_results
            else:
                logger.debug(
                    f"No matches found in cache for query='{query}', falling back to dialogs search"
                )
        else:
            logger.debug("Cache is empty, falling back to dialogs search")
    except Exception as cache_error:
        logger.warning(
            f"Error accessing cache, falling back to dialogs search: {cache_error}"
        )

    # Fallback to direct dialogs search if cache is empty or failed

    # Use unique client name to avoid conflicts with concurrent requests
    import uuid

    client_name = f"butler_search_{uuid.uuid4().hex[:8]}"

    client = Client(
        client_name,
        api_id=int(api_id),
        api_hash=api_hash,
        session_string=session_string,
        no_updates=True,
    )

    try:
        await client.start()

        # Search through user's dialogs
        logger.debug(
            f"Starting dialog search: query='{query}', normalized='{query_normalized}', query_lower='{query_lower}'"
        )
        from pyrogram.enums import ChatType

        dialog_count = 0
        channels_processed = 0
        matching_attempts = 0
        async for dialog in client.get_dialogs(limit=1000):
            dialog_count += 1
            if not dialog.chat:
                continue

            # Skip private chats
            # Note: dialog.chat.type is ChatType enum
            chat_type = dialog.chat.type
            # Check if it's a channel or supergroup (use enum comparison for reliability)
            if chat_type not in (ChatType.CHANNEL, ChatType.SUPERGROUP):
                continue

            channels_processed += 1

            # Check if title or username matches query
            title = getattr(dialog.chat, "title", "") or ""
            username = getattr(dialog.chat, "username", "") or ""

            # Debug logging for specific channels - use INFO level so it shows
            if any(
                term in (title.lower() + " " + username.lower())
                for term in [
                    "крупнокалиберный",
                    "переполох",
                    "деградат",
                    "нация",
                    "лвд",
                    "bolshiepushki",
                    "degradat1",
                    "thinkaboutism",
                ]
            ):
                logger.info(
                    f"Processing potential match: type={chat_type.name}, title='{title}', username='{username}', "
                    f"query='{query}'"
                )

            # Skip if both title and username are empty
            if not title and not username:
                continue

            # Match by title or username using token-based matching
            # This handles cases like "крупнокалиберный_переполох" matching "Крупнокалиберный Переполох"
            title_lower = title.lower() if title else ""
            username_lower = username.lower() if username else ""

            # Normalize title and username for matching (replace underscores, hyphens with spaces)
            title_normalized = title_lower.replace("_", " ").replace("-", " ")
            username_normalized = username_lower.replace("_", " ").replace("-", " ")

            # Track matching attempts for specific channels
            is_target_channel = any(
                term in (title_lower + " " + username_lower)
                for term in [
                    "крупнокалиберный",
                    "переполох",
                    "деградат",
                    "нация",
                    "лвд",
                    "bolshiepushki",
                    "degradat1",
                    "thinkaboutism",
                ]
            )
            if is_target_channel:
                matching_attempts += 1
                logger.info(
                    f"Processing target channel: title='{title}', username='{username}', "
                    f"title_normalized='{title_normalized}', query_lower='{query_lower}'"
                )

            # Calculate weighted score for this channel
            score = 0

            # Exact title match: 100
            if query_lower == title_lower:
                score = 100
            # Exact username match: 90
            elif query_lower == username_lower:
                score = 90
            # All tokens in title: 80
            elif query_lower:
                query_tokens = set(query_lower.split())
                title_tokens = (
                    set(title_normalized.split()) if title_normalized else set()
                )
                username_tokens = (
                    set(username_normalized.split()) if username_normalized else set()
                )

                if query_tokens:
                    title_match = (
                        query_tokens.issubset(title_tokens) if title_tokens else False
                    )
                    username_match = (
                        query_tokens.issubset(username_tokens)
                        if username_tokens
                        else False
                    )

                    if title_match:
                        score = 80
                    elif username_match:
                        score = 70
                    else:
                        # 50%+ tokens in title: 60
                        title_ratio = (
                            len(query_tokens & title_tokens) / len(query_tokens)
                            if query_tokens
                            else 0
                        )
                        username_ratio = (
                            len(query_tokens & username_tokens) / len(query_tokens)
                            if query_tokens
                            else 0
                        )

                        if title_ratio >= 0.5:
                            score = 60
                        elif username_ratio >= 0.5:
                            score = 50
                        else:
                            # Substring match: 40
                            if (
                                query_lower in title_lower
                                or query_lower in username_lower
                                or query_lower in title_normalized
                                or query_lower in username_normalized
                                or title_normalized in query_lower
                                or username_normalized in query_lower
                            ):
                                score = 40
                            else:
                                # Check significant tokens (length >= 4)
                                significant_query_tokens = {
                                    t for t in query_tokens if len(t) >= 4
                                }
                                if significant_query_tokens:
                                    title_sig_match = any(
                                        any(st in tt for tt in title_tokens)
                                        or st in title_normalized
                                        for st in significant_query_tokens
                                    )
                                    username_sig_match = any(
                                        any(st in ut for ut in username_tokens)
                                        or st in username_normalized
                                        for st in significant_query_tokens
                                    )
                                    if title_sig_match or username_sig_match:
                                        score = 30

            # Simple match flag for backward compatibility
            simple_match = score >= 40
            token_match = score >= 30

            if score > 0:
                # Log match found for debugging
                if any(
                    term in (title.lower() + " " + username.lower())
                    for term in [
                        "крупнокалиберный",
                        "переполох",
                        "деградат",
                        "нация",
                        "лвд",
                        "bolshiepushki",
                        "degradat1",
                        "thinkaboutism",
                    ]
                ):
                    logger.info(
                        f"Match found: simple_match={simple_match}, token_match={token_match}, "
                        f"title='{title}', username='{username}', query='{query}'"
                    )

                # For subscription search, we need both username and title
                # Skip channels without title
                if not title or not title.strip():
                    if any(
                        term in username.lower()
                        for term in ["bolshiepushki", "degradat1", "thinkaboutism"]
                    ):
                        logger.warning(
                            f"Skipping channel without title: username='{username}', "
                            f"query='{query}'"
                        )
                    continue

                # Skip channels without username (can't subscribe to private groups)
                if not username or not username.strip():
                    if (
                        "крупнокалиберный" in title.lower()
                        or "переполох" in title.lower()
                        or "деградат" in title.lower()
                        or "лвд" in title.lower()
                    ):
                        logger.warning(
                            f"Skipping channel without username: title='{title}', "
                            f"query='{query}'"
                        )
                    continue

                description = getattr(dialog.chat, "description", "") or ""

                # Ensure username and title are not None and are stripped
                username = username.strip() if username else ""
                title = title.strip() if title else ""

                # Double-check after strip
                if not username or not title:
                    logger.debug(
                        f"Skipping channel after strip: username='{username}', "
                        f"title='{title}', query='{query}'"
                    )
                    continue

                # Check if we already have this channel (deduplication by username)
                # If exists, keep the one with higher score
                existing_index = None
                for i, r in enumerate(results):
                    if r.get("username") == username:
                        existing_index = i
                        break

                if existing_index is not None:
                    existing_score = results[existing_index].get("score", 0)
                    if score > existing_score:
                        # Replace with higher score
                        results[existing_index] = {
                            "username": username,
                            "title": title,
                            "description": description if description else "",
                            "chat_id": dialog.chat.id,
                            "score": score,
                        }
                        logger.debug(
                            f"Updated channel with higher score: username='{username}', "
                            f"old_score={existing_score}, new_score={score}"
                        )
                    else:
                        logger.debug(
                            f"Skipping duplicate channel with lower score: username='{username}', "
                            f"existing_score={existing_score}, new_score={score}"
                        )
                    continue

                results.append(
                    {
                        "username": username,
                        "title": title,
                        "description": description if description else "",
                        "chat_id": dialog.chat.id,
                        "score": score,
                    }
                )

                logger.debug(
                    f"Found channel match: username='{username}', title='{title}', "
                    f"score={score}, query='{query}'"
                )

                if len(results) >= limit * 2:  # Collect more for sorting, then trim
                    break

        # Sort results by score (descending) and return top-N
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:limit]

        logger.debug(
            f"After sorting: top {len(results)} results with scores: "
            f"{[(r.get('username'), r.get('score')) for r in results[:5]]}"
        )

        # If no results found in dialogs, try multiple fallback strategies
        if not results:
            logger.debug(
                f"No channels found in dialogs, trying fallback strategies: query='{query}', normalized='{query_normalized}'"
            )

            # Strategy 1: Try direct resolve with normalized query (in case it's a username variant)
            try:
                username_to_try = query_normalized.lstrip("@").strip()

                # Try direct get_chat (works for public channels by username)
                try:
                    chat = await client.get_chat(username_to_try)
                    if chat and hasattr(chat, "title"):
                        chat_username = getattr(chat, "username", "") or ""
                        chat_title = getattr(chat, "title", "") or ""

                        # Only add if we have both username and title
                        if chat_username and chat_title:
                            results.append(
                                {
                                    "username": chat_username,
                                    "title": chat_title,
                                    "description": getattr(chat, "description", "")
                                    or "",
                                    "chat_id": chat.id,
                                    "score": 85,  # Direct resolve gets high score
                                }
                            )
                            logger.info(
                                f"Found channel via direct resolve: "
                                f"query='{query}', username='{chat_username}', "
                                f"title='{chat_title}'"
                            )
                except Exception as resolve_error:
                    logger.debug(
                        f"Direct resolve failed for '{username_to_try}': {resolve_error}"
                    )
            except Exception as e:
                logger.debug(f"Error during direct resolve: {e}")

            # Strategy 2: Try searching in all known dialogs more thoroughly
            # Sometimes channels are in dialogs but matching failed due to normalization
            if not results:
                logger.debug(
                    f"Re-scanning dialogs with improved matching: query='{query_normalized}'"
                )
                # Re-scan with more relaxed matching - check each word individually
                query_words = [
                    w for w in query_normalized.lower().split() if len(w) >= 3
                ]

                async for dialog in client.get_dialogs(limit=1000):
                    if not dialog.chat:
                        continue
                    from pyrogram.enums import ChatType

                    chat_type = dialog.chat.type
                    if chat_type not in (ChatType.CHANNEL, ChatType.SUPERGROUP):
                        continue

                    title = getattr(dialog.chat, "title", "") or ""
                    username = getattr(dialog.chat, "username", "") or ""

                    if not title or not username:
                        continue

                    # Normalize title for matching
                    title_normalized = title.lower().replace("_", " ").replace("-", " ")

                    # More relaxed matching: check if any significant word matches
                    # For "крупнокалиберный_переполох" -> ["крупнокалиберный", "переполох"]
                    # Should match "Крупнокалиберный Переполох"
                    significant_match = False

                    if query_words:
                        # Check if any query word appears in title (even partial)
                        for query_word in query_words:
                            if query_word in title_normalized:
                                significant_match = True
                                break

                        # Also check if at least 50% of words match
                        if not significant_match and len(query_words) > 1:
                            matching_words = sum(
                                1 for word in query_words if word in title_normalized
                            )
                            significant_match = matching_words >= max(
                                1, len(query_words) // 2
                            )

                    if significant_match:
                        # Check if we already have this channel
                        if not any(r.get("username") == username for r in results):
                            results.append(
                                {
                                    "username": username,
                                    "title": title,
                                    "description": getattr(
                                        dialog.chat, "description", ""
                                    )
                                    or "",
                                    "chat_id": dialog.chat.id,
                                    "score": 35,  # Relaxed matching gets lower score
                                }
                            )
                            logger.info(
                                f"Found channel via relaxed matching: "
                                f"query='{query}', username='{username}', "
                                f"title='{title}'"
                            )
                            if len(results) >= limit:
                                break

            # Strategy 3: Try known username patterns (for common channels)
            # This is a last resort - try transliterated variants
            if not results and any("\u0400" <= c <= "\u04ff" for c in query_normalized):
                logger.debug(
                    f"Query contains Cyrillic, trying transliteration variants"
                )
                # Could try transliteration here, but might be too complex
                # For now, just log that we tried

            # Sort fallback results by score
            if results:
                results.sort(key=lambda x: x.get("score", 0), reverse=True)
                results = results[:limit]

        # Strategy 4: Bot API fallback (if enabled and no results)
        if not results:
            try:
                from src.infrastructure.config.settings import get_settings

                settings = get_settings()

                if settings.bot_api_fallback_enabled:
                    # Check if query looks like a username (latin, digits, underscore)
                    username_pattern = query_normalized.lstrip("@").strip()
                    if username_pattern and all(
                        c.isalnum() or c == "_" for c in username_pattern
                    ):
                        from src.infrastructure.clients.bot_api_resolver import (
                            BotApiChannelResolver,
                        )

                        resolver = BotApiChannelResolver()
                        try:
                            bot_result = await resolver.resolve_username(
                                username_pattern
                            )
                            if bot_result:
                                results.append(bot_result)
                                logger.info(
                                    f"Found channel via Bot API fallback: username='{bot_result['username']}', "
                                    f"query='{query}'"
                                )
                        finally:
                            await resolver.close()
            except Exception as bot_api_error:
                logger.debug(f"Bot API fallback error: {bot_api_error}")

        # Strategy 5: LLM fallback (if enabled and no results or ambiguous)
        if len(results) == 0 or (
            len(results) > 0 and all(r.get("score", 0) < 50 for r in results)
        ):
            try:
                from src.infrastructure.config.settings import get_settings

                settings = get_settings()

                if settings.llm_fallback_enabled:
                    # Get cached channels for LLM processing
                    try:
                        from src.infrastructure.cache.dialogs_cache import (
                            PublicChannelsCache,
                        )

                        cache = PublicChannelsCache()
                        cached_channels = await cache.get_cached()

                        if cached_channels:
                            from src.infrastructure.llm.channel_matcher import (
                                LlmChannelMatcher,
                            )

                            matcher = LlmChannelMatcher()
                            llm_results = await matcher.match_channels(
                                query, cached_channels, limit=limit
                            )

                            if llm_results:
                                # Merge LLM results with existing results (deduplicate by username)
                                existing_usernames = {
                                    r.get("username") for r in results
                                }

                                for llm_result in llm_results:
                                    if (
                                        llm_result.get("username")
                                        not in existing_usernames
                                    ):
                                        results.append(llm_result)
                                        logger.info(
                                            f"Found channel via LLM fallback: "
                                            f"username='{llm_result.get('username')}', "
                                            f"confidence={llm_result.get('llm_confidence', 0):.2f}, "
                                            f"query='{query}'"
                                        )

                                # Re-sort by score
                                if results:
                                    results.sort(
                                        key=lambda x: x.get("score", 0), reverse=True
                                    )
                                    results = results[:limit]
                    except Exception as llm_error:
                        logger.debug(f"LLM fallback error: {llm_error}")
            except Exception as llm_config_error:
                logger.debug(f"LLM fallback config error: {llm_config_error}")

    except FloodWait as e:
        logger.warning(f"FloodWait during channel search: {e.value} seconds")
    except Exception as e:
        logger.error(f"Error searching channels: {e}", exc_info=True)
    finally:
        if client.is_connected:
            await client.stop()

            logger.info(
                f"Channel search completed: query={query}, normalized={query_normalized}, "
                f"dialogs_scanned={dialog_count}, channels_processed={channels_processed}, "
                f"matching_attempts={matching_attempts}, results_count={len(results)}"
            )

    logger.info(
        f"Channel search completed: query={query}, normalized={query_normalized}, results_count={len(results)}"
    )
    return results


async def fetch_channel_posts(
    channel_username: str,
    since: datetime,
    user_id: int | None = None,
    save_to_db: bool = True,
) -> List[dict]:
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
    if (
        _check_pyrogram_available()
        and os.getenv("TELEGRAM_API_ID")
        and os.getenv("TELEGRAM_API_HASH")
    ):
        try:
            posts = await _fetch_with_pyrogram(
                channel_username=channel_username,
                since=since,
                user_id=user_id,
            )
            # Return posts even if empty - Pyrogram worked, just no posts found
            logger.info(
                f"Pyrogram fetch completed: channel={channel_username}, count={len(posts)}, since={since.isoformat()}"
            )
        except Exception as e:
            logger.warning(
                f"Pyrogram fetch failed: {e}, trying Bot API: channel={channel_username}",
                exc_info=True,
            )

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
        logger.info(
            f"Pyrogram not available or failed, Bot API cannot fetch posts: channel={channel_username}"
        )
        logger.info(
            f"Returning empty list - no real posts can be fetched without Pyrogram: channel={channel_username}"
        )
        return []

    # Save posts to database if requested
    if save_to_db and user_id is not None and posts:
        await _save_posts_to_db(posts, channel_username, user_id)

    return posts


async def _update_channel_username_in_db(
    user_id: int, old_username: str, new_username: str
) -> None:
    """Update channel username in database without touching title.

    Purpose:
        Helper function to update channel_username when actual username
        differs from stored value. Does NOT update title to preserve
        existing metadata.

    Args:
        user_id: Telegram user ID
        old_username: Current username in database (may be incorrect)
        new_username: Correct username from Telegram

    Raises:
        None: Errors are logged and handled gracefully
    """
    try:
        from src.infrastructure.database.mongo import get_db

        db = await get_db()
        await db.channels.update_one(
            {
                "user_id": user_id,
                "channel_username": old_username,
                "active": True,
            },
            {
                "$set": {
                    "channel_username": new_username,
                    # NOTE: Do NOT set title here - preserve existing title
                    # Title should only be updated from real Telegram metadata
                }
            },
        )
        logger.info(
            f"Updated channel username in database: "
            f"from '{old_username}' to '{new_username}' for user_id={user_id}"
        )
    except Exception as update_error:
        logger.warning(
            f"Failed to update channel username in database: "
            f"from '{old_username}' to '{new_username}', error={update_error}"
        )


async def _save_posts_to_db(
    posts: List[dict], channel_username: str, user_id: int
) -> None:
    """Save posts to database via repository.

    Purpose:
        Helper function to save fetched posts to MongoDB.
        Also updates channel username in database if it was resolved from title.

    Args:
        posts: List of post dictionaries (should contain actual_username in metadata if different)
        channel_username: Channel username (may be original input)
        user_id: User ID

    Raises:
        None: Errors are logged and handled gracefully
    """
    try:
        # Check if posts have actual_username different from input
        # Posts from Pyrogram have "channel" field with actual username
        actual_username = channel_username
        if posts:
            first_post = posts[0]
            # Posts from Pyrogram have "channel" field with actual username
            # Use it if available, otherwise fall back to channel_username parameter
            post_channel = first_post.get("channel") or first_post.get(
                "channel_username"
            )
            if post_channel:
                actual_username = post_channel

                # Update channel username in database if it was different
                # NOTE: Do NOT update title here - it should only be updated from
                # real Telegram metadata (from channel object in Pyrogram fetch)
                if actual_username != channel_username:
                    await _update_channel_username_in_db(
                        user_id, channel_username, actual_username
                    )

        # Import here to avoid circular dependencies
        from src.presentation.mcp.tools.digest_tools import (
            save_posts_to_db as mcp_save_posts,
        )

        result = await mcp_save_posts(posts, actual_username, user_id)
        logger.debug(
            f"Saved posts to database: original_input={channel_username}, "
            f"actual_username={actual_username}, "
            f"saved={result['saved']}, skipped={result['skipped']}, total={result['total']}"
        )
    except Exception as e:
        logger.warning(
            f"Failed to save posts to database: channel={channel_username}, error={str(e)}",
            exc_info=True,
        )
