#!/usr/bin/env python3
"""Test and run script for Day 12 project.

This script provides utilities for testing and running Day 12 features:
- Run unit tests
- Run integration tests
- Start Docker Compose services
- Check service health
- View metrics
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command and return result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def run_tests(test_type: str = "all") -> int:
    """Run tests for Day 12 features.

    Args:
        test_type: Type of tests to run (all, unit, integration, e2e, metrics)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    test_paths = {
        "all": [
            "tests/workers/test_post_fetcher_worker.py",
            "src/tests/presentation/mcp/test_pdf_digest_tools.py",
            "tests/integration/test_pdf_digest_flow.py",
            "src/tests/infrastructure/monitoring/test_prometheus_metrics.py",
        ],
        "unit": [
            "tests/workers/test_post_fetcher_worker.py",
            "src/tests/presentation/mcp/test_pdf_digest_tools.py",
            "src/tests/infrastructure/monitoring/test_prometheus_metrics.py",
        ],
        "integration": [
            "tests/integration/test_pdf_digest_flow.py",
        ],
        "metrics": [
            "src/tests/infrastructure/monitoring/test_prometheus_metrics.py",
        ],
    }

    paths = test_paths.get(test_type, test_paths["all"])

    try:
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + paths
        run_command(cmd)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return e.returncode


def check_services() -> int:
    """Check if Docker Compose services are running.

    Returns:
        Exit code (0 = all healthy, 1 = some unhealthy)
    """
    compose_file = "docker-compose.day12.yml"

    if not Path(compose_file).exists():
        print(f"Error: {compose_file} not found")
        return 1

    try:
        # Check service status
        cmd = ["docker-compose", "-f", compose_file, "ps"]
        result = run_command(cmd, check=False)

        # Check health endpoints
        services = {
            "mcp-server": "http://localhost:8004/health",
            "telegram-bot": None,  # No HTTP endpoint
            "post-fetcher-worker": None,  # No HTTP endpoint
        }

        print("\n=== Service Health Checks ===")
        for service, endpoint in services.items():
            if endpoint:
                try:
                    import httpx
                    response = httpx.get(endpoint, timeout=5)
                    status = "healthy" if response.status_code == 200 else "unhealthy"
                    print(f"{service}: {status} ({endpoint})")
                except Exception as e:
                    print(f"{service}: unreachable ({e})")
            else:
                print(f"{service}: no HTTP endpoint (check logs)")

        return 0
    except Exception as e:
        print(f"Error checking services: {e}")
        return 1


def start_services() -> int:
    """Start Docker Compose services.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    compose_file = "docker-compose.day12.yml"

    if not Path(compose_file).exists():
        print(f"Error: {compose_file} not found")
        return 1

    try:
        # Build images
        print("Building images...")
        cmd = ["docker-compose", "-f", compose_file, "build"]
        run_command(cmd)

        # Start services
        print("\nStarting services...")
        cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
        run_command(cmd)

        # Wait for services to be healthy
        print("\nWaiting for services to be healthy...")
        time.sleep(10)

        # Check status
        return check_services()
    except subprocess.CalledProcessError as e:
        print(f"Failed to start services: {e}")
        return e.returncode


def stop_services() -> int:
    """Stop Docker Compose services.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    compose_file = "docker-compose.day12.yml"

    if not Path(compose_file).exists():
        print(f"Error: {compose_file} not found")
        return 1

    try:
        cmd = ["docker-compose", "-f", compose_file, "down"]
        run_command(cmd)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop services: {e}")
        return e.returncode


def view_metrics() -> int:
    """View Prometheus metrics from MCP server.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        import httpx

        url = "http://localhost:8004/metrics"
        print(f"Fetching metrics from {url}...")

        response = httpx.get(url, timeout=10)

        if response.status_code == 200:
            print("\n=== Prometheus Metrics ===")
            print(response.text)
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
    except ImportError:
        print("Error: httpx not installed. Install with: pip install httpx")
        return 1
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return 1


def view_logs(service: str = None) -> int:
    """View logs from Docker Compose services.

    Args:
        service: Specific service to view logs for (optional)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    compose_file = "docker-compose.day12.yml"

    if not Path(compose_file).exists():
        print(f"Error: {compose_file} not found")
        return 1

    try:
        cmd = ["docker-compose", "-f", compose_file, "logs", "-f"]
        if service:
            cmd.append(service)

        # Run in foreground (will stream logs)
        subprocess.run(cmd)
        return 0
    except KeyboardInterrupt:
        print("\nLogs viewing interrupted")
        return 0
    except Exception as e:
        print(f"Error viewing logs: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test and run Day 12 project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/day12_run.py test --type unit
  python scripts/day12_run.py start
  python scripts/day12_run.py metrics
  python scripts/day12_run.py logs post-fetcher-worker
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "metrics"],
        default="all",
        help="Type of tests to run"
    )

    # Start command
    subparsers.add_parser("start", help="Start Docker Compose services")

    # Stop command
    subparsers.add_parser("stop", help="Stop Docker Compose services")

    # Check command
    subparsers.add_parser("check", help="Check service health")

    # Metrics command
    subparsers.add_parser("metrics", help="View Prometheus metrics")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View service logs")
    logs_parser.add_argument(
        "service",
        nargs="?",
        help="Specific service to view logs for (optional)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "test": lambda: run_tests(args.type if hasattr(args, "type") else "all"),
        "start": start_services,
        "stop": stop_services,
        "check": check_services,
        "metrics": view_metrics,
        "logs": lambda: view_logs(args.service if hasattr(args, "service") else None),
    }

    func = commands.get(args.command)
    if func:
        return func()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
