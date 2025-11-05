#!/usr/bin/env python3
"""Diagnostic script for channel search.

Purpose:
    Debug channel search strategies and show detailed results from each source.
    Shows scoring breakdown, timing, and source attribution.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.clients.telegram_utils import search_channels_by_name
from src.infrastructure.cache.dialogs_cache import PublicChannelsCache
from src.infrastructure.clients.bot_api_resolver import BotApiChannelResolver
from src.infrastructure.logging import get_logger

logger = get_logger("diag_search")


async def diagnose_search(query: str, limit: int = 5):
    """Diagnose channel search for a given query.

    Purpose:
        Show detailed breakdown of search results from all sources:
        - MongoDB cache
        - MTProto dialogs search
        - Bot API fallback
        - Scoring details

    Args:
        query: Search query
        limit: Maximum results to show
    """
    print("=" * 80)
    print(f"Channel Search Diagnosis: '{query}'")
    print("=" * 80)
    print()
    
    # 1. Check MongoDB cache
    print("1. MongoDB Cache:")
    print("-" * 80)
    try:
        cache = PublicChannelsCache()
        cached_channels = await cache.get_cached()
        cache_age = await cache.get_cache_age()
        
        print(f"   Cache size: {len(cached_channels)} channels")
        if cache_age is not None:
            print(f"   Cache age: {cache_age:.1f} hours")
        else:
            print("   Cache age: N/A (empty)")
        
        # Search in cache
        if cached_channels:
            query_lower = query.replace("_", " ").replace("-", " ").strip().lower()
            cache_matches = []
            
            for channel in cached_channels:
                title = channel.get("title", "").lower()
                username = channel.get("username", "").lower()
                
                if query_lower in title or query_lower in username:
                    cache_matches.append({
                        "username": channel.get("username"),
                        "title": channel.get("title"),
                        "match_type": "title" if query_lower in title else "username"
                    })
            
            if cache_matches:
                print(f"   Matches in cache: {len(cache_matches)}")
                for i, match in enumerate(cache_matches[:limit], 1):
                    print(f"   {i}. @{match['username']} | {match['title']} ({match['match_type']})")
            else:
                print("   No matches in cache")
        else:
            print("   Cache is empty")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 2. Full search (includes all strategies)
    print("2. Full Search Results:")
    print("-" * 80)
    start_time = time.time()
    
    try:
        results = await search_channels_by_name(query, limit=limit)
        elapsed = time.time() - start_time
        
        print(f"   Search time: {elapsed:.3f}s")
        print(f"   Results found: {len(results)}")
        print()
        
        if results:
            for i, result in enumerate(results, 1):
                score = result.get("score", 0)
                username = result.get("username", "N/A")
                title = result.get("title", "N/A")
                chat_id = result.get("chat_id", "N/A")
                
                print(f"   {i}. @{username}")
                print(f"      Title: {title}")
                print(f"      Score: {score}")
                print(f"      Chat ID: {chat_id}")
                print()
        else:
            print("   No results found")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 3. Bot API fallback test
    print("3. Bot API Fallback Test:")
    print("-" * 80)
    username_pattern = query.lstrip("@").strip()
    
    # Check if query looks like username
    is_username_like = all(c.isalnum() or c == "_" for c in username_pattern) if username_pattern else False
    print(f"   Query looks like username: {is_username_like}")
    
    if is_username_like:
        try:
            resolver = BotApiChannelResolver()
            try:
                bot_start = time.time()
                bot_result = await resolver.resolve_username(username_pattern)
                bot_elapsed = time.time() - bot_start
                
                if bot_result:
                    print(f"   Bot API found: @{bot_result['username']} | {bot_result['title']}")
                    print(f"   Bot API time: {bot_elapsed:.3f}s")
                else:
                    print("   Bot API: Channel not found")
            finally:
                await resolver.close()
        except Exception as e:
            print(f"   Bot API error: {e}")
    else:
        print("   Skipping Bot API test (query doesn't look like username)")
    print()
    
    print("=" * 80)
    print("Diagnosis complete")
    print("=" * 80)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/diag_search.py <query> [limit]")
        print()
        print("Examples:")
        print("  python scripts/diag_search.py 'крупнокалиберный_переполох'")
        print("  python scripts/diag_search.py 'деградат нация' 10")
        sys.exit(1)
    
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    asyncio.run(diagnose_search(query, limit))


if __name__ == "__main__":
    main()

