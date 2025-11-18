"""Channel digest generation tools.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from src.infrastructure.config.settings import get_settings
from src.infrastructure.di.factories import (
    create_channel_digest_by_name_use_case,
    create_channel_digest_use_case,
)
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.post_repository import PostRepository
from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database

logger = get_logger("channel_digest")
_settings = get_settings()


async def _normalize_post_dates(posts: List[dict]) -> List[dict]:
    """Normalize post date strings to datetime objects.

    Args:
        posts: List of post dictionaries

    Returns:
        List of posts with normalized dates
    """
    normalized = []
    for post in posts:
        normalized_post = dict(post)
        if isinstance(normalized_post.get("date"), str):
            try:
                normalized_post["date"] = datetime.fromisoformat(
                    normalized_post["date"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass
        normalized.append(normalized_post)
    return normalized


async def _generate_summary(
<<<<<<< HEAD
    posts: List[dict],
    max_sentences: int,
    hours: int = None,
    channel_username: str = None,
    channel_title: str = None,
=======
    posts: List[dict], max_sentences: int, hours: int = None
>>>>>>> origin/master
) -> str:
    """Generate summary from posts with fallback.

    Args:
        posts: List of normalized post dictionaries
        max_sentences: Maximum sentences in summary
        hours: Time period in hours (for prompt context)
<<<<<<< HEAD
        channel_username: Channel username for context
        channel_title: Channel title for better context
=======
>>>>>>> origin/master

    Returns:
        Summary text
    """
    if not posts:
        logger.warning("_generate_summary called with empty posts list")
        return "Нет постов для суммаризации."

    try:
        from src.infrastructure.llm.summarizer import summarize_posts

        # Pass hours as metadata to ensure different prompts for different periods
        logger.info(
            f"Calling LLM summarizer: posts_count={len(posts)}, "
            f"max_sentences={max_sentences}, hours={hours}, "
<<<<<<< HEAD
            f"channel_username={channel_username}, channel_title={channel_title}, "
=======
>>>>>>> origin/master
            f"total_text_length={sum(len(p.get('text', '')) for p in posts)}"
        )

        # Log sample posts for debugging
        if posts:
            sample_posts = posts[:3]
            logger.debug(
                f"Sample posts for summarization: "
                f"first_post_length={len(sample_posts[0].get('text', '')) if sample_posts else 0}, "
                f"first_post_preview={sample_posts[0].get('text', '')[:200] if sample_posts else 'N/A'}"
            )

<<<<<<< HEAD
        # Extract channel info from first post for context isolation (fallback)
=======
        # Extract channel info from first post for context isolation
>>>>>>> origin/master
        channel_username_from_posts = None
        if posts and posts[0].get("channel_username"):
            channel_username_from_posts = posts[0].get("channel_username")

<<<<<<< HEAD
        # Use provided channel_username or extract from posts
        final_channel_username = channel_username or channel_username_from_posts

=======
>>>>>>> origin/master
        summary = await summarize_posts(
            posts,
            max_sentences=max_sentences,
            time_period_hours=hours,
<<<<<<< HEAD
            channel_username=final_channel_username,
            channel_title=channel_title,
=======
            channel_username=channel_username_from_posts,
>>>>>>> origin/master
        )
        logger.info(
            f"LLM summarizer returned summary: length={len(summary)} characters, "
            f"first_200_chars={summary[:200]}"
        )
        return summary
    except Exception as e:
        logger.error(
            f"Error in summarizer: type={type(e).__name__}, error={str(e)}, "
            f"posts_count={len(posts)}, max_sentences={max_sentences}, hours={hours}",
            exc_info=True,
        )
        # Fallback: simple heuristic summary
        texts: List[str] = []
        for p in posts[: min(20, len(posts))]:
            t = str(p.get("text", "")).strip()
            if not t:
                continue
            texts.append(t)
        joined = "\n\n".join(texts)
        parts = [
            s.strip()
            for s in joined.replace("?", ".").replace("!", ".").split(".")
            if s.strip()
        ]
        # Don't truncate here - let data_handler format properly for Telegram
        # Return full summary text
        summary_text = ". ".join(parts[:max_sentences])
        logger.warning(
            f"Using fallback summary of {len(summary_text)} characters (first 200: {summary_text[:200]})"
        )
        return summary_text


@mcp.tool()
async def get_channel_digest_by_name(
    user_id: int, channel_username: str, hours: int = 72
) -> Dict[str, Any]:
    """Get digest for a specific channel by username.

    Automatically subscribes to channel if not subscribed, then generates digest.

    Args:
        user_id: Telegram user ID
        channel_username: Channel username without @
        hours: Hours to look back (default 72 = 3 days)

    Returns:
        Dict with digests list
    """
    db = await get_database()
    channel_username = channel_username.lstrip("@")

    logger.info(
        f"get_channel_digest_by_name called: user_id={user_id}, channel={channel_username}, hours={hours}"
    )

    # Try to find exact match first
    existing = await db.channels.find_one(
        {"user_id": user_id, "channel_username": channel_username, "active": True}
    )

    logger.info(
        f"Exact match search result: found={existing is not None}, searching for='{channel_username}'"
    )

<<<<<<< HEAD
    # If not found, try case-insensitive match immediately (before other searches)
    # This handles cases where username might have different case
    if not existing:
        existing = await db.channels.find_one(
            {
                "user_id": user_id,
                "channel_username": {"$regex": f"^{re.escape(channel_username)}$", "$options": "i"},
                "active": True,
            }
        )
        if existing:
            logger.info(
                f"Found case-insensitive match: {existing.get('channel_username')} for {channel_username}"
            )
            channel_username = existing.get("channel_username")  # Use exact name from DB

=======
>>>>>>> origin/master
    # If exact match not found, try case-insensitive, partial, and title-based search
    if not existing:
        all_channels = await db.channels.find(
            {"user_id": user_id, "active": True}
        ).to_list(length=100)

        logger.info(f"Found {len(all_channels)} active channels for user {user_id}")

        # Try case-insensitive match first
        for channel in all_channels:
            if channel.get("channel_username", "").lower() == channel_username.lower():
                logger.info(
                    f"Found case-insensitive match: {channel.get('channel_username')} for {channel_username}"
                )
                channel_username = channel.get(
                    "channel_username"
                )  # Use exact name from DB
                existing = channel
                break

        # If still not found, try partial match (for Russian declension) - but only if both are similar
        # This helps match "Набока" (Russian name) with "onaboka" (username)
        if not existing and len(channel_username) > 3:
            channel_lower = channel_username.lower()
            logger.info(
                f"Trying partial match for '{channel_username}' (lower: '{channel_lower}')"
            )
            # First try exact prefix match
            for channel in all_channels:
                db_name = channel.get("channel_username", "").lower()
                # Normalize Russian declension for comparison
                normalized_search = channel_lower.rstrip("еи")
                normalized_db = db_name.rstrip("еи")

                # Check if one is prefix of another (handles "набока" vs "набоке")
                if (
                    db_name.startswith(channel_lower[:4])
                    or channel_lower.startswith(db_name[:4])
                    or normalized_search.startswith(normalized_db[:4])
                    or normalized_db.startswith(normalized_search[:4])
                ):
                    logger.info(
                        f"Found partial match: {channel.get('channel_username')} for {channel_username}"
                    )
                    channel_username = channel.get("channel_username")
                    existing = channel
                    break

            # If still not found, try transliteration-based match (Russian name -> username)
            # Example: "Набока" should match "onaboka" (both normalized to similar pattern)
            if not existing:
                # Simple transliteration check: if search is Russian-only and DB has Latin
                # or vice versa, check if they could be the same
                bool(re.search(r"[а-яА-Я]", channel_username))
                for channel in all_channels:
                    db_name = channel.get("channel_username", "")
                    not bool(re.search(r"[а-яА-Я]", db_name)) if db_name else False

                    # If search is Russian and DB is Latin (or vice versa), skip transliteration matching
                    # For now, focus on exact/partial matches and metadata resolution

        # If still not found, try matching by channel title using metadata
        if not existing:
            logger.info(f"Trying to resolve '{channel_username}' by title/metadata...")
            logger.info(f"Checking {len(all_channels)} channels for title match")
            try:
                # Import here to avoid circular dependency
                from src.presentation.mcp.tools.channels.channel_metadata import (
                    get_channel_metadata,
                )

                search_lower = channel_username.lower()
                normalized_search = search_lower.rstrip("еи")

                # Score all matches and pick the best one (not just first)
                best_match = None
                best_score = 0

                # First, try to fetch metadata for channels missing it and refresh the list
                for channel in all_channels:
                    db_username = channel.get("channel_username")
                    if not db_username:
                        continue

                    # If channel has no title, try to fetch metadata
                    if not channel.get("title") or channel.get("title") == "N/A":
                        try:
                            logger.info(
                                f"Channel {db_username} missing title, fetching metadata..."
                            )
                            metadata = await get_channel_metadata(
                                db_username, user_id=user_id
                            )
                            if metadata.get("success") and metadata.get("title"):
                                channel["title"] = metadata.get("title")
                                channel["description"] = metadata.get("description", "")
                                # Update in DB
                                await db.channels.update_one(
                                    {"_id": channel.get("_id")},
                                    {
                                        "$set": {
                                            "title": metadata.get("title"),
                                            "description": metadata.get(
                                                "description", ""
                                            ),
                                        }
                                    },
                                )
                                logger.info(
                                    f"Updated channel {db_username} with metadata: title={metadata.get('title')}"
                                )
                        except Exception as e:
                            logger.debug(
                                f"Failed to fetch metadata for {db_username}: {e}"
                            )

                # Refresh channels list from DB after metadata updates
                all_channels = await db.channels.find(
                    {"user_id": user_id, "active": True}
                ).to_list(length=100)
                logger.info(
                    f"Refreshed channel list after metadata fetch: {len(all_channels)} channels"
                )

                # Now score all channels by match quality
                for channel in all_channels:
                    db_username = channel.get("channel_username")
                    if not db_username:
                        continue

                    channel_title = channel.get("title", "").lower()
                    channel_desc = channel.get("description", "").lower()
                    score = 0

                    # Try to get fresh metadata if title still missing
                    if not channel_title or channel_title == "n/a":
                        try:
                            metadata = await get_channel_metadata(
                                db_username, user_id=user_id
                            )
                            if metadata.get("success"):
                                channel_title = metadata.get("title", "").lower()
                                channel_desc = metadata.get("description", "").lower()
                        except Exception as e:
                            logger.debug(
                                f"Failed to get metadata for {db_username}: {e}"
                            )
                            continue

                    if not channel_title:
                        continue

                    normalized_title = (
                        channel_title.rstrip("еи") if channel_title else ""
                    )
                    normalized_desc = channel_desc.rstrip("еи") if channel_desc else ""
                    title_words = set(channel_title.split()) if channel_title else set()

                    # Scoring system: higher score = better match
                    # Exact match gets highest score
                    if search_lower == channel_title:
                        score = 100
                    elif search_lower in channel_title or channel_title.startswith(
                        search_lower
                    ):
                        score = 80
                    elif normalized_search == normalized_title:
                        score = 75
                    elif (
                        normalized_search in normalized_title
                        or normalized_title.startswith(normalized_search)
                    ):
                        score = 70
                    # Check if search is in any title word (word contains search term)
                    elif any(
                        search_lower == w or w.startswith(search_lower)
                        for w in title_words
                    ):
                        score = 60
                    elif any(
                        normalized_search == w.rstrip("еи")
                        or w.rstrip("еи").startswith(normalized_search)
                        for w in title_words
                    ):
                        score = 55
                    # Check if normalized search matches any normalized title word (for cases like "Гладкова" -> "гладков" matches "Гладков" in "Алексей Гладков")
                    elif any(
                        normalized_search == w.rstrip("еи")
                        or w.rstrip("еи") == normalized_search
                        for w in title_words
                    ):
                        score = 50
                    # Check if any normalized title word is prefix/suffix of normalized search
                    elif any(
                        w.rstrip("еи") in normalized_search
                        or normalized_search.startswith(w.rstrip("еи"))
                        for w in title_words
                        if len(w.rstrip("еи")) >= 3
                    ):
                        score = 48
                    # Check if search contains any title word (reverse check - less reliable)
                    elif any(len(w) >= 4 and w in search_lower for w in title_words):
                        score = 45
                    # Check description as fallback
                    elif (
                        search_lower in channel_desc
                        or normalized_search in normalized_desc
                    ):
                        score = 40
                    else:
                        # No match
                        continue

                    logger.info(
                        f"Channel '{db_username}' scored {score} for search '{channel_username}' "
                        f"(title: {channel.get('title', 'N/A')})"
                    )

                    if score > best_score:
                        best_score = score
                        best_match = (channel, db_username)

                if best_match and best_score >= 40:  # Minimum threshold for matching
                    existing = best_match[0]
                    channel_username = best_match[1]
                    logger.info(
                        f"Selected best match: '{channel_username}' (score: {best_score}) "
                        f"for search '{channel_username}'"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to resolve channel by metadata: {e}", exc_info=True
                )
                # Continue with original channel_username even if resolution fails

    # If channel not found in subscriptions, try to find it via Telegram search
    # and offer subscription (as per cases.md: "Предлагать подписаться и только после согласия делать дайджест")
    if not existing:
        logger.info(
            f"Channel not subscribed: user_id={user_id}, channel={channel_username}. "
            f"Attempting to find via Telegram search..."
        )

        # Try to search for channel via Telegram API
        # This handles cases like "крупнокалиберный_переполох" -> "bolshiepushki"
        try:
            from src.application.use_cases.search_channel_for_subscription import (
                SearchChannelForSubscriptionUseCase,
            )

            # SearchChannelForSubscriptionUseCase doesn't need MCP client - it uses Telegram API directly
            search_use_case = SearchChannelForSubscriptionUseCase()

            logger.info(
                f"Searching Telegram for channel matching '{channel_username}'..."
            )
            search_results = await search_use_case.execute(user_id, channel_username)

            if search_results and len(search_results) > 0:
                # Found potential channel - offer to subscribe
                top_match = search_results[0]
                found_username = top_match.username
                found_title = top_match.title

                logger.info(
                    f"Found channel via Telegram search: username={found_username}, "
                    f"title={found_title} for query '{channel_username}'"
                )

                return {
                    "digests": [],
                    "channel": channel_username,
                    "status": "not_subscribed",
                    "found_channel": {
                        "username": found_username,
                        "title": found_title,
                        "description": top_match.description,
                    },
                    "message": (
                        f"Подписка не найдена для канала '{channel_username}'. "
                        f"Найден канал: {found_title} (@{found_username}). "
                        f"Подпишитесь на канал, чтобы получать дайджесты."
                    ),
                    "generated_at": datetime.utcnow().isoformat(),
                }
            else:
                logger.info(
                    f"No channels found in Telegram for query '{channel_username}'"
                )
        except Exception as e:
            logger.warning(
                f"Failed to search Telegram for channel '{channel_username}': {e}",
                exc_info=True,
            )

        # If search failed or no results, return simple not_subscribed
        return {
            "digests": [],
            "channel": channel_username,
            "status": "not_subscribed",
            "message": f"Подписка не найдена для канала '{channel_username}'. Попробуйте подписаться на канал через команду подписки.",
            "generated_at": datetime.utcnow().isoformat(),
        }

    # Check feature flag for new summarization (after channel resolution)
    if _settings.use_new_summarization:
        try:
            logger.info(
                f"Using new summarization system for channel digest by name: user_id={user_id}, channel={channel_username}, hours={hours}"
            )
            # Create use case instance
            use_case = create_channel_digest_by_name_use_case()
            # Verify it's the correct type before calling execute
            from src.application.use_cases.generate_channel_digest_by_name import (
                GenerateChannelDigestByNameUseCase,
            )

            if not isinstance(use_case, GenerateChannelDigestByNameUseCase):
                error_msg = f"Factory returned {type(use_case)}, expected GenerateChannelDigestByNameUseCase"
                logger.error(error_msg)
                raise TypeError(error_msg)
            result = await use_case.execute(
                user_id=user_id,
                channel_username=channel_username,
                hours=hours,
            )

            # Convert to expected format (backward compatibility)
            return {
                "digests": [
                    {
                        "channel": result.channel_username,
                        "summary": result.summary.text,
                        "post_count": result.post_count,
                        "tags": result.tags,
                        "channel_title": result.channel_title,
                    }
                ],
                "channel": result.channel_username,
                "generated_at": result.generated_at.isoformat(),
                "_metadata": {
                    "method": "new",
                    "summary_method": result.summary.method,
                    "confidence": result.summary.confidence,
                },
            }
        except Exception as e:
            logger.error(
                f"Error in new summarization, falling back to old: user_id={user_id}, channel={channel_username}, error={str(e)}",
                exc_info=True,
            )
            # Fall through to old implementation

    # Old implementation (fallback or feature flag disabled)
    logger.debug(
        f"Using old summarization system: user_id={user_id}, channel={channel_username}, hours={hours}"
    )

    # Get posts for this channel
    repository = PostRepository(db)

    # Debug: Check DB state before query
    db_name = db.name
    db_posts_count = await db.posts.count_documents({"user_id": user_id})
    db_channels_count = await db.channels.count_documents(
        {"user_id": user_id, "active": True}
    )
    logger.info(
        f"DB state before query: db_name={db_name}, posts={db_posts_count}, channels={db_channels_count}, user_id={user_id}"
    )

    # Also check all posts and channels to see what's actually in DB
    all_db_posts = await db.posts.count_documents({})
    all_db_channels = await db.channels.count_documents({})
    logger.info(
        f"Total DB state: all_posts={all_db_posts}, all_channels={all_db_channels}"
    )

    all_posts = await repository.get_posts_by_user_subscriptions(user_id, hours=hours)

    logger.info(f"Repository returned {len(all_posts)} posts for user {user_id}")

    channel_posts = [
        post for post in all_posts if post.get("channel_username") == channel_username
    ]

    logger.info(
        f"Filtered to {len(channel_posts)} posts for channel '{channel_username}'"
    )

    # Check if we have recent posts (within requested hours)
    logger.info(f"Checking if posts are recent (hours={hours})")
    has_recent_posts = False
    if channel_posts:
        from datetime import datetime as dt

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Check if any post is within the requested time window
        for post in channel_posts:
            post_date = post.get("date")
            if post_date:
                try:
                    # Convert ISO string to datetime if needed
                    if isinstance(post_date, str):
                        post_dt = dt.fromisoformat(post_date.replace("Z", "+00:00"))
                    elif isinstance(post_date, datetime):
                        post_dt = post_date
                    else:
                        # If it's not a string or datetime, assume it's recent
                        has_recent_posts = True
                        break

                    # Ensure both are timezone-aware for comparison
                    if post_dt.tzinfo is None:
                        post_dt = post_dt.replace(tzinfo=timezone.utc)
                    if cutoff.tzinfo is None:
                        cutoff = cutoff.replace(tzinfo=timezone.utc)

                    # Compare: post should be >= cutoff (more recent than cutoff)
                    if post_dt >= cutoff:
                        has_recent_posts = True
                        logger.debug(f"Found recent post: {post_dt} >= {cutoff}")
                        break
                except (ValueError, AttributeError, TypeError) as e:
                    # If date parsing fails, assume we have posts
                    logger.debug(
                        f"Date parsing failed for post {post.get('message_id')}: {e}, assuming recent"
                    )
                    has_recent_posts = True
                    break
        else:
            # If no posts have valid dates, but we have posts, consider them recent
            if channel_posts:
                logger.debug("Posts found but no valid dates, assuming recent")
                has_recent_posts = True

    logger.info(
        f"has_recent_posts={has_recent_posts}, channel_posts count={len(channel_posts)}"
    )

    if not channel_posts or not has_recent_posts:
        # Try to collect posts using MCP tool if none found in DB
        if not channel_posts:
            logger.info(f"No posts found for channel {channel_username} in DB")
        elif not has_recent_posts:
            logger.info(
                f"Posts found but none are recent enough (within {hours} hours)"
            )

        logger.info(
            f"Attempting to collect posts via MCP tool for channel {channel_username}..."
        )
        try:
            # Import and call collect_posts MCP tool directly
            from src.presentation.mcp.tools.channels.posts_management import (
                collect_posts,
            )

            collect_result = await collect_posts(
                channel_username=channel_username,
                user_id=user_id,
                wait_for_completion=True,
                timeout_seconds=60,
                hours=hours,
                fallback_to_7_days=True,
            )

            logger.info(f"collect_posts result: {collect_result}")

            if collect_result.get("status") == "success":
                collected_count = collect_result.get("collected_count", 0)
                logger.info(
                    f"Collected {collected_count} posts for channel {channel_username}"
                )

                # Re-query posts from DB after collection
                all_posts = await repository.get_posts_by_user_subscriptions(
                    user_id, hours=hours
                )
                channel_posts = [
                    post
                    for post in all_posts
                    if post.get("channel_username") == channel_username
                ]
                logger.info(f"Found {len(channel_posts)} posts after collection")
            else:
                error_msg = collect_result.get("error", "unknown error")
                logger.warning(
                    f"collect_posts failed for {channel_username}: {error_msg}"
                )
                return {
                    "digests": [],
                    "channel": channel_username,
                    "message": f"За последние {hours} часов постов из канала {channel_username} не найдено. "
                    f"Попробуйте позже - данные собираются автоматически.",
                    "generated_at": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.warning(
                f"Failed to collect posts for {channel_username}: {e}", exc_info=True
            )
            return {
                "digests": [],
                "channel": channel_username,
                "message": f"За последние {hours} часов постов из канала {channel_username} не найдено. "
                f"Данные собираются автоматически - попробуйте позже.",
                "generated_at": datetime.utcnow().isoformat(),
            }

    # Filter posts by date to ensure we only include posts within the requested time window
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    filtered_posts = []
    for post in channel_posts:
        post_date = post.get("date")
        if post_date:
            try:
                if isinstance(post_date, str):
                    post_dt = datetime.fromisoformat(post_date.replace("Z", "+00:00"))
                elif isinstance(post_date, datetime):
                    post_dt = post_date
                else:
                    # If date format is unknown, include post
                    filtered_posts.append(post)
                    continue

                # Ensure timezone-aware
                if post_dt.tzinfo is None:
                    post_dt = post_dt.replace(tzinfo=timezone.utc)

                # Only include posts within the requested time window
                if post_dt >= cutoff:
                    filtered_posts.append(post)
            except (ValueError, AttributeError, TypeError) as e:
                logger.debug(
                    f"Date parsing failed for post, excluding from digest: {e}"
                )
                # Exclude posts with invalid dates from digest
                continue
        else:
            # Posts without dates are excluded
            logger.debug(f"Post without date excluded from digest")

    logger.info(
        f"Filtered {len(channel_posts)} posts to {len(filtered_posts)} posts within {hours} hours window"
    )

    if not filtered_posts:
        return {
            "digests": [],
            "channel": channel_username,
            "message": f"За последние {hours} часов постов из канала {channel_username} не найдено. "
            f"Данные собираются автоматически - попробуйте позже.",
            "generated_at": datetime.utcnow().isoformat(),
        }

    # Normalize and summarize
    settings = get_settings()
    logger.info(
        f"Normalizing {len(filtered_posts)} posts before summarization for {hours}h period"
    )

    # Log post dates for debugging
    post_dates = []
    for post in filtered_posts[:5]:  # Log first 5 posts
        post_date = post.get("date")
        if post_date:
            post_dates.append(str(post_date)[:19])  # ISO format truncated
    logger.info(f"Post dates sample (first 5): {post_dates}")

    normalized_posts = await _normalize_post_dates(filtered_posts)
    logger.info(f"After normalization: {len(normalized_posts)} posts")

    # Log sample post texts to verify different content
    sample_texts = [p.get("text", "")[:100] for p in normalized_posts[:3]]
    logger.info(f"Sample post texts (first 100 chars of first 3): {sample_texts}")

    # CRITICAL: Verify all posts belong to the correct channel
    wrong_channel_posts = []
    for post in normalized_posts:
        post_channel = post.get("channel_username", "")
        if post_channel != channel_username:
            wrong_channel_posts.append(
                {
                    "message_id": post.get("message_id"),
                    "expected_channel": channel_username,
                    "actual_channel": post_channel,
                    "text_preview": post.get("text", "")[:100],
                }
            )

    if wrong_channel_posts:
        logger.error(
            f"⚠️  CRITICAL: Found {len(wrong_channel_posts)} posts with wrong channel_username "
            f"for digest generation! Expected: {channel_username}, "
            f"Wrong posts: {wrong_channel_posts[:5]}"
        )
        # Filter out wrong channel posts
        normalized_posts = [
            p for p in normalized_posts if p.get("channel_username") == channel_username
        ]
        logger.warning(
            f"Filtered out {len(wrong_channel_posts)} wrong channel posts, "
            f"remaining: {len(normalized_posts)}"
        )
    else:
        logger.info(
            f"✅ All {len(normalized_posts)} posts belong to correct channel: {channel_username}"
        )

    # Adaptive max_sentences based on post count and time period
    # Base: 8 sentences, scale up with more posts
    base_sentences = settings.digest_summary_sentences
    post_count = len(normalized_posts)

    # Scale: 1 sentence per 3-4 posts, but respect limits
    # For small counts (1-5 posts): use base (8)
    # For medium (6-15 posts): scale to 10-12
    # For large (16+ posts): scale to 12-15
    if post_count <= 5:
        max_sentences = base_sentences
    elif post_count <= 15:
        # Add 1-2 sentences for more content
        max_sentences = min(base_sentences + 2, 12)
    else:
        # For many posts, use more sentences to cover more topics
        max_sentences = min(base_sentences + 4, 15)

    logger.info(
        f"Using adaptive max_sentences={max_sentences} for {post_count} posts (base={base_sentences}, hours={hours})"
    )

<<<<<<< HEAD
    # Get channel title from existing channel document
    channel_title = existing.get("title") if existing else None

    # Generate summary - ensure we pass the actual filtered posts
    summary = await _generate_summary(
        normalized_posts,
        max_sentences,
        hours=hours,
        channel_username=channel_username,
        channel_title=channel_title,
    )
=======
    # Generate summary - ensure we pass the actual filtered posts
    summary = await _generate_summary(normalized_posts, max_sentences, hours=hours)
>>>>>>> origin/master
    logger.info(
        f"Generated summary length: {len(summary)} characters, first 200 chars: {summary[:200]}"
    )

    digest = {
        "channel": channel_username,
        "summary": summary,
        "post_count": len(filtered_posts),  # Use filtered count, not all posts
        "tags": [],
    }

    return {
        "digests": [digest],
        "channel": channel_username,
        "generated_at": datetime.utcnow().isoformat(),
    }


@mcp.tool()
async def get_channel_digest(user_id: int, hours: int = 24) -> Dict[str, Any]:
    """Generate digest from subscribed channels.

    Purpose:
        Generates digests for all user's active channels using new or old summarization system.

    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with digests list and metadata.
    """
    # Check feature flag
    if _settings.use_new_summarization:
        try:
            logger.info(
                f"Using new summarization system for channel digest: user_id={user_id}, hours={hours}"
            )
            use_case = create_channel_digest_use_case()
            # Verify it's the correct type (not a Future)
            from src.application.use_cases.generate_channel_digest import (
                GenerateChannelDigestUseCase,
            )

            if not isinstance(use_case, GenerateChannelDigestUseCase):
                error_msg = f"Factory returned {type(use_case)}, expected GenerateChannelDigestUseCase"
                logger.error(error_msg)
                raise TypeError(error_msg)
            result = await use_case.execute(user_id=user_id, hours=hours)

            # Convert to expected format (backward compatibility)
            digests = []
            for digest in result:
                digests.append(
                    {
                        "channel": digest.channel_username,
                        "summary": digest.summary.text,
                        "post_count": digest.post_count,
                        "tags": digest.tags,
                        "channel_title": digest.channel_title,
                    }
                )

            return {
                "digests": digests,
                "generated_at": datetime.utcnow().isoformat(),
                "_metadata": {
                    "method": "new",
                    "total_channels": len(digests),
                },
            }
        except Exception as e:
            logger.error(
                f"Error in new summarization, falling back to old: user_id={user_id}, error={str(e)}",
                exc_info=True,
            )
            # Fall through to old implementation

    # Old implementation (fallback or feature flag disabled)
    logger.debug(f"Using old summarization system: user_id={user_id}, hours={hours}")
    db = await get_database()
    repository = PostRepository(db)
    channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(
        length=100
    )
    digests = []

    try:
        all_posts = await repository.get_posts_by_user_subscriptions(
            user_id, hours=hours
        )
        logger.debug(
            f"Retrieved posts from MongoDB: user_id={user_id}, post_count={len(all_posts)}"
        )
    except Exception as e:
        logger.error(
            f"Error retrieving posts: user_id={user_id}, error={str(e)}", exc_info=True
        )
        return {"digests": [], "generated_at": datetime.utcnow().isoformat()}

    # Group posts by channel
    posts_by_channel: Dict[str, List[dict]] = {}
    for post in all_posts:
        channel_name = post.get("channel_username")
        if channel_name:
            if channel_name not in posts_by_channel:
                posts_by_channel[channel_name] = []
            posts_by_channel[channel_name].append(post)

    # Process each channel
    settings = get_settings()
    for channel in channels:
        channel_name = channel["channel_username"]
        try:
            posts = posts_by_channel.get(channel_name, [])
            if not posts:
                continue

            normalized_posts = await _normalize_post_dates(posts)
<<<<<<< HEAD
            # Get channel title from channel document
            channel_title = channel.get("title") if channel else None

            summary = await _generate_summary(
                normalized_posts,
                settings.digest_summary_sentences,
                hours=hours,
                channel_username=channel.get("channel_username"),
                channel_title=channel_title,
=======
            summary = await _generate_summary(
                normalized_posts, settings.digest_summary_sentences, hours=hours
>>>>>>> origin/master
            )

            digests.append(
                {
                    "channel": channel_name,
                    "summary": summary,
                    "post_count": len(posts),
                    "tags": channel.get("tags", []),
                }
            )
            await db.channels.update_one(
                {"_id": channel["_id"]},
                {"$set": {"last_digest": datetime.utcnow().isoformat()}},
            )
        except Exception as e:
            logger.error(
                f"Error processing channel: channel={channel_name}, error={str(e)}",
                exc_info=True,
            )

    return {"digests": digests, "generated_at": datetime.utcnow().isoformat()}


@mcp.tool()
async def request_channel_digest_async(
    user_id: int,
    chat_id: int,
    channel_username: str | None = None,
    hours: int = 72,
    language: str | None = None,
    max_sentences: int | None = None,
) -> Dict[str, Any]:
    """Request async channel digest generation (long-running task).

    Purpose:
        Creates and enqueues a long-running summarization task.
        Returns immediately with task ID and acknowledgment message.
        Actual summarization happens in background worker with extended timeout.

    Args:
        user_id: Telegram user ID
        chat_id: Telegram chat ID for sending results
        channel_username: Optional channel username (None = all channels)
        hours: Time window in hours (default 72)
        language: Language for summary ("ru" | "en", default from settings)
        max_sentences: Maximum sentences in summary (default from settings)

    Returns:
        Dict with task_id and ack_message.
    """
    from src.application.use_cases.request_channel_digest_async import (
        RequestChannelDigestAsyncUseCase,
    )

    # Use settings defaults if not provided
    if language is None:
        language = _settings.summarizer_language
    if max_sentences is None:
        max_sentences = _settings.digest_summary_sentences

    logger.info(
        f"Requesting async digest: user_id={user_id}, chat_id={chat_id}, "
        f"channel={channel_username}, hours={hours}, max_sentences={max_sentences}, language={language}"
    )

    use_case = RequestChannelDigestAsyncUseCase()
    result = await use_case.execute(
        user_id=user_id,
        chat_id=chat_id,
        channel_username=channel_username,
        hours=hours,
        language=language,
        max_sentences=max_sentences,
    )

    return {
        "task_id": result["task_id"],
        "ack_message": result["ack_message"],
    }
