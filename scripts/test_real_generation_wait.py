#!/usr/bin/env python3
"""Test real test generation - waits for LLM to be ready.

Purpose:
    Waits for LLM service to be ready, then tests real test generation.

Usage:
    LLM_URL=http://localhost:8000 python scripts/test_real_generation_wait.py [module_path]
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.clients.llm_client import get_llm_client


async def wait_for_llm(max_wait: int = 300) -> bool:
    """Wait for LLM service to be ready.

    Args:
        max_wait: Maximum seconds to wait.

    Returns:
        True if service is ready, False otherwise.
    """
    print("Waiting for LLM service to be ready...")
    print(f"(This may take up to {max_wait} seconds while model loads)")

    start_time = time.time()
    attempt = 0

    while time.time() - start_time < max_wait:
        attempt += 1
        try:
            client = get_llm_client(timeout=5.0)
            result = await client.generate("test", max_tokens=5)
            elapsed = time.time() - start_time
            print(f"\n✓ LLM service is ready! (waited {elapsed:.1f}s)")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            if attempt % 10 == 0:  # Print every 10 attempts
                print(f"  Attempt {attempt}: still waiting... ({elapsed:.0f}s elapsed)")
            await asyncio.sleep(2)

    print(f"\n❌ LLM service not ready after {max_wait}s")
    return False


async def main() -> None:
    """Main function."""
    if not await wait_for_llm():
        print("\nPlease ensure LLM service is running:")
        print("  docker ps | grep llm-api")
        print("  docker logs llm-api-gigachat --tail 20")
        sys.exit(1)

    # Import and run the actual test
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "test_real_generation", project_root / "scripts" / "test_real_generation.py"
    )
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)

    module_path = None
    if len(sys.argv) > 1:
        module_path = Path(sys.argv[1])
        if not module_path.exists():
            print(f"❌ Module not found: {module_path}")
            sys.exit(1)

    await test_module.test_real_generation(module_path)


if __name__ == "__main__":
    asyncio.run(main())
