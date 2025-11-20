"""Verification script for Test Agent production validation.

Purpose:
    Runs Test Agent CLI against all sample files and verifies
    that acceptance criteria are met (test generation, execution, coverage ≥80%).

Example:
    $ python scripts/verify_test_agent.py
"""

import asyncio
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
SAMPLES_DIR = PROJECT_ROOT / "docs" / "specs" / "epic_26" / "test_samples"
CLI_MODULE = "src.presentation.cli.test_agent.main"


@dataclass
class SampleResult:
    """Result for a single sample file.

    Attributes:
        file_name: Name of the sample file.
        file_path: Full path to the sample file.
        status: Test execution status (passed/failed/error).
        test_count: Total number of tests.
        passed_count: Number of passed tests.
        failed_count: Number of failed tests.
        coverage: Coverage percentage.
        errors: List of error messages.
        verification_passed: Whether verification passed (coverage ≥80%).
    """

    file_name: str
    file_path: str
    status: str
    test_count: int
    passed_count: int
    failed_count: int
    coverage: float
    errors: List[str]
    verification_passed: bool


@dataclass
class VerificationReport:
    """Overall verification report.

    Attributes:
        total_samples: Total number of samples processed.
        passed_samples: Number of samples that passed verification.
        failed_samples: Number of samples that failed verification.
        results: List of individual sample results.
        overall_status: Overall status (PASS/FAIL).
    """

    total_samples: int
    passed_samples: int
    failed_samples: int
    results: List[SampleResult]
    overall_status: str


def run_test_agent(file_path: Path) -> tuple[str, str, int]:
    """Run Test Agent CLI for a file.

    Args:
        file_path: Path to the Python file to test.

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    cmd = [sys.executable, "-m", CLI_MODULE, str(file_path)]
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.stdout, result.stderr, result.returncode


def parse_test_result(stdout: str, stderr: str, returncode: int) -> SampleResult:
    """Parse Test Agent CLI output into SampleResult.

    Args:
        stdout: Standard output from CLI.
        stderr: Standard error from CLI.
        returncode: Exit code from CLI.

    Returns:
        SampleResult with parsed data.
    """
    status = "passed" if returncode == 0 else "failed"
    test_count = 0
    passed_count = 0
    failed_count = 0
    coverage = 0.0
    errors: List[str] = []

    # Parse status from output
    stdout_upper = stdout.upper()
    if "TEST STATUS: ERROR" in stdout_upper or "STATUS: ERROR" in stdout_upper:
        status = "error"
    elif "TEST STATUS: FAILED" in stdout_upper or "STATUS: FAILED" in stdout_upper:
        status = "failed"
    elif "TEST STATUS: PASSED" in stdout_upper or "STATUS: PASSED" in stdout_upper:
        status = "passed"
    elif returncode != 0:
        status = "error"

    # Parse test counts
    for line in stdout.split("\n"):
        if "Tests:" in line:
            # Format: "Tests: 5 total, 5 passed, 0 failed"
            # Extract numbers from the line
            # Find all numbers in the line
            numbers = re.findall(r"\d+", line)
            if len(numbers) >= 3:
                test_count = int(numbers[0])
                passed_count = int(numbers[1])
                failed_count = int(numbers[2])
            else:
                # Fallback: parse by keywords
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "total" in part.lower():
                        try:
                            test_count = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif "passed" in part.lower() and "failed" not in part.lower():
                        try:
                            passed_count = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif "failed" in part.lower():
                        try:
                            failed_count = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass

    # Parse coverage
    for line in stdout.split("\n"):
        if "Coverage:" in line:
            try:
                # Format: "Coverage: 85.5%"
                coverage_part = line.split("Coverage:")[1]
                coverage_str = coverage_part.split("%")[0].strip()
                coverage = float(coverage_str)
            except (ValueError, IndexError):
                pass

    # Parse errors
    if "Errors:" in stdout:
        error_section = stdout.split("Errors:")[1]
        for line in error_section.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                error_text = line[1:].strip()
                if error_text:
                    errors.append(error_text)

    if stderr:
        stderr_clean = stderr.strip()
        if stderr_clean:
            errors.append(stderr_clean)

    verification_passed = coverage >= 80.0 and status == "passed"

    return SampleResult(
        file_name="",
        file_path="",
        status=status,
        test_count=test_count,
        passed_count=passed_count,
        failed_count=failed_count,
        coverage=coverage,
        errors=errors,
        verification_passed=verification_passed,
    )


def process_sample(file_path: Path) -> SampleResult:
    """Process a single sample file.

    Args:
        file_path: Path to the sample file.

    Returns:
        SampleResult for the file.
    """
    print(f"Processing: {file_path.name}...")

    try:
        stdout, stderr, returncode = run_test_agent(file_path)
        result = parse_test_result(stdout, stderr, returncode)
        result.file_name = file_path.name
        result.file_path = str(file_path)

        if result.verification_passed:
            print(f"  ✓ PASSED - Coverage: {result.coverage:.1f}%")
        else:
            print(
                f"  ✗ FAILED - Status: {result.status}, Coverage: {result.coverage:.1f}%"
            )
            if result.errors:
                print(f"    Errors: {len(result.errors)}")

        return result
    except subprocess.TimeoutExpired:
        print(f"  ✗ TIMEOUT - Execution exceeded 5 minutes")
        return SampleResult(
            file_name=file_path.name,
            file_path=str(file_path),
            status="error",
            test_count=0,
            passed_count=0,
            failed_count=0,
            coverage=0.0,
            errors=["Execution timeout (5 minutes)"],
            verification_passed=False,
        )
    except Exception as e:
        print(f"  ✗ ERROR - {e}")
        return SampleResult(
            file_name=file_path.name,
            file_path=str(file_path),
            status="error",
            test_count=0,
            passed_count=0,
            failed_count=0,
            coverage=0.0,
            errors=[str(e)],
            verification_passed=False,
        )


def generate_report(results: List[SampleResult]) -> VerificationReport:
    """Generate verification report.

    Args:
        results: List of sample results.

    Returns:
        VerificationReport with summary.
    """
    total = len(results)
    passed = sum(1 for r in results if r.verification_passed)
    failed = total - passed
    overall_status = "PASS" if failed == 0 else "FAIL"

    return VerificationReport(
        total_samples=total,
        passed_samples=passed,
        failed_samples=failed,
        results=results,
        overall_status=overall_status,
    )


def print_report(report: VerificationReport) -> None:
    """Print verification report to console.

    Args:
        report: VerificationReport to print.
    """
    print("\n" + "=" * 60)
    print("Test Agent Verification Report")
    print("=" * 60)
    print(f"\nTotal Samples: {report.total_samples}")
    print(f"Passed: {report.passed_samples}")
    print(f"Failed: {report.failed_samples}")
    print(f"\nOverall Status: {report.overall_status}")

    print("\nDetailed Results:")
    print("-" * 60)
    for result in report.results:
        status_icon = "✓" if result.verification_passed else "✗"
        print(f"{status_icon} {result.file_name}")
        print(f"  Status: {result.status}")
        print(
            f"  Tests: {result.test_count} total, {result.passed_count} passed, {result.failed_count} failed"
        )
        print(f"  Coverage: {result.coverage:.1f}%")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
            for error in result.errors[:3]:
                print(f"    - {error[:80]}")

    print("=" * 60)


def save_json_report(report: VerificationReport, output_path: Path) -> None:
    """Save verification report as JSON.

    Args:
        report: VerificationReport to save.
        output_path: Path to save JSON file.
    """
    report_dict = asdict(report)
    with open(output_path, "w") as f:
        json.dump(report_dict, f, indent=2)


def main() -> int:
    """Main entry point for verification script.

    Returns:
        Exit code: 0 if all samples pass, 1 otherwise.
    """
    if not SAMPLES_DIR.exists():
        print(f"Error: Samples directory not found: {SAMPLES_DIR}")
        return 1

    sample_files = sorted(SAMPLES_DIR.glob("*.py"))
    if not sample_files:
        print(f"Error: No sample files found in {SAMPLES_DIR}")
        return 1

    print(f"Found {len(sample_files)} sample files")
    print(f"Samples directory: {SAMPLES_DIR}\n")

    results: List[SampleResult] = []
    for file_path in sample_files:
        result = process_sample(file_path)
        results.append(result)

    report = generate_report(results)
    print_report(report)

    # Save JSON report
    json_path = PROJECT_ROOT / "docs" / "specs" / "epic_26" / "verification_report.json"
    save_json_report(report, json_path)
    print(f"\nJSON report saved to: {json_path}")

    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
