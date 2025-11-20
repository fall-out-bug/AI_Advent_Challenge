#!/usr/bin/env python3
"""End-to-end test for the full notification flow."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

from src.infrastructure.database.mongo import get_db
from src.presentation.mcp.client import get_mcp_client
from src.workers.summary_worker import SummaryWorker


async def test_step_1_db_query():
    """Test: Can we query DB for user tasks?"""
    print("\n" + "=" * 60)
    print("STEP 1: Testing direct DB query")
    print("=" * 60)

    db = await get_db()
    user_id = 204047849

    # Test distinct user_ids
    user_ids = await db.tasks.distinct("user_id")
    print(f"✓ Found {len(user_ids)} users with tasks: {user_ids}")
    assert user_id in user_ids, f"User {user_id} not in list!"

    # Test query tasks
    raw_tasks = await db.tasks.find({"user_id": user_id}).to_list(length=200)
    print(f"✓ Found {len(raw_tasks)} total tasks for user {user_id}")

    active_tasks = [t for t in raw_tasks if not t.get("completed", False)]
    print(f"✓ Found {len(active_tasks)} active tasks")

    if active_tasks:
        print(f"  Sample tasks:")
        for i, task in enumerate(active_tasks[:3], 1):
            print(f"    {i}. {task.get('title', 'No title')[:50]}")
    else:
        print("  ⚠ NO ACTIVE TASKS FOUND!")

    return len(active_tasks) > 0


async def test_step_2_mcp_call():
    """Test: Can we call MCP get_summary?"""
    print("\n" + "=" * 60)
    print("STEP 2: Testing MCP get_summary call")
    print("=" * 60)

    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8004")
    print(f"Using MCP URL: {mcp_url}")

    mcp = get_mcp_client(server_url=mcp_url)
    user_id = 204047849

    try:
        print(f"Calling MCP get_summary for user {user_id}...")
        result = await asyncio.wait_for(
            mcp.call_tool("get_summary", {"user_id": user_id, "timeframe": "last_24h"}),
            timeout=10.0,
        )
        tasks = result.get("tasks", [])
        stats = result.get("stats", {})

        print(f"✓ MCP call successful")
        print(f"✓ MCP returned {len(tasks)} tasks")
        print(f"✓ Stats: {stats}")

        if tasks:
            print(f"  Sample tasks from MCP:")
            for i, task in enumerate(tasks[:3], 1):
                print(f"    {i}. {task.get('title', 'No title')[:50]}")
        else:
            print("  ⚠ MCP RETURNED 0 TASKS (expected - this is the bug)")

        return len(tasks)
    except asyncio.TimeoutError:
        print(f"✗ MCP call timed out after 10 seconds")
        return -2
    except Exception as e:
        print(f"✗ MCP call failed: {e}")
        import traceback

        traceback.print_exc()
        return -1


async def test_step_3_worker_method():
    """Test: Does worker._get_summary_text work with debug=True?"""
    print("\n" + "=" * 60)
    print("STEP 3: Testing worker._get_summary_text (debug=True)")
    print("=" * 60)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("✗ TELEGRAM_BOT_TOKEN not set")
        return None

    worker = SummaryWorker(bot_token)
    user_id = 204047849

    try:
        print(f"Calling worker._get_summary_text(user_id={user_id}, debug=True)...")
        text = await asyncio.wait_for(
            worker._get_summary_text(user_id, timeframe="last_24h", debug=True),
            timeout=30.0,
        )
        print(f"✓ Worker method returned text")
        print(f"✓ Text length: {len(text) if text else 0}")

        if text:
            print(f"\nPreview (first 300 chars):")
            print(text[:300])
            print("\nFull text:")
            print(text)

            if "No tasks found" in text:
                print("\n⚠ PROBLEM: Text says 'No tasks found' despite debug fallback!")
            elif "Debug Summary" in text and (
                "Tasks:" in text
                or len([line for line in text.split("\n") if line.strip()]) > 3
            ):
                print("\n✓ SUCCESS: Text contains task list!")
        else:
            print("✗ Text is None or empty!")

        return text
    except asyncio.TimeoutError:
        print(f"✗ Worker method timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"✗ Worker method failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_step_4_digest_flow():
    """Test: Can we get channel digest?"""
    print("\n" + "=" * 60)
    print("STEP 4: Testing channel digest flow")
    print("=" * 60)

    db = await get_db()
    user_id = 204047849

    # Check channels
    channels = await db.channels.find({"user_id": user_id, "active": True}).to_list(
        length=100
    )
    print(f"✓ Found {len(channels)} active channels for user {user_id}")

    if channels:
        for ch in channels:
            print(f"  - {ch.get('channel_username')}")

        # Test MCP digest call
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8004")
        mcp = get_mcp_client(server_url=mcp_url)

        try:
            result = await mcp.call_tool(
                "get_channel_digest", {"user_id": user_id, "hours": 168}
            )
            digests = result.get("digests", [])
            print(f"\n✓ MCP digest call successful")
            print(f"✓ Returned {len(digests)} digests")

            if digests:
                for d in digests:
                    print(f"  - {d.get('channel')}: {d.get('post_count', 0)} posts")
            else:
                print("  ⚠ No digests returned")
        except Exception as e:
            print(f"✗ MCP digest call failed: {e}")
    else:
        print("⚠ No channels found")


async def test_step_5_telegram_send():
    """Test: Can we send message to Telegram?"""
    print("\n" + "=" * 60)
    print("STEP 5: Testing Telegram send capability")
    print("=" * 60)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("✗ TELEGRAM_BOT_TOKEN not set")
        return False

    from aiogram import Bot

    bot = Bot(token=bot_token)
    user_id = 204047849

    try:
        # Try to get bot info
        bot_info = await bot.get_me()
        print(f"✓ Bot authenticated: @{bot_info.username}")

        # Try to get chat info (this will fail if chat doesn't exist)
        try:
            chat = await bot.get_chat(user_id)
            print(f"✓ Chat accessible: {chat.type} (ID: {chat.id})")

            # Test send (but don't actually send to avoid spam)
            print(f"✓ Ready to send messages to user {user_id}")
            print(f"  (Not sending test message to avoid spam)")
            return True
        except Exception as e:
            print(f"✗ Cannot access chat with user {user_id}: {e}")
            print(f"  Make sure user has started conversation with bot!")
            return False
    except Exception as e:
        print(f"✗ Telegram bot error: {e}")
        return False
    finally:
        await bot.session.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FULL FLOW END-TO-END TEST")
    print("=" * 60)

    results = {}

    results["step1_db"] = await test_step_1_db_query()
    results["step2_mcp"] = await test_step_2_mcp_call()
    results["step3_worker"] = await test_step_3_worker_method()
    await test_step_4_digest_flow()
    results["step5_telegram"] = await test_step_5_telegram_send()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Step 1 (DB query): {'✓' if results.get('step1_db') else '✗'}")
    print(f"Step 2 (MCP call): {results.get('step2_mcp', -1)} tasks returned")
    print(f"Step 3 (Worker method): {'✓' if results.get('step3_worker') else '✗'}")
    print(f"Step 5 (Telegram): {'✓' if results.get('step5_telegram') else '✗'}")

    if (
        results.get("step1_db")
        and results.get("step3_worker")
        and "No tasks found" not in str(results.get("step3_worker", ""))
    ):
        print("\n✓ ALL CRITICAL STEPS PASSED")
    else:
        print("\n⚠ SOME STEPS FAILED - check details above")

    # Cleanup
    from src.infrastructure.database.mongo import get_client

    client = await get_client()
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
