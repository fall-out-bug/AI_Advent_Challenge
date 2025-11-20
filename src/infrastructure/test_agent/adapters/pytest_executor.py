"""Pytest executor adapter for test execution."""

import subprocess
from pathlib import Path
from typing import List

from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.domain.test_agent.interfaces.test_executor import ITestExecutor


class TestExecutor:
    """
    Pytest executor adapter implementing ITestExecutor.

    Purpose:
        Executes pytest tests and collects results, returning domain entities.

    Example:
        >>> executor = TestExecutor()
        >>> result = executor.execute("tests/test_example.py")
        >>> result.status
        <TestStatus.PASSED: 'passed'>
    """

    def execute(self, test_file_path: str) -> TestResult:
        """Execute tests and return results.

        Args:
            test_file_path: Path to the test file to execute.

        Returns:
            TestResult domain entity with execution results.

        Raises:
            FileNotFoundError: If test file does not exist.
            Exception: If test execution fails unexpectedly.
        """
        path = Path(test_file_path)
        if not path.exists():
            raise FileNotFoundError(f"Test file not found: {test_file_path}")

        try:
            result = subprocess.run(
                ["pytest", str(path), "-v", "--tb=long", "--capture=no"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Combine stdout and stderr for better error parsing
            combined_output = result.stdout
            if result.stderr:
                combined_output += "\n" + result.stderr

            # For debugging: if return code is non-zero, log full output
            import os

            if result.returncode != 0 and os.getenv("TEST_AGENT_DEBUG_OUTPUT"):
                debug_output_path = Path("/tmp/pytest_debug_output.txt")
                try:
                    debug_output_path.write_text(
                        f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nRETURNCODE: {result.returncode}"
                    )
                except Exception:
                    pass

            return self._parse_pytest_output(
                combined_output, result.stderr, result.returncode
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                status=TestStatus.ERROR,
                test_count=0,
                passed_count=0,
                failed_count=0,
                errors=["Test execution timeout (60s)"],
            )
        except Exception as e:
            return TestResult(
                status=TestStatus.ERROR,
                test_count=0,
                passed_count=0,
                failed_count=0,
                errors=[str(e)],
            )

    def get_coverage(self, test_file_path: str) -> float:
        """Get test coverage percentage.

        Args:
            test_file_path: Path to the test file.

        Returns:
            Coverage percentage as float (0.0-100.0).

        Raises:
            FileNotFoundError: If test file does not exist.
        """
        path = Path(test_file_path)
        if not path.exists():
            raise FileNotFoundError(f"Test file not found: {test_file_path}")

        try:
            result = subprocess.run(
                [
                    "pytest",
                    str(path),
                    "--cov",
                    "--cov-report=term-missing",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return self._parse_coverage_output(result.stdout)
        except Exception:
            return 0.0

    def _parse_pytest_output(
        self, stdout: str, stderr: str, returncode: int
    ) -> TestResult:
        """Parse pytest output into TestResult.

        Args:
            stdout: Standard output from pytest.
            stderr: Standard error from pytest.
            returncode: Exit code from pytest.

        Returns:
            TestResult domain entity.
        """
        lines = stdout.split("\n")
        test_count = 0
        passed_count = 0
        failed_count = 0
        errors: List[str] = []
        in_error_section = False
        error_section: List[str] = []

        # Parse stdout for test results and errors
        for i, line in enumerate(lines):
            if "PASSED" in line:
                passed_count += 1
                test_count += 1
                in_error_section = False
            elif "FAILED" in line:
                failed_count += 1
                test_count += 1
                errors.append(line.strip())
                in_error_section = False
            elif "ERROR" in line:
                in_error_section = True
                error_section = [line.strip()]
                # Collect error details from following lines
                for j in range(i + 1, min(i + 20, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if next_line.startswith("=") and len(error_section) > 1:
                        # End of error section
                        break
                    if (
                        "collected" in next_line.lower()
                        or "passed" in next_line.lower()
                    ):
                        break
                    error_section.append(next_line)
                if error_section:
                    errors.append("\n".join(error_section[:10]))  # First 10 lines
                    error_section = []

        # Add stderr errors (syntax errors, import errors, etc.)
        if stderr:
            stderr_lines = stderr.strip().split("\n")
            for line in stderr_lines:
                if line.strip() and (
                    "Error" in line
                    or "SyntaxError" in line
                    or "ImportError" in line
                    or "NameError" in line
                    or "IndentationError" in line
                    or "TypeError" in line
                ):
                    errors.append(line.strip())

        # Extract detailed error information from stdout
        if returncode != 0:
            # Look for error traceback or detailed messages
            error_started = False
            error_details: List[str] = []
            for i, line in enumerate(lines):
                if (
                    "ERROR" in line
                    or "FAILED" in line
                    or "Error" in line
                    or "SyntaxError" in line
                    or "NameError" in line
                    or "ImportError" in line
                ):
                    error_started = True
                    error_details = [line.strip()]
                    # Collect next 20 lines for context
                    for j in range(i + 1, min(i + 21, len(lines))):
                        next_line = lines[j].strip()
                        if next_line:
                            error_details.append(next_line)
                        # Stop at separator lines if we have enough context
                        if next_line.startswith("=") and len(error_details) > 3:
                            break
                    if error_details and "\n".join(error_details) not in errors:
                        errors.append("\n".join(error_details[:20]))

            # If still no errors, include last 30 lines of output
            if not errors and len(lines) > 0:
                errors.append("\n".join(lines[-30:]))

        if stderr and ("SyntaxError" in stderr or "IndentationError" in stderr):
            return TestResult(
                status=TestStatus.ERROR,
                test_count=test_count,
                passed_count=passed_count,
                failed_count=failed_count,
                errors=errors if errors else [stderr.strip()],
            )

        if returncode == 0:
            status = TestStatus.PASSED
        elif failed_count > 0 or in_error_section:
            status = TestStatus.FAILED
        else:
            status = TestStatus.ERROR

        # If no specific errors found but return code is non-zero, include full output
        if not errors and returncode != 0:
            # Extract relevant error lines from stdout
            for line in lines:
                if any(
                    keyword in line
                    for keyword in [
                        "ERROR",
                        "Error",
                        "SyntaxError",
                        "ImportError",
                        "NameError",
                        "FAILED",
                        "Traceback",
                    ]
                ):
                    errors.append(line.strip())
            # If still no errors, include last 50 lines of output for debugging
            if not errors:
                errors.append("Test execution failed - last 50 lines of output:")
                errors.extend(lines[-50:])
            elif len(errors) < 5:
                # Add more context around errors
                for i, line in enumerate(lines):
                    if any(
                        keyword in line for keyword in ["ERROR", "Error", "Traceback"]
                    ):
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 15)
                        context = "\n".join(lines[context_start:context_end])
                        if context not in errors:
                            errors.append(context)
                            break

        # If we have collection errors and no detailed errors, include full error section
        if returncode != 0 and (not errors or len(errors) < 3):
            # Find ERROR collecting section and extract it
            in_error_block = False
            error_block: List[str] = []
            for i, line in enumerate(lines):
                if "ERROR collecting" in line or (
                    "ERROR" in line and "collecting" in line.lower()
                ):
                    in_error_block = True
                    error_block = [line]
                    # Collect next 50 lines for full context
                    for j in range(i + 1, min(i + 51, len(lines))):
                        error_block.append(lines[j])
                        # Stop at separator but keep some context
                        if lines[j].strip().startswith("=") and len(error_block) > 10:
                            break
                    if error_block:
                        errors.append("\n".join(error_block[:50]))
                        break

            # If still no detailed errors, include all lines with ERROR/Error/Traceback
            if not errors or (
                len(errors) == 1 and "ERROR" in errors[0] and len(errors[0]) < 200
            ):
                all_error_lines = [
                    line
                    for line in lines
                    if any(
                        keyword in line
                        for keyword in [
                            "ERROR",
                            "Error",
                            "Traceback",
                            "SyntaxError",
                            "NameError",
                            "ImportError",
                            "IndentationError",
                        ]
                    )
                ]
                if all_error_lines:
                    errors.extend(all_error_lines[:20])
                # Last resort: include last 100 lines
                if len(errors) < 5:
                    errors.append("Full output (last 100 lines):")
                    errors.extend(lines[-100:])

        # Only add "Unknown error" if tests failed but no specific errors were found
        # If tests passed (returncode == 0), errors list should be empty
        final_errors = errors[:20] if errors else []
        if not final_errors and returncode != 0 and status != TestStatus.PASSED:
            final_errors = ["Unknown error during test execution"]

        return TestResult(
            status=status,
            test_count=test_count,
            passed_count=passed_count,
            failed_count=failed_count,
            errors=final_errors,
        )

    def _parse_coverage_output(self, stdout: str) -> float:
        """Parse coverage output to extract percentage.

        Args:
            stdout: Standard output from pytest with coverage.

        Returns:
            Coverage percentage as float.
        """
        lines = stdout.split("\n")
        for line in lines:
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        try:
                            return float(part.replace("%", ""))
                        except ValueError:
                            continue
        return 0.0
