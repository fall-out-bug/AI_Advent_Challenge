#!/usr/bin/env python3
"""Export channel posts to file for comparison.

Purpose:
    Export posts from specific channels to compare and identify mixing issues.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Load environment variables
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.logging import get_logger

logger = get_logger("export_posts")


async def export_channel_posts(user_id: int, channels: list[str], hours: int = 168):
    """Export posts from channels to file.
    
    Args:
        user_id: Telegram user ID
        channels: List of channel usernames
        hours: Hours to look back (default 168 = 7 days)
    """
    print("=" * 80)
    print(f"Exporting posts for {len(channels)} channels")
    print("=" * 80)
    print()
    
    db = await get_db()
    post_repo = PostRepository(db)
    
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    all_posts = {}
    
    for channel_username in channels:
        print(f"Fetching posts for @{channel_username}...")
        posts = await post_repo.get_posts_by_channel(
            channel_username, since, user_id=user_id
        )
        
        print(f"  Found {len(posts)} posts")
        
        # Get channel metadata
        channel_doc = await db.channels.find_one({
            "user_id": user_id,
            "channel_username": channel_username,
            "active": True
        })
        
        channel_title = channel_doc.get("title") if channel_doc else None
        channel_id = channel_doc.get("channel_id") if channel_doc else None
        
        all_posts[channel_username] = {
            "channel_username": channel_username,
            "channel_title": channel_title,
            "channel_id": channel_id,
            "posts_count": len(posts),
            "posts": []
        }
        
        # Format posts for export
        for post in posts:
            post_data = {
                "message_id": post.get("message_id"),
                "date": str(post.get("date")) if post.get("date") else None,
                "text": post.get("text", ""),
                "text_length": len(post.get("text", "")),
                "channel_username_db": post.get("channel_username"),  # What's stored in DB
                "channel_id_db": post.get("channel_id"),  # What's stored in DB
                "user_id_db": post.get("user_id"),  # What's stored in DB
            }
            all_posts[channel_username]["posts"].append(post_data)
        
        # Show sample posts
        if posts:
            print(f"  Sample posts (first 3):")
            for i, post in enumerate(posts[:3], 1):
                text_preview = post.get("text", "")[:150]
                date_str = str(post.get("date"))[:19] if post.get("date") else "N/A"
                print(f"    {i}. Date: {date_str}, Length: {len(post.get('text', ''))}")
                print(f"       Text: {text_preview}...")
                print(f"       DB channel_username: {post.get('channel_username')}")
                print(f"       DB channel_id: {post.get('channel_id')}")
        
        print()
    
    # Write to file
    output_file = Path(__file__).parent.parent / "channel_posts_export.json"
    
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "time_window_hours": hours,
        "since": since.isoformat(),
        "channels": all_posts
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported to: {output_file}")
    print(f"   Total channels: {len(all_posts)}")
    print(f"   Total posts: {sum(len(ch['posts']) for ch in all_posts.values())}")
    
    # Also create a human-readable text file
    text_file = Path(__file__).parent.parent / "channel_posts_export.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CHANNEL POSTS EXPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Exported at: {export_data['exported_at']}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Time window: {hours} hours (since {since.isoformat()})\n")
        f.write("\n")
        
        for channel_username, channel_data in all_posts.items():
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write(f"CHANNEL: @{channel_username}\n")
            f.write(f"Title: {channel_data['channel_title']}\n")
            f.write(f"Channel ID (DB): {channel_data['channel_id']}\n")
            f.write(f"Posts count: {channel_data['posts_count']}\n")
            f.write("=" * 80 + "\n")
            f.write("\n")
            
            for i, post in enumerate(channel_data['posts'], 1):
                f.write(f"\n--- POST {i} ---\n")
                f.write(f"Message ID: {post['message_id']}\n")
                f.write(f"Date: {post['date']}\n")
                f.write(f"Text length: {post['text_length']}\n")
                f.write(f"DB channel_username: {post['channel_username_db']}\n")
                f.write(f"DB channel_id: {post['channel_id_db']}\n")
                f.write(f"DB user_id: {post['user_id_db']}\n")
                f.write(f"\nText:\n{post['text']}\n")
                f.write("\n")
    
    print(f"✅ Also exported human-readable text to: {text_file}")
    
    # Check for potential mixing issues
    print("\n" + "=" * 80)
    print("POTENTIAL MIXING ISSUES:")
    print("=" * 80)
    
    all_channel_ids = set()
    all_channel_usernames = set()
    
    for channel_username, channel_data in all_posts.items():
        for post in channel_data['posts']:
            post_channel_id = post.get('channel_id_db')
            post_channel_username = post.get('channel_username_db')
            
            if post_channel_id:
                all_channel_ids.add(post_channel_id)
            if post_channel_username:
                all_channel_usernames.add(post_channel_username)
    
    # Check if posts have wrong channel_id or channel_username
    for channel_username, channel_data in all_posts.items():
        expected_channel_id = channel_data.get('channel_id')
        expected_channel_username = channel_username
        
        wrong_posts = []
        for post in channel_data['posts']:
            post_channel_id = post.get('channel_id_db')
            post_channel_username = post.get('channel_username_db')
            
            if post_channel_id and post_channel_id != expected_channel_id:
                wrong_posts.append({
                    'message_id': post['message_id'],
                    'expected_channel_id': expected_channel_id,
                    'actual_channel_id': post_channel_id,
                    'expected_channel_username': expected_channel_username,
                    'actual_channel_username': post_channel_username,
                })
            elif post_channel_username and post_channel_username != expected_channel_username:
                wrong_posts.append({
                    'message_id': post['message_id'],
                    'expected_channel_id': expected_channel_id,
                    'actual_channel_id': post_channel_id,
                    'expected_channel_username': expected_channel_username,
                    'actual_channel_username': post_channel_username,
                })
        
        if wrong_posts:
            print(f"\n⚠️  @{channel_username}: Found {len(wrong_posts)} posts with wrong channel_id/username:")
            for wp in wrong_posts[:5]:  # Show first 5
                print(f"   Message ID {wp['message_id']}:")
                print(f"      Expected: @{wp['expected_channel_username']} (ID: {wp['expected_channel_id']})")
                print(f"      Actual: @{wp['actual_channel_username']} (ID: {wp['actual_channel_id']})")
            if len(wrong_posts) > 5:
                print(f"   ... and {len(wrong_posts) - 5} more")
    
    # Check for duplicate channel_ids across channels
    channel_ids_by_channel = {}
    for channel_username, channel_data in all_posts.items():
        channel_ids = set()
        for post in channel_data['posts']:
            if post.get('channel_id_db'):
                channel_ids.add(post['channel_id_db'])
        if channel_ids:
            channel_ids_by_channel[channel_username] = channel_ids
    
    # Find overlapping channel_ids
    all_ids = {}
    for channel_username, ids in channel_ids_by_channel.items():
        for channel_id in ids:
            if channel_id not in all_ids:
                all_ids[channel_id] = []
            all_ids[channel_id].append(channel_username)
    
    overlapping = {cid: channels for cid, channels in all_ids.items() if len(channels) > 1}
    if overlapping:
        print(f"\n⚠️  Found {len(overlapping)} channel_ids that appear in multiple channels:")
        for channel_id, channels_list in list(overlapping.items())[:10]:
            print(f"   Channel ID {channel_id} appears in: {', '.join(f'@{c}' for c in channels_list)}")
    
    print("\n" + "=" * 80)
    print("Export complete!")
    print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export channel posts for comparison")
    parser.add_argument("--user-id", type=int, help="Telegram user ID", default=204047849)
    parser.add_argument("--hours", type=int, default=168, help="Hours to look back (default: 168 = 7 days)")
    parser.add_argument(
        "--channels",
        nargs="+",
        default=["alexgladkovblog", "onaboka", "xor_journal"],
        help="Channel usernames (default: alexgladkovblog onaboka xor_journal)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(export_channel_posts(
        user_id=args.user_id,
        channels=args.channels,
        hours=args.hours
    ))


if __name__ == "__main__":
    main()

