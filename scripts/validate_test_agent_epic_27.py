"""Comprehensive validation script for Epic 27 Test Agent.

Purpose:
    Validates the enhanced Test Agent with various test scenarios
    to ensure it's useful and production-ready.

Example:
    $ python scripts/validate_test_agent_epic_27.py
    $ python scripts/validate_test_agent_epic_27.py --quick
    $ python scripts/validate_test_agent_epic_27.py --module src/domain/test_agent/entities/code_file.py
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
CLI_MODULE = "src.presentation.cli.test_agent.main"


class ValidationResult:
    """Result of a validation test."""

    def __init__(self, name: str) -> None:
        """Initialize validation result.

        Args:
            name: Test name.
        """
        self.name = name
        self.passed = False
        self.coverage = 0.0
        self.test_count = 0
        self.generation_time = 0.0
        self.errors: List[str] = []
        self.warnings: List[str] = []


def run_test_agent(
    module_path: Path, timeout: int = 600
) -> tuple[str, str, int, float]:
    """Run Test Agent on a module.

    Args:
        module_path: Path to module to test.
        timeout: Timeout in seconds.

    Returns:
        Tuple of (stdout, stderr, returncode, elapsed_time).
    """
    start_time = time.time()
    cmd = [
        sys.executable,
        "-m",
        CLI_MODULE,
        str(module_path),
        "--save-tests",
    ]
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.time() - start_time
    return result.stdout, result.stderr, result.returncode, elapsed


def find_generated_tests() -> List[Path]:
    """Find generated test files.

    Returns:
        List of generated test file paths.
    """
    workspace_dir = PROJECT_ROOT / "workspace"
    if not workspace_dir.exists():
        return []
    return list(workspace_dir.glob("generated_tests_*.py"))


def run_pytest_coverage(test_file: Path, source_file: Path) -> tuple[float, int, int]:
    """Run pytest with coverage.

    Args:
        test_file: Path to test file.
        source_file: Path to source file.

    Returns:
        Tuple of (coverage, test_count, passed_count).
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

    # Parse test count
    test_count = 0
    passed_count = 0
    for line in result.stdout.split("\n"):
        if "passed" in line.lower() and "failed" not in line.lower():
            numbers = re.findall(r"\d+", line)
            if numbers:
                passed_count = int(numbers[0])
        if "test" in line.lower() and "passed" in line.lower():
            numbers = re.findall(r"\d+", line)
            if numbers:
                test_count = int(numbers[0])

    return coverage, test_count, passed_count


def validate_small_module(module_path: Path) -> ValidationResult:
    """Validate Test Agent with small module.

    Args:
        module_path: Path to small module.

    Returns:
        ValidationResult.
    """
    result = ValidationResult(f"Small Module: {module_path.name}")

    try:
        # Run Test Agent
        stdout, stderr, returncode, elapsed = run_test_agent(module_path)
        result.generation_time = elapsed

        if returncode != 0:
            result.errors.append(f"Test Agent failed: {stderr}")
            return result

        # Find generated tests
        test_files = find_generated_tests()
        if not test_files:
            result.errors.append("No test files generated")
            return result

        # Run tests with coverage
        coverage, test_count, passed_count = run_pytest_coverage(
            test_files[0], module_path
        )

        result.coverage = coverage
        result.test_count = test_count

        # Validate
        if coverage >= 80.0:
            result.passed = True
        else:
            result.warnings.append(f"Coverage {coverage:.1f}% < 80%")

        if test_count == 0:
            result.errors.append("No tests generated")
            result.passed = False

        if elapsed > 60:
            result.warnings.append(f"Generation took {elapsed:.1f}s (slow)")

    except subprocess.TimeoutExpired:
        result.errors.append("Test Agent timed out")
    except Exception as e:
        result.errors.append(f"Error: {e}")

    return result


def validate_medium_module(module_path: Path) -> ValidationResult:
    """Validate Test Agent with medium module (chunking).

    Args:
        module_path: Path to medium module.

    Returns:
        ValidationResult.
    """
    result = ValidationResult(f"Medium Module (Chunking): {module_path.name}")

    try:
        # Run Test Agent
        stdout, stderr, returncode, elapsed = run_test_agent(module_path)
        result.generation_time = elapsed

        if returncode != 0:
            result.errors.append(f"Test Agent failed: {stderr}")
            return result

        # Check if chunking was used
        if "chunking" not in stdout.lower() and "chunk" not in stdout.lower():
            result.warnings.append("Chunking may not have been used")

        # Find generated tests
        test_files = find_generated_tests()
        if not test_files:
            result.errors.append("No test files generated")
            return result

        # Run tests with coverage
        coverage, test_count, passed_count = run_pytest_coverage(
            test_files[0], module_path
        )

        result.coverage = coverage
        result.test_count = test_count

        # Validate
        if coverage >= 80.0:
            result.passed = True
        else:
            result.warnings.append(f"Coverage {coverage:.1f}% < 80%")

        if "context" in stderr.lower() and "limit" in stderr.lower():
            result.errors.append("Context limit error detected")
            result.passed = False

    except subprocess.TimeoutExpired:
        result.errors.append("Test Agent timed out")
    except Exception as e:
        result.errors.append(f"Error: {e}")

    return result


def find_test_modules() -> Dict[str, List[Path]]:
    """Find modules for testing.

    Returns:
        Dictionary mapping category to list of module paths.
    """
    modules: Dict[str, List[Path]] = {
        "small": [],
        "medium": [],
        "large": [],
    }

    # Find modules in src/
    for py_file in (PROJECT_ROOT / "src").rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            line_count = len(py_file.read_text().split("\n"))
            if line_count < 100:
                modules["small"].append(py_file)
            elif line_count < 500:
                modules["medium"].append(py_file)
            else:
                modules["large"].append(py_file)
        except Exception:
            continue

    return modules


def print_results(results: List[ValidationResult]) -> None:
    """Print validation results.

    Args:
        results: List of validation results.
    """
    print("\n" + "=" * 70)
    print("Validation Results")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for result in results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"\n{status}: {result.name}")
        print(f"  Coverage: {result.coverage:.1f}%")
        print(f"  Tests: {result.test_count}")
        print(f"  Time: {result.generation_time:.1f}s")

        if result.warnings:
            for warning in result.warnings:
                print(f"  ⚠ {warning}")

        if result.errors:
            for error in result.errors:
                print(f"  ✗ {error}")

    print("\n" + "=" * 70)
    print(f"Summary: {passed}/{total} tests passed")
    print("=" * 70)


def main() -> int:
    """Main validation function.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(description="Validate Epic 27 Test Agent")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation (fewer tests)",
    )
    parser.add_argument(
        "--module",
        type=Path,
        help="Test specific module",
    )
    args = parser.parse_args()

    print("Epic 27 Test Agent Validation")
    print("=" * 70)

    results: List[ValidationResult] = []

    if args.module:
        # Test specific module
        if not args.module.exists():
            print(f"Error: Module not found: {args.module}")
            return 1

        line_count = len(args.module.read_text().split("\n"))
        if line_count < 200:
            result = validate_small_module(args.module)
        else:
            result = validate_medium_module(args.module)
        results.append(result)
    else:
        # Find and test modules
        modules = find_test_modules()

        # Test small modules
        if modules["small"]:
            test_module = modules["small"][0]
            result = validate_small_module(test_module)
            results.append(result)

        # Test medium modules
        if modules["medium"]:
            test_module = modules["medium"][0]
            result = validate_medium_module(test_module)
            results.append(result)

        # Test large modules (if not quick mode)
        if not args.quick and modules["large"]:
            test_module = modules["large"][0]
            result = validate_medium_module(test_module)
            results.append(result)

    print_results(results)

    # Return success if all passed
    if all(r.passed for r in results):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
