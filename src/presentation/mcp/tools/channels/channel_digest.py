"""Channel digest generation tools.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from datetime import datetime
from typing import Any, Dict, List

from src.presentation.mcp.server import mcp
from src.presentation.mcp.tools.channels.utils import get_database
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.logging import get_logger
from src.infrastructure.config.settings import get_settings

logger = get_logger("channel_digest")


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


async def _generate_summary(posts: List[dict], max_sentences: int) -> str:
    """Generate summary from posts with fallback.
    
    Args:
        posts: List of normalized post dictionaries
        max_sentences: Maximum sentences in summary
        
    Returns:
        Summary text
    """
    try:
        from src.infrastructure.llm.summarizer import summarize_posts
        return await summarize_posts(posts, max_sentences=max_sentences)
    except ModuleNotFoundError:
        # Fallback: simple heuristic summary
        texts: List[str] = []
        for p in posts[:min(20, len(posts))]:
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
        return ". ".join(parts[:max_sentences])[:1200]


@mcp.tool()
async def get_channel_digest_by_name(user_id: int, channel_username: str, hours: int = 72) -> Dict[str, Any]:
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
    
    # Auto-subscribe if needed
    existing = await db.channels.find_one({
        "user_id": user_id,
        "channel_username": channel_username,
        "active": True
    })
    
    if not existing:
        logger.info("Auto-subscribing to channel", user_id=user_id, channel=channel_username)
        channel_doc = {
            "user_id": user_id,
            "channel_username": channel_username,
            "tags": [],
            "subscribed_at": datetime.utcnow().isoformat(),
            "last_digest": None,
            "active": True,
        }
        await db.channels.insert_one(channel_doc)
    
    # Get posts for this channel
    repository = PostRepository(db)
    all_posts = await repository.get_posts_by_user_subscriptions(user_id, hours=hours)
    channel_posts = [
        post for post in all_posts 
        if post.get("channel_username") == channel_username
    ]
    
    if not channel_posts:
        return {
            "digests": [],
            "channel": channel_username,
            "message": f"За последние {hours} часов постов из канала {channel_username} не найдено.",
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # Normalize and summarize
    settings = get_settings()
    normalized_posts = await _normalize_post_dates(channel_posts)
    summary = await _generate_summary(normalized_posts, settings.digest_summary_sentences)
    
    digest = {
        "channel": channel_username,
        "summary": summary,
        "post_count": len(channel_posts),
        "tags": [],
    }
    
    return {
        "digests": [digest],
        "channel": channel_username,
        "generated_at": datetime.utcnow().isoformat()
    }


@mcp.tool()
async def get_channel_digest(user_id: int, hours: int = 24) -> Dict[str, Any]:
    """Generate digest from subscribed channels.

    Reads posts from MongoDB and generates summaries per channel.
    
    Args:
        user_id: Telegram user ID
        hours: Hours to look back (default 24)

    Returns:
        Dict with digests list
    """
    db = await get_database()
    repository = PostRepository(db)
    channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(length=100)
    digests = []
    
    try:
        all_posts = await repository.get_posts_by_user_subscriptions(user_id, hours=hours)
        logger.debug("Retrieved posts from MongoDB", user_id=user_id, post_count=len(all_posts))
    except Exception as e:
        logger.error("Error retrieving posts", user_id=user_id, error=str(e), exc_info=True)
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
            summary = await _generate_summary(normalized_posts, settings.digest_summary_sentences)
            
            digests.append({
                "channel": channel_name,
                "summary": summary,
                "post_count": len(posts),
                "tags": channel.get("tags", []),
            })
            await db.channels.update_one(
                {"_id": channel["_id"]},
                {"$set": {"last_digest": datetime.utcnow().isoformat()}}
            )
        except Exception as e:
            logger.error("Error processing channel", channel=channel_name, error=str(e), exc_info=True)

    return {"digests": digests, "generated_at": datetime.utcnow().isoformat()}

