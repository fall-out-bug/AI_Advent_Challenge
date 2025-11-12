#!/usr/bin/env python
"""Check coverage thresholds and generate report.

Usage:
    python -m scripts.quality.check_coverage --threshold 80
    python -m scripts.quality.check_coverage --html
"""

import argparse
import sys
from pathlib import Path

import pytest


def check_coverage(threshold: int, html: bool = False) -> bool:
    """Check test coverage.

    Args:
        threshold: Minimum coverage threshold (0-100)
        html: Generate HTML coverage report

    Returns:
        True if coverage meets threshold
    """
    print("📊 Checking Test Coverage")
    print(f"   Target threshold: {threshold}%")
    print()

    # Run pytest with coverage
    pytest_args = [
        "src/tests",
        "--cov=src",
        "--cov-report=term",
        f"--cov-fail-under={threshold}",
        "-v",
    ]

    if html:
        pytest_args.append("--cov-report=html")
        print("   Generating HTML report...")

    exit_code = pytest.main(pytest_args)

    if html:
        html_path = Path("htmlcov/index.html")
        if html_path.exists():
            print(f"\n✅ HTML coverage report: {html_path.absolute()}")

    return exit_code == 0


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check test coverage")
    parser.add_argument(
        "--threshold",
        type=int,
        default=75,
        help="Minimum coverage threshold (default: 75)"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    args = parser.parse_args()

    success = check_coverage(args.threshold, args.html)

    if not success:
        print("\n❌ Coverage check failed")
        sys.exit(1)

    print("\n✅ Coverage check passed")


if __name__ == "__main__":
    main()
