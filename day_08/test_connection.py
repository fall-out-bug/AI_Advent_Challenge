#!/usr/bin/env python3
"""
Test script to check model connections.
"""

import asyncio
import sys
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient


async def test_connection():
    """Test connection to models."""
    client = UnifiedModelClient()
    
    print("Testing StarCoder connection...")
    try:
        result = await asyncio.wait_for(client.check_availability("starcoder"), timeout=5)
        print(f"StarCoder: {result}")
    except Exception as e:
        print(f"StarCoder error: {e}")
    
    print("Testing Mistral connection...")
    try:
        result = await asyncio.wait_for(client.check_availability("mistral"), timeout=5)
        print(f"Mistral: {result}")
    except Exception as e:
        print(f"Mistral error: {e}")


if __name__ == "__main__":
    asyncio.run(test_connection())
