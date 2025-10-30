#!/usr/bin/env python3
"""Debug script to test summary and digest generation directly."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).parent
sys.path.insert(0, str(_root))

from src.infrastructure.database.mongo import get_db, get_client
from src.presentation.mcp.client import get_mcp_client
from src.presentation.mcp.tools.reminder_tools import get_summary
from src.presentation.mcp.tools.digest_tools import get_channel_digest


async def test_summary(user_id: int):
    """Test summary generation."""
    print(f"\n{'='*60}")
    print(f"Testing SUMMARY for user_id={user_id}")
    print(f"{'='*60}\n")
    
    # Test direct MCP tool call
    print("1. Calling get_summary MCP tool directly...")
    try:
        result = await get_summary(user_id, timeframe="last_24h")
        print(f"   ✓ Tool call successful")
        print(f"   Tasks count: {len(result.get('tasks', []))}")
        print(f"   Stats: {result.get('stats', {})}")
        
        if result.get('tasks'):
            print("\n   Sample tasks:")
            for i, task in enumerate(result['tasks'][:3], 1):
                print(f"   {i}. {task.get('title', 'No title')} (completed: {task.get('completed', False)})")
        else:
            print("   ⚠ No tasks returned!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test via HTTP MCP client
    print("\n2. Calling get_summary via HTTP MCP client...")
    try:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8004")
        mcp = get_mcp_client(server_url=mcp_url)
        result = await mcp.call_tool("get_summary", {"user_id": user_id, "timeframe": "last_24h"})
        print(f"   ✓ HTTP call successful")
        print(f"   Tasks count: {len(result.get('tasks', []))}")
        print(f"   Stats: {result.get('stats', {})}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_digest(user_id: int):
    """Test digest generation."""
    print(f"\n{'='*60}")
    print(f"Testing DIGEST for user_id={user_id}")
    print(f"{'='*60}\n")
    
    # Check channels first
    print("1. Checking subscribed channels...")
    try:
        db = await get_db()
        channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(length=100)
        print(f"   Found {len(channels)} active channels:")
        for ch in channels:
            print(f"   - {ch.get('channel_username')} (tags: {ch.get('tags', [])})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test direct MCP tool call
    print("\n2. Calling get_channel_digest MCP tool directly...")
    try:
        result = await get_channel_digest(user_id, hours=168)  # 7 days for debug
        print(f"   ✓ Tool call successful")
        print(f"   Digests count: {len(result.get('digests', []))}")
        
        if result.get('digests'):
            print("\n   Sample digests:")
            for i, digest in enumerate(result['digests'][:3], 1):
                print(f"   {i}. Channel: {digest.get('channel')}")
                print(f"      Posts: {digest.get('post_count', 0)}")
                print(f"      Summary: {digest.get('summary', '')[:100]}...")
        else:
            print("   ⚠ No digests returned!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test via HTTP MCP client
    print("\n3. Calling get_channel_digest via HTTP MCP client...")
    try:
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8004")
        mcp = get_mcp_client(server_url=mcp_url)
        result = await mcp.call_tool("get_channel_digest", {"user_id": user_id, "hours": 168})
        print(f"   ✓ HTTP call successful")
        print(f"   Digests count: {len(result.get('digests', []))}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_db_queries(user_id: int):
    """Test database queries directly."""
    print(f"\n{'='*60}")
    print(f"Testing DATABASE queries for user_id={user_id}")
    print(f"{'='*60}\n")
    
    try:
        db = await get_db()
        
        # Query tasks
        print("1. Querying tasks...")
        task_query = {
            "user_id": user_id,
            "$or": [
                {"completed": False},
                {"completed": {"$exists": False}},
            ],
        }
        tasks = await db.tasks.find(task_query).to_list(length=10)
        print(f"   Found {len(tasks)} active tasks")
        if tasks:
            print("   Sample tasks:")
            for i, task in enumerate(tasks[:5], 1):
                print(f"   {i}. {task.get('title', 'No title')}")
                print(f"      ID: {task.get('_id')}")
                print(f"      Completed: {task.get('completed', False)}")
                print(f"      Deadline: {task.get('deadline', 'None')}")
        
        # Query channels
        print("\n2. Querying channels...")
        channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(length=10)
        print(f"   Found {len(channels)} active channels")
        if channels:
            print("   Sample channels:")
            for i, ch in enumerate(channels[:5], 1):
                print(f"   {i}. {ch.get('channel_username')}")
                print(f"      ID: {ch.get('_id')}")
                print(f"      Tags: {ch.get('tags', [])}")
                
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main debug function."""
    user_id = 204047849
    
    print(f"Starting debug for user_id={user_id}")
    print(f"MONGODB_URL: {os.getenv('MONGODB_URL', 'NOT SET')}")
    print(f"MCP_SERVER_URL: {os.getenv('MCP_SERVER_URL', 'NOT SET')}")
    
    await test_db_queries(user_id)
    await test_summary(user_id)
    await test_digest(user_id)
    
    print(f"\n{'='*60}")
    print("Debug complete!")
    print(f"{'='*60}\n")
    
    # Cleanup
    client = await get_client()
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
