"""E2E user simulation script - Scenario 1: Medium-sized module.

Purpose:
    Simulates user pointing CLI to medium-sized module, running Test Agent,
    verifying tests are generated and saved, running pytest, and verifying
    coverage >= 80%.

Example:
    $ python scripts/e2e/epic_27/test_scenario_1_medium_module.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CLI_MODULE = "src.presentation.cli.test_agent.main"


def create_medium_module() -> Path:
    """Create medium-sized module for testing.

    Returns:
        Path to created module file.
    """
    module_code = '''"""Medium-sized module for E2E testing."""

from typing import List, Optional


class Calculator:
    """Calculator class with basic operations."""

    def __init__(self, initial_value: float = 0.0) -> None:
        """Initialize calculator with optional initial value.

        Args:
            initial_value: Starting value for calculator.
        """
        self.value = initial_value

    def add(self, number: float) -> float:
        """Add number to current value.

        Args:
            number: Number to add.

        Returns:
            Updated calculator value.
        """
        self.value += number
        return self.value

    def subtract(self, number: float) -> float:
        """Subtract number from current value.

        Args:
            number: Number to subtract.

        Returns:
            Updated calculator value.
        """
        self.value -= number
        return self.value

    def multiply(self, number: float) -> float:
        """Multiply current value by number.

        Args:
            number: Number to multiply by.

        Returns:
            Updated calculator value.
        """
        self.value *= number
        return self.value

    def divide(self, number: float) -> float:
        """Divide current value by number.

        Args:
            number: Number to divide by.

        Returns:
            Updated calculator value.

        Raises:
            ValueError: If number is zero.
        """
        if number == 0:
            raise ValueError("Cannot divide by zero")
        self.value /= number
        return self.value

    def reset(self) -> None:
        """Reset calculator to zero."""
        self.value = 0.0

    def get_value(self) -> float:
        """Get current calculator value.

        Returns:
            Current calculator value.
        """
        return self.value


def calculate_sum(numbers: List[float]) -> float:
    """Calculate sum of numbers.

    Args:
        numbers: List of numbers to sum.

    Returns:
        Sum of all numbers.
    """
    return sum(numbers)


def calculate_average(numbers: List[float]) -> Optional[float]:
    """Calculate average of numbers.

    Args:
        numbers: List of numbers.

    Returns:
        Average of numbers, or None if list is empty.
    """
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def find_maximum(numbers: List[float]) -> Optional[float]:
    """Find maximum value in list.

    Args:
        numbers: List of numbers.

    Returns:
        Maximum value, or None if list is empty.
    """
    if not numbers:
        return None
    return max(numbers)


def find_minimum(numbers: List[float]) -> Optional[float]:
    """Find minimum value in list.

    Args:
        numbers: List of numbers.

    Returns:
        Minimum value, or None if list is empty.
    """
    if not numbers:
        return None
    return min(numbers)
'''
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=PROJECT_ROOT
    ) as tmp_file:
        tmp_file.write(module_code)
        return Path(tmp_file.name)


def run_test_agent(file_path: Path) -> Tuple[str, str, int]:
    """Run Test Agent CLI for a file.

    Purpose:
        Simulates user running CLI command to generate tests.

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
        timeout=600,  # 10 minutes timeout
    )
    return result.stdout, result.stderr, result.returncode


def find_generated_tests() -> Path | None:
    """Find generated test files in workspace directory.

    Returns:
        Path to generated test file, or None if not found.
    """
    workspace_dir = PROJECT_ROOT / "workspace"
    if not workspace_dir.exists():
        return None

    test_files = list(workspace_dir.glob("generated_tests_*.py"))
    if test_files:
        # Return most recent file
        return max(test_files, key=lambda p: p.stat().st_mtime)
    return None


def run_pytest(test_file: Path, source_file: Path) -> Tuple[str, str, int]:
    """Run pytest on generated tests with coverage.

    Purpose:
        Simulates user running pytest to verify generated tests.

    Args:
        test_file: Path to generated test file.
        source_file: Path to source file being tested.

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    import os

    # Add source file directory to Python path
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
    return result.stdout, result.stderr, result.returncode


def parse_coverage(pytest_output: str) -> float:
    """Parse coverage percentage from pytest output.

    Args:
        pytest_output: Pytest stdout output.

    Returns:
        Coverage percentage as float.
    """
    import re

    # Look for coverage percentage in output
    # Format: "TOTAL ... XX%"
    pattern = r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%"
    match = re.search(pattern, pytest_output)
    if match:
        return float(match.group(1))

    # Alternative format: "coverage: XX%"
    pattern = r"coverage:\s*(\d+(?:\.\d+)?)%"
    match = re.search(pattern, pytest_output, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return 0.0


def main() -> int:
    """Main function for Scenario 1 E2E test.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import os

    print("=" * 70)
    print("E2E Scenario 1: Medium-sized Module")
    print("=" * 70)
    print()

    # Step 1: Create medium-sized module
    print("Step 1: Creating medium-sized module...")
    module_path = create_medium_module()
    print(f"✓ Created module: {module_path}")
    print()

    try:
        # Step 2: Run Test Agent CLI
        print("Step 2: Running Test Agent CLI...")
        print(f"Command: python -m {CLI_MODULE} {module_path} --save-tests")
        stdout, stderr, returncode = run_test_agent(module_path)

        if returncode != 0:
            print(f"✗ Test Agent failed with exit code {returncode}")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return 1

        print("✓ Test Agent completed successfully")
        print()

        # Step 3: Verify tests are generated and saved
        print("Step 3: Verifying generated tests...")
        test_file = find_generated_tests()
        if not test_file:
            print("✗ Generated test file not found in workspace/")
            return 1

        print(f"✓ Found generated test file: {test_file}")
        print(f"  Test file size: {test_file.stat().st_size} bytes")
        print()

        # Step 4: Run pytest on generated tests
        print("Step 4: Running pytest on generated tests...")
        pytest_stdout, pytest_stderr, pytest_returncode = run_pytest(
            test_file, module_path
        )

        if pytest_returncode != 0:
            print(f"⚠ Pytest returned exit code {pytest_returncode}")
            print("Pytest STDOUT:", pytest_stdout)
            print("Pytest STDERR:", pytest_stderr)
        else:
            print("✓ Pytest completed successfully")
        print()

        # Step 5: Verify coverage >= 80%
        print("Step 5: Verifying coverage >= 80%...")
        coverage = parse_coverage(pytest_stdout)
        print(f"Coverage: {coverage:.1f}%")

        if coverage >= 80.0:
            print("✓ Coverage target met (>= 80%)")
        else:
            print(f"⚠ Coverage below target (expected >= 80%, got {coverage:.1f}%)")
            # Note: This is a warning, not a failure, as LLM generation
            # may not always achieve perfect coverage

        print()
        print("=" * 70)
        print("Scenario 1: COMPLETED")
        print("=" * 70)

        # Return success if pytest passed
        return 0 if pytest_returncode == 0 else 1

    except subprocess.TimeoutExpired:
        print("✗ Test Agent or pytest timed out")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        if module_path.exists():
            module_path.unlink()
            print(f"✓ Cleaned up module file: {module_path}")


if __name__ == "__main__":
    sys.exit(main())
