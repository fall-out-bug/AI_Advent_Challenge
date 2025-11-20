#!/usr/bin/env python3
"""Script to initialize Pyrogram session for Telegram channel access.

Run this once to authenticate with your Telegram account.
After first run, session will be saved and you won't need to enter phone/code again.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os

from dotenv import load_dotenv

load_dotenv()

try:
    from pyrogram import Client
except ImportError:
    print("❌ Pyrogram not installed. Run: pip install pyrogram")
    sys.exit(1)


async def initialize_session():
    """Initialize Pyrogram session."""
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("❌ TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        sys.exit(1)

    print("🔐 Initializing Pyrogram session...")
    print(f"API ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    print("\n📱 You will be prompted to:")
    print("   1. Enter your phone number (with country code, e.g., +79991234567)")
    print("   2. Enter the verification code sent to your Telegram")
    print("   3. Enter password if you have 2FA enabled")
    print("\n💾 Session will be saved to: telegram_channel_reader.session")
    print("   (You won't need to enter credentials again)\n")

    client = Client("telegram_channel_reader", api_id=int(api_id), api_hash=api_hash)

    try:
        await client.start()
        print("\n✅ Successfully authenticated!")
        print("✅ Session saved. You can now use Pyrogram to fetch channel posts.")

        # Test: get your own info
        me = await client.get_me()
        print(
            f"\n👤 Logged in as: {me.first_name} (@{me.username if me.username else 'no username'})"
        )

    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if client.is_connected:
            await client.stop()


if __name__ == "__main__":
    asyncio.run(initialize_session())
