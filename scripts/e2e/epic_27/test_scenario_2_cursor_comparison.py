"""E2E user simulation script - Scenario 2: Comparison with Cursor-agent tests.

Purpose:
    Simulates user selecting module with existing Cursor-agent tests,
    running local Test Agent on same module, running pytest for both
    test sets, and comparing coverage reports.

Example:
    $ python scripts/e2e/epic_27/test_scenario_2_cursor_comparison.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CLI_MODULE = "src.presentation.cli.test_agent.main"


def find_module_with_cursor_tests() -> Optional[Tuple[Path, Path]]:
    """Find module with existing Cursor-agent tests.

    Returns:
        Tuple of (module_path, cursor_test_path) if found, None otherwise.
    """
    # Look for common patterns:
    # - tests/ directory with test files
    # - test_*.py files that might be Cursor-generated
    tests_dir = PROJECT_ROOT / "tests"
    if not tests_dir.exists():
        return None

    # Look for test files that might be Cursor-generated
    # (This is a heuristic - in real scenario, user would specify)
    for test_file in tests_dir.rglob("test_*.py"):
        # Try to find corresponding source file
        # Pattern: test_<module_name>.py -> <module_name>.py
        test_name = test_file.stem.replace("test_", "")
        possible_sources = [
            PROJECT_ROOT / "src" / f"{test_name}.py",
            PROJECT_ROOT
            / "src"
            / test_file.parent.relative_to(tests_dir)
            / f"{test_name}.py",
        ]

        for source_path in possible_sources:
            if source_path.exists():
                return (source_path, test_file)

    return None


def create_test_module_with_cursor_tests() -> Tuple[Path, Path]:
    """Create test module with simulated Cursor-agent tests.

    Returns:
        Tuple of (module_path, cursor_test_path).
    """
    module_code = '''"""Module for Cursor comparison testing."""

def calculate_factorial(n: int) -> int:
    """Calculate factorial of n.

    Args:
        n: Non-negative integer.

    Returns:
        Factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * calculate_factorial(n - 1)


def calculate_fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number.

    Args:
        n: Non-negative integer.

    Returns:
        Nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n == 0:
        return 0
    if n == 1:
        return 1
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


def is_prime(n: int) -> bool:
    """Check if number is prime.

    Args:
        n: Positive integer.

    Returns:
        True if n is prime, False otherwise.

    Raises:
        ValueError: If n is not positive.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True
'''

    cursor_test_code = '''"""Cursor-agent generated tests (simulated)."""

import pytest

from src.example_module import calculate_factorial, calculate_fibonacci, is_prime


def test_calculate_factorial_zero():
    """Test factorial of zero."""
    assert calculate_factorial(0) == 1


def test_calculate_factorial_one():
    """Test factorial of one."""
    assert calculate_factorial(1) == 1


def test_calculate_factorial_positive():
    """Test factorial of positive number."""
    assert calculate_factorial(5) == 120


def test_calculate_factorial_negative():
    """Test factorial of negative number raises error."""
    with pytest.raises(ValueError):
        calculate_factorial(-1)


def test_calculate_fibonacci_zero():
    """Test Fibonacci of zero."""
    assert calculate_fibonacci(0) == 0


def test_calculate_fibonacci_one():
    """Test Fibonacci of one."""
    assert calculate_fibonacci(1) == 1


def test_calculate_fibonacci_positive():
    """Test Fibonacci of positive number."""
    assert calculate_fibonacci(5) == 5


def test_is_prime_two():
    """Test is_prime with two."""
    assert is_prime(2) is True


def test_is_prime_composite():
    """Test is_prime with composite number."""
    assert is_prime(4) is False


def test_is_prime_large():
    """Test is_prime with large prime."""
    assert is_prime(17) is True
'''

    # Create module in src/
    src_dir = PROJECT_ROOT / "src"
    src_dir.mkdir(exist_ok=True)
    module_path = src_dir / "example_module.py"
    module_path.write_text(module_code)

    # Create Cursor test file
    tests_dir = PROJECT_ROOT / "tests" / "cursor_tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    cursor_test_path = tests_dir / "test_example_module.py"
    cursor_test_path.write_text(cursor_test_code)

    return module_path, cursor_test_path


def run_test_agent(file_path: Path) -> Tuple[str, str, int]:
    """Run Test Agent CLI for a file.

    Args:
        file_path: Path to Python file to test.

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    cmd = [
        sys.executable,
        "-m",
        CLI_MODULE,
        str(file_path),
        "--save-tests",
    ]
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return result.stdout, result.stderr, result.returncode


def find_generated_tests() -> Optional[Path]:
    """Find generated test files in workspace directory.

    Returns:
        Path to generated test file, or None if not found.
    """
    workspace_dir = PROJECT_ROOT / "workspace"
    if not workspace_dir.exists():
        return None

    test_files = list(workspace_dir.glob("generated_tests_*.py"))
    if test_files:
        return max(test_files, key=lambda p: p.stat().st_mtime)
    return None


def run_pytest_with_coverage(
    test_file: Path, source_file: Path
) -> Tuple[str, str, int, float]:
    """Run pytest on tests with coverage.

    Args:
        test_file: Path to test file.
        source_file: Path to source file being tested.

    Returns:
        Tuple of (stdout, stderr, returncode, coverage).
    """
    import os
    import re

    source_dir = source_file.parent
    env = dict(os.environ)
    pythonpath = env.get("PYTHONPATH", "")
    if pythonpath:
        env["PYTHONPATH"] = f"{source_dir}:{pythonpath}"
    else:
        env["PYTHONPATH"] = str(source_dir)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        f"--cov={source_file.parent}",
        f"--cov={source_file.name}",
        "--cov-report=term",
        "-v",
    ]
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )

    # Parse coverage
    coverage = 0.0
    pattern = r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%"
    match = re.search(pattern, result.stdout)
    if match:
        coverage = float(match.group(1))
    else:
        pattern = r"coverage:\s*(\d+(?:\.\d+)?)%"
        match = re.search(pattern, result.stdout, re.IGNORECASE)
        if match:
            coverage = float(match.group(1))

    return result.stdout, result.stderr, result.returncode, coverage


def compare_coverage(local_coverage: float, cursor_coverage: float) -> Tuple[bool, str]:
    """Compare coverage between local and Cursor tests.

    Args:
        local_coverage: Coverage from local Test Agent.
        cursor_coverage: Coverage from Cursor-agent tests.

    Returns:
        Tuple of (is_comparable, message).
    """
    diff = abs(local_coverage - cursor_coverage)
    threshold = 20.0  # 20% difference is acceptable

    if diff <= threshold:
        return (
            True,
            f"Coverage is comparable (diff: {diff:.1f}%, threshold: {threshold}%)",
        )
    else:
        return (
            False,
            f"Coverage difference is large (diff: {diff:.1f}%, threshold: {threshold}%)",
        )


def main() -> int:
    """Main function for Scenario 2 E2E test.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("=" * 70)
    print("E2E Scenario 2: Comparison with Cursor-agent Tests")
    print("=" * 70)
    print()

    # Step 1: Find or create module with Cursor tests
    print("Step 1: Finding module with Cursor-agent tests...")
    result = find_module_with_cursor_tests()
    if result is None:
        print("  No existing Cursor tests found, creating test module...")
        module_path, cursor_test_path = create_test_module_with_cursor_tests()
        print(f"✓ Created module: {module_path}")
        print(f"✓ Created Cursor test file: {cursor_test_path}")
    else:
        module_path, cursor_test_path = result
        print(f"✓ Found module: {module_path}")
        print(f"✓ Found Cursor test file: {cursor_test_path}")
    print()

    try:
        # Step 2: Run Cursor tests and get coverage
        print("Step 2: Running Cursor-agent tests...")
        (
            cursor_stdout,
            cursor_stderr,
            cursor_returncode,
            cursor_coverage,
        ) = run_pytest_with_coverage(cursor_test_path, module_path)

        if cursor_returncode == 0:
            print(f"✓ Cursor tests passed")
        else:
            print(f"⚠ Cursor tests returned exit code {cursor_returncode}")

        print(f"  Cursor coverage: {cursor_coverage:.1f}%")
        print()

        # Step 3: Run local Test Agent
        print("Step 3: Running local Test Agent on same module...")
        print(f"Command: python -m {CLI_MODULE} {module_path} --save-tests")
        stdout, stderr, returncode = run_test_agent(module_path)

        if returncode != 0:
            print(f"✗ Test Agent failed with exit code {returncode}")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return 1

        print("✓ Test Agent completed successfully")
        print()

        # Step 4: Find and run local generated tests
        print("Step 4: Running local Test Agent generated tests...")
        local_test_file = find_generated_tests()
        if not local_test_file:
            print("✗ Generated test file not found")
            return 1

        print(f"✓ Found generated test file: {local_test_file}")
        (
            local_stdout,
            local_stderr,
            local_returncode,
            local_coverage,
        ) = run_pytest_with_coverage(local_test_file, module_path)

        if local_returncode == 0:
            print(f"✓ Local tests passed")
        else:
            print(f"⚠ Local tests returned exit code {local_returncode}")

        print(f"  Local coverage: {local_coverage:.1f}%")
        print()

        # Step 5: Compare coverage
        print("Step 5: Comparing coverage...")
        print(f"  Cursor-agent coverage: {cursor_coverage:.1f}%")
        print(f"  Local Test Agent coverage: {local_coverage:.1f}%")
        print(f"  Difference: {abs(local_coverage - cursor_coverage):.1f}%")

        is_comparable, message = compare_coverage(local_coverage, cursor_coverage)
        if is_comparable:
            print(f"✓ {message}")
        else:
            print(f"⚠ {message}")
            # Note: This is a warning, not a failure, as coverage may vary

        print()
        print("=" * 70)
        print("Scenario 2: COMPLETED")
        print("=" * 70)

        # Return success if both test suites passed
        return 0 if (cursor_returncode == 0 and local_returncode == 0) else 1

    except subprocess.TimeoutExpired:
        print("✗ Test execution timed out")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup created files
        if module_path.exists() and "example_module" in str(module_path):
            module_path.unlink()
        if cursor_test_path.exists() and "cursor_tests" in str(cursor_test_path):
            cursor_test_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
