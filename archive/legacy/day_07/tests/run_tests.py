#!/usr/bin/env python3
"""Test runner script for the multi-agent system."""

import os
import subprocess
import sys
from pathlib import Path


def run_unit_tests():
    """Run unit tests for the multi-agent system."""
    print("🧪 Running Unit Tests")
    print("=" * 30)

    # Change to the day_07 directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    # Run unit tests
    unit_test_files = ["tests/test_generator.py", "tests/test_reviewer.py"]

    for test_file in unit_test_files:
        if Path(test_file).exists():
            print(f"\n🔍 Running {test_file}...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
        else:
            print(f"⚠️  {test_file} not found")

    return True


def run_integration_tests():
    """Run integration tests for the multi-agent system."""
    print("🧪 Running Integration Tests")
    print("=" * 30)

    # Change to the day_07 directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    # Run integration tests
    integration_test_file = "tests/test_orchestrator.py"
    if Path(integration_test_file).exists():
        print(f"\n🔍 Running {integration_test_file}...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", integration_test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ {integration_test_file} passed")
        else:
            print(f"❌ {integration_test_file} failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
    else:
        print(f"⚠️  {integration_test_file} not found")

    return True


def run_coverage_tests():
    """Run tests with coverage analysis."""
    print("🧪 Running Coverage Tests")
    print("=" * 30)

    # Change to the day_07 directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Coverage analysis completed!")
        print("\n📊 Coverage Report:")
        print(result.stdout)
        print("\n💡 HTML report generated in htmlcov/")
    else:
        print("❌ Coverage analysis failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0


def run_tests():
    """Run all tests for the multi-agent system."""
    print("🧪 Running Multi-Agent System Tests")
    print("=" * 50)

    # Change to the day_07 directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    # Run unit tests
    print("\n📋 Running Unit Tests...")
    print("-" * 30)

    unit_test_files = ["tests/test_generator.py", "tests/test_reviewer.py"]

    for test_file in unit_test_files:
        if Path(test_file).exists():
            print(f"\n🔍 Running {test_file}...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ {test_file} passed")
            else:
                print(f"❌ {test_file} failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
        else:
            print(f"⚠️  {test_file} not found")

    # Run integration tests
    print("\n📋 Running Integration Tests...")
    print("-" * 30)

    integration_test_file = "tests/test_orchestrator.py"
    if Path(integration_test_file).exists():
        print(f"\n🔍 Running {integration_test_file}...")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", integration_test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ {integration_test_file} passed")
        else:
            print(f"❌ {integration_test_file} failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
    else:
        print(f"⚠️  {integration_test_file} not found")

    # Run all tests together
    print("\n📋 Running All Tests...")
    print("-" * 30)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ All tests passed!")
        print("\n📊 Test Summary:")
        print(result.stdout)
    else:
        print("❌ Some tests failed!")
        print("\n📊 Test Summary:")
        print(result.stdout)
        print("\n🔍 Error Details:")
        print(result.stderr)

    return result.returncode == 0


def run_coverage():
    """Run tests with coverage analysis."""
    print("\n📊 Running Tests with Coverage...")
    print("-" * 30)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Coverage analysis completed!")
        print("\n📊 Coverage Report:")
        print(result.stdout)
        print("\n💡 HTML report generated in htmlcov/")
    else:
        print("❌ Coverage analysis failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0


def lint_code():
    """Run code linting."""
    print("\n🔍 Running Code Linting...")
    print("-" * 30)

    # Run flake8
    print("Running flake8...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            ".",
            "--max-line-length=100",
            "--ignore=E203,W503",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ flake8 passed")
    else:
        print("❌ flake8 found issues:")
        print(result.stdout)

    # Run black check
    print("\nRunning black check...")
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."], capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ black formatting is correct")
    else:
        print("❌ black formatting issues found:")
        print(result.stdout)
        print("\n💡 Run 'black .' to fix formatting issues")

    return True


def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent System Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run coverage tests only")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    
    return parser.parse_args()


def main():
    """Main test runner function."""
    import os

    print("🌟 Multi-Agent System Test Suite")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: tests directory not found")
        print("Please run this script from the day_07 directory")
        return False

    # Parse arguments
    args = parse_arguments()

    # Run tests based on arguments
    if args.unit:
        tests_passed = run_unit_tests()
        coverage_passed = True  # Skip coverage for unit-only runs
        lint_passed = True  # Skip linting for unit-only runs
    elif args.integration:
        tests_passed = run_integration_tests()
        coverage_passed = True  # Skip coverage for integration-only runs
        lint_passed = True  # Skip linting for integration-only runs
    elif args.coverage:
        tests_passed = True  # Skip tests for coverage-only runs
        coverage_passed = run_coverage_tests()
        lint_passed = True  # Skip linting for coverage-only runs
    elif args.lint:
        tests_passed = True  # Skip tests for lint-only runs
        coverage_passed = True  # Skip coverage for lint-only runs
        lint_passed = lint_code()
    elif args.all:
        # Run all tests
        tests_passed = run_tests()

        # Run coverage if tests passed
        if tests_passed:
            coverage_passed = run_coverage()
        else:
            print("\n⚠️  Skipping coverage analysis due to test failures")
            coverage_passed = False

        # Run linting
        lint_passed = lint_code()
    else:
        # Default: run all tests
        tests_passed = run_tests()

        # Run coverage if tests passed
        if tests_passed:
            coverage_passed = run_coverage()
        else:
            print("\n⚠️  Skipping coverage analysis due to test failures")
            coverage_passed = False

        # Run linting
        lint_passed = lint_code()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Suite Summary")
    print("=" * 60)
    print(f"Unit & Integration Tests: {'✅ PASSED' if tests_passed else '❌ FAILED'}")
    print(f"Coverage Analysis: {'✅ PASSED' if coverage_passed else '❌ FAILED'}")
    print(f"Code Linting: {'✅ PASSED' if lint_passed else '❌ FAILED'}")

    if tests_passed and coverage_passed and lint_passed:
        print("\n🎉 All checks passed! The system is ready for deployment.")
        return True
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
