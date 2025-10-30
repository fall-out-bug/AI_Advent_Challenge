#!/usr/bin/env python3
"""Script to get channel digest summary for user subscriptions.

This script requires MongoDB to be available. 
To get your digest summary, you need to:

1. Make sure MongoDB is running and dependencies are installed:
   pip install motor pymongo

2. Run the script with your Telegram user ID:
   python scripts/get_digest.py <your_user_id> [hours]

Example:
   python scripts/get_digest.py 123456789        # Last 24 hours
   python scripts/get_digest.py 123456789 48    # Last 48 hours

Alternatively, you can use the Telegram bot:
   - Send /menu command
   - Click "📮 Digest" button
   - Bot will show your channel digest automatically
"""

import sys

try:
    import asyncio
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv(project_root / ".env")
    except ImportError:
        pass  # dotenv not available, rely on system env vars
    
    from src.presentation.mcp.tools.digest_tools import get_channel_digest, list_channels
    
    
    def format_digest(digest_data: dict) -> str:
        """Format digest data for display."""
        digests = digest_data.get("digests", [])
        generated_at = digest_data.get("generated_at", "")
        
        if not digests:
            return "📰 No digests available. No posts found in subscribed channels."
        
        output = []
        output.append("=" * 60)
        output.append("📰 CHANNEL DIGEST SUMMARY")
        output.append("=" * 60)
        output.append(f"Generated at: {generated_at}")
        output.append(f"Channels: {len(digests)}")
        output.append("")
        
        for i, digest in enumerate(digests, 1):
            channel = digest.get("channel", "unknown")
            summary = digest.get("summary", "")
            post_count = digest.get("post_count", 0)
            tags = digest.get("tags", [])
            
            output.append(f"{i}. 📌 {channel}")
            if tags:
                output.append(f"   Tags: {', '.join(tags)}")
            output.append(f"   Posts: {post_count}")
            output.append(f"   Summary: {summary}")
            output.append("")
        
        output.append("=" * 60)
        return "\n".join(output)
    
    
    async def main() -> None:
        """Main function to get and display digest."""
        if len(sys.argv) < 2:
            print(__doc__)
            sys.exit(1)
        
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ Error: Invalid user_id '{sys.argv[1]}'. Must be an integer.")
            sys.exit(1)
        
        hours = 24
        if len(sys.argv) >= 3:
            try:
                hours = int(sys.argv[2])
            except ValueError:
                print(f"⚠️  Warning: Invalid hours '{sys.argv[2]}', using default 24")
                hours = 24
        
        print(f"\n🔍 Fetching digest for user {user_id} (last {hours} hours)...\n")
        
        # First check if user has any subscriptions
        try:
            channels = await list_channels(user_id=user_id, limit=100)  # type: ignore[arg-type]
            subscribed_channels = channels.get("channels", [])
            
            if not subscribed_channels:
                print(f"⚠️  No subscribed channels found for user {user_id}.")
                print("\nTo subscribe to a channel, use:")
                print("  python scripts/subscribe_channel.py <user_id> <channel_username>")
                sys.exit(0)
            
            print(f"📋 Found {len(subscribed_channels)} subscribed channel(s):")
            for ch in subscribed_channels:
                print(f"   - {ch.get('channel_username', 'unknown')}")
            print()
        except Exception as e:
            print(f"⚠️  Warning: Could not list channels: {e}")
            print("Continuing with digest generation...\n")
        
        # Get digest
        try:
            digest_data = await get_channel_digest(user_id=user_id, hours=hours)  # type: ignore[arg-type]
            print(format_digest(digest_data))
        except Exception as e:
            print(f"❌ Error generating digest: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    if "bson" in str(e) or "motor" in str(e):
        print(__doc__)
        print("\n❌ MongoDB dependencies not installed.")
        print("Install them with: pip install motor pymongo")
        sys.exit(1)
    else:
        raise
