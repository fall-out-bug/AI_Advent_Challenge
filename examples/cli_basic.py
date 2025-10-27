#!/usr/bin/env python
"""Basic CLI usage examples.

This script demonstrates common CLI operations.
"""

import asyncio

from src.presentation.cli.main_cli import main


async def main_example():
    """Run basic CLI example."""
    print("=" * 60)
    print("AI Challenge CLI - Basic Usage Examples")
    print("=" * 60)
    print()

    # Status check
    print("1. Checking system status...")
    print("   Run: python -m src.presentation.cli.main_cli status")
    print()

    # Health check
    print("2. Running health checks...")
    print("   Run: python -m src.presentation.cli.main_cli health")
    print()

    # Metrics
    print("3. Viewing metrics...")
    print("   Run: python -m src.presentation.cli.main_cli metrics")
    print()

    # Config
    print("4. Viewing configuration...")
    print("   Run: python -m src.presentation.cli.main_cli config")
    print()

    print("=" * 60)
    print("For more examples, see examples/ directory")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main_example())

