#!/usr/bin/env python3
"""Direct test of worker method with debug=True."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

from src.workers.summary_worker import SummaryWorker


async def test():
    print("="*60)
    print("TESTING WORKER._get_summary_text with debug=True")
    print("="*60)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("✗ TELEGRAM_BOT_TOKEN not set")
        return

    worker = SummaryWorker(bot_token)
    user_id = 204047849

    print(f"\nCalling: worker._get_summary_text(user_id={user_id}, timeframe='last_24h', debug=True)")
    print("Expecting: Debug mode should query DB directly, bypass MCP")

    try:
        text = await asyncio.wait_for(
            worker._get_summary_text(user_id, timeframe="last_24h", debug=True),
            timeout=30.0
        )

        print(f"\n✓ Method returned")
        print(f"✓ Text length: {len(text) if text else 0}")
        print(f"\n" + "="*60)
        print("RESULT TEXT:")
        print("="*60)
        print(text)
        print("="*60)

        if "No tasks found" in text:
            print("\n✗ PROBLEM: Still says 'No tasks found'")
            print("  Debug fallback did not work!")
        elif "Debug Summary" in text and len(text) > 100:
            print("\n✓ SUCCESS: Got task summary!")
            task_count = text.count('🟢') + text.count('🔴') + text.count('🟡') + text.count('⚪')
            if task_count > 0:
                print(f"  Found {task_count} task emoji markers in text")
        else:
            print("\n? UNEXPECTED: Got text but format is unclear")

    except asyncio.TimeoutError:
        print("\n✗ TIMEOUT: Method took >30 seconds")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await worker._cleanup()


if __name__ == "__main__":
    asyncio.run(test())
