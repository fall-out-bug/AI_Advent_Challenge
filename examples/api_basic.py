#!/usr/bin/env python
"""Basic API usage examples.

This script demonstrates common API operations.
"""

import httpx


def main():
    """Run basic API examples."""
    print("=" * 60)
    print("AI Challenge API - Basic Usage Examples")
    print("=" * 60)
    print()

    base_url = "http://localhost:8000"

    # Health check
    print("1. Health Check")
    print("-" * 60)
    print(f"GET {base_url}/health/")
    print()
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
    print(f"GET {base_url}/health/ready")
    print()
    try:
        response = httpx.get(f"{base_url}/health/ready")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Overall: {data.get('overall')}")
        for check, details in data.get('checks', {}).items():
            print(f"  {check}: {details.get('status')}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Metrics
    print("3. Metrics Dashboard")
    print("-" * 60)
    print(f"GET {base_url}/dashboard/")
    print(f"View in browser: {base_url}/dashboard/")
    print()

    # Dashboard data
    print("4. Dashboard Data")
    print("-" * 60)
    print(f"GET {base_url}/dashboard/data")
    print()
    try:
        response = httpx.get(f"{base_url}/dashboard/data")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Request Count: {data.get('request_count', 0)}")
        print(f"Success Rate: {data.get('success_rate', 0):.2%}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    print("=" * 60)
    print("For more examples, see examples/ directory")
    print("=" * 60)


if __name__ == "__main__":
    main()

