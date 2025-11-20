#!/usr/bin/env python3
"""Diagnostic script for XOR channel digest issue.

Purpose:
    Debug why XOR channel digest fails with "Ошибка при генерации суммаризации"
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Determine project root
ROOT_DIR = Path(__file__).resolve().parents[2]

# Load .env file explicitly
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Try default locations

# Debug: check if LLM_URL is loaded
llm_url = os.getenv("LLM_URL", "")
print(f"DEBUG: LLM_URL from env: '{llm_url}'")

# Add src to path
sys.path.insert(0, str(ROOT_DIR))

from src.infrastructure.database.mongo import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.repositories.post_repository import PostRepository

logger = get_logger("diag_xor")


async def diagnose_xor_digest(user_id: int = None, hours: int = 168):
    """Diagnose XOR channel digest generation.

    Args:
        user_id: Telegram user ID (if None, will try to find from DB)
        hours: Hours to look back (default 168 = 7 days)
    """
    print("=" * 80)
    print(f"XOR Channel Digest Diagnosis")
    print("=" * 80)
    print()

    db = await get_db()

    # 1. Find XOR channel
    print("1. Finding XOR channel in database:")
    print("-" * 80)

    channel_query = {
        "channel_username": {"$regex": "xor", "$options": "i"},
        "active": True,
    }
    if user_id:
        channel_query["user_id"] = user_id

    channels = await db.channels.find(channel_query).to_list(length=10)

    if not channels:
        print("   ❌ No XOR channels found in database")
        print(f"   Query: {channel_query}")
        return

    print(f"   Found {len(channels)} XOR channel(s):")
    for ch in channels:
        print(
            f"   - @{ch.get('channel_username')} | {ch.get('title')} | user_id={ch.get('user_id')}"
        )

    xor_channel = channels[0]
    channel_username = xor_channel.get("channel_username")
    found_user_id = xor_channel.get("user_id")

    print(f"\n   Using channel: @{channel_username}, user_id={found_user_id}")
    print()

    # 2. Check posts
    print("2. Checking posts for XOR channel:")
    print("-" * 80)

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    post_repo = PostRepository(db)
    posts = await post_repo.get_posts_by_channel(
        channel_username, since, user_id=found_user_id
    )

    print(f"   Posts found: {len(posts)}")
    print(f"   Time window: {hours} hours (since {since.isoformat()})")

    if posts:
        print(f"\n   Sample posts (first 3):")
        for i, post in enumerate(posts[:3], 1):
            post_text = post.get("text", "")[:200]
            post_date = post.get("date")
            print(f"   {i}. Date: {post_date}, Length: {len(post.get('text', ''))}")
            print(f"      Preview: {post_text}...")
    else:
        print("   ❌ No posts found for XOR channel")
        print("   This might be the issue - posts need to be collected first")
        return

    print()

    # 3. Test summarization
    print("3. Testing summarization:")
    print("-" * 80)

    try:
        from src.infrastructure.llm.summarizer import summarize_posts

        # Convert posts to dict format
        posts_dict = []
        for post in posts[:20]:  # Limit to 20 posts for testing
            posts_dict.append(
                {
                    "text": post.get("text", ""),
                    "date": post.get("date"),
                }
            )

        print(f"   Testing with {len(posts_dict)} posts")
        print(
            f"   Total text length: {sum(len(p.get('text', '')) for p in posts_dict)}"
        )

        summary = await summarize_posts(
            posts_dict, max_sentences=25, time_period_hours=hours
        )

        print(f"   ✅ Summarization successful!")
        print(f"   Summary length: {len(summary)} characters")
        print(f"   Summary preview: {summary[:300]}...")

    except Exception as e:
        print(f"   ❌ Summarization failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback

        traceback.print_exc()

    print()

    # 4. Test full digest generation
    print("4. Testing full digest generation:")
    print("-" * 80)

    try:
        from src.application.use_cases.generate_channel_digest_by_name import (
            GenerateChannelDigestByNameUseCase,
        )

        use_case = GenerateChannelDigestByNameUseCase()
        result = await use_case.execute(
            user_id=found_user_id,
            channel_username=channel_username,
            hours=hours,
        )

        print(f"   ✅ Digest generation successful!")
        print(f"   Channel: {result.channel_username}")
        print(f"   Title: {result.channel_title}")
        print(f"   Post count: {result.post_count}")
        print(f"   Summary length: {len(result.summary.text)}")
        print(f"   Summary method: {result.summary.method}")
        print(f"   Summary confidence: {result.summary.confidence}")
        print(f"   Summary preview: {result.summary.text[:300]}...")

    except Exception as e:
        print(f"   ❌ Digest generation failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 80)
    print("Diagnosis complete")
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose XOR channel digest issues")
    parser.add_argument("--user-id", type=int, help="Telegram user ID")
    parser.add_argument(
        "--hours",
        type=int,
        default=168,
        help="Hours to look back (default: 168 = 7 days)",
    )

    args = parser.parse_args()

    asyncio.run(diagnose_xor_digest(user_id=args.user_id, hours=args.hours))


if __name__ == "__main__":
    main()
