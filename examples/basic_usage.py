#!/usr/bin/env python
"""Basic usage examples for API and CLI.

This script demonstrates common API and CLI operations.
"""

import asyncio

import httpx


def demo_api_usage():
    """Demonstrate basic API operations."""
    print("=" * 60)
    print("AI Challenge API - Basic Usage")
    print("=" * 60)
    print()

    base_url = "http://localhost:8000"

    # Health check
    print("1. Health Check")
    print("-" * 60)
    try:
        response = httpx.get(f"{base_url}/health/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Readiness check
    print("2. Readiness Check")
    print("-" * 60)
    try:
        response = httpx.get(f"{base_url}/health/ready")
        data = response.json()
        print(f"Overall: {data.get('overall')}")
        for check, details in data.get("checks", {}).items():
            print(f"  {check}: {details.get('status')}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Metrics
    print("3. View Metrics Dashboard")
    print("-" * 60)
    print(f"Open in browser: {base_url}/dashboard/")
    print()


async def demo_cli_usage():
    """Demonstrate basic CLI operations."""
    print("=" * 60)
    print("AI Challenge CLI - Basic Usage")
    print("=" * 60)
    print()

    print("1. Backoffice CLI Help")
    print("   Run: poetry run python -m src.presentation.cli.backoffice.main --help")
    print()

    print("2. Generate Digest")
    print(
        "   Run: poetry run python -m src.presentation.cli.backoffice.main "
        "digest run --user-id 42 --hours 24"
    )
    print()

    print("3. Export Digest to Markdown")
    print(
        "   Run: poetry run python -m src.presentation.cli.backoffice.main "
        "digest export --user-id 42 --format markdown --output digest.md --overwrite"
    )
    print()


def main():
    """Run all basic examples."""
    demo_api_usage()
    asyncio.run(demo_cli_usage())

    print("=" * 60)
    print("For more examples, see examples/full_workflow.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
