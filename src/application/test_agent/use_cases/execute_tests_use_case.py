"""Use case for executing tests and collecting results."""

import ast
import os
import re
import tempfile
from pathlib import Path

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestResult
from src.domain.test_agent.interfaces.test_executor import ITestExecutor
from src.domain.test_agent.interfaces.use_cases import IExecuteTestsUseCase
from src.infrastructure.logging import get_logger


class ExecuteTestsUseCase:
    """
    Use case for orchestrating test execution and collecting results.

    Purpose:
        Executes test cases using test executor, collects coverage, and returns
        domain entities with results.

    Example:
        >>> use_case = ExecuteTestsUseCase(test_executor=executor)
        >>> test_cases = [TestCase(name="test_add", code="...")]
        >>> code_file = CodeFile(path="code.py", content="...")
        >>> result = use_case.execute_tests(test_cases, code_file)
        >>> result.status
        <TestStatus.PASSED: 'passed'>
    """

    def __init__(self, test_executor: ITestExecutor) -> None:
        """Initialize use case.

        Args:
            test_executor: Test executor interface for running tests.
        """
        self.test_executor = test_executor
        self.logger = get_logger("test_agent.execute_tests")
        self.debug_enabled = os.getenv("TEST_AGENT_DEBUG_LLM", "").lower() in (
            "1",
            "true",
            "yes",
        )

    def execute_tests(
        self, test_cases: list[TestCase], code_file: CodeFile
    ) -> TestResult:
        """Execute tests and return results.

        Args:
            test_cases: List of TestCase domain entities to execute.
            code_file: CodeFile domain entity with code to test.

        Returns:
            TestResult domain entity with execution results.

        Raises:
            Exception: If test execution fails.
        """
        self.logger.info(
            "Starting test execution",
            extra={
                "source_file": code_file.path,
                "test_cases_count": len(test_cases),
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write test file with source code embedded
            test_file = Path(tmpdir) / "test_generated.py"

            # CRITICAL: Validate and create immutable source code copy
            # This ensures source code is never modified
            try:
                source_ast = ast.parse(code_file.content)
                source_function_names = {
                    node.name
                    for node in ast.walk(source_ast)
                    if isinstance(node, ast.FunctionDef)
                }
                # Create immutable copy of source code
                immutable_source_code = code_file.content
                source_code_hash = hash(immutable_source_code)

                self.logger.debug(
                    "Source code validated",
                    extra={
                        "source_functions": list(source_function_names),
                        "source_lines": len(immutable_source_code.split("\n")),
                        "source_hash": source_code_hash,
                    },
                )
            except SyntaxError as e:
                self.logger.error(
                    f"Source code has syntax errors: {e.msg} at line {e.lineno}"
                )
                raise Exception(
                    f"Source code has syntax errors: {e.msg} at line {e.lineno}"
                ) from e

            # CRITICAL: Build test file with immutable source code section
            # Use strict markers to separate source and test sections
            SOURCE_MARKER_START = "# ===== SOURCE CODE (IMMUTABLE) =====\n"
            SOURCE_MARKER_END = "# ===== END SOURCE CODE =====\n"
            TEST_MARKER_START = "# ===== GENERATED TEST CASES =====\n"

            # Check for typing imports needed in source code
            typing_types = {
                "List": "List",
                "Dict": "Dict",
                "Optional": "Optional",
                "Union": "Union",
                "Tuple": "Tuple",
                "Set": "Set",
                "Callable": "Callable",
                "Any": "Any",
                "Sequence": "Sequence",
                "Iterable": "Iterable",
            }
            used_types = []
            for type_name, pattern in typing_types.items():
                # Check for usage like List[int], Dict[str, int], Optional[int], etc.
                # Also check for: -> List, : List, , List, (List (in type hints)
                # Also check for nested types: List[Dict[...]], Dict[str, List[...]], etc.
                # Check both with and without brackets: Any, Any[, : Any, -> Any
                # Also check with/without spaces: :Any, : Any, ->Any, -> Any
                if (
                    f"{pattern}[" in immutable_source_code
                    or f": {pattern}" in immutable_source_code
                    or f":{pattern}" in immutable_source_code
                    or f"-> {pattern}" in immutable_source_code
                    or f"->{pattern}" in immutable_source_code
                    or f", {pattern}" in immutable_source_code
                    or f",{pattern}" in immutable_source_code
                    or f"({pattern}" in immutable_source_code
                    or f"[{pattern}"
                    in immutable_source_code  # For nested types like List[Dict[...]]
                    or f"{pattern}["
                    in immutable_source_code  # For Dict[...], List[...], etc.
                    or f", {pattern}]"
                    in immutable_source_code  # For Dict[str, Any], List[Dict, ...]
                    or f",{pattern}]"
                    in immutable_source_code  # For Dict[str,Any], List[Dict,...]
                    or f"{pattern}]" in immutable_source_code  # For ...Any], ...Dict]
                    or f"{pattern})"
                    in immutable_source_code  # For function parameters: value: Any)
                    or f"{pattern},"
                    in immutable_source_code  # For function parameters: value: Any,
                ):
                    used_types.append(type_name)

            # Also check for lowercase 'any' which should be 'Any' from typing
            # This is a common mistake - 'any' is a built-in function, not a type
            if "any" in immutable_source_code and "Any" not in used_types:
                # Check if it's used as a type hint (not just in strings/comments)
                # Look for patterns like: : any, -> any, [any, any], Dict[str, any]
                if (
                    ": any" in immutable_source_code
                    or "-> any" in immutable_source_code
                    or "[any" in immutable_source_code
                    or ", any" in immutable_source_code
                    or "Dict[str, any" in immutable_source_code
                    or "Dict[any" in immutable_source_code
                ):
                    used_types.append("Any")

            # Build test file content with imports and immutable source section
            test_content_lines = []

            # Add typing imports if needed
            if used_types:
                # Parse existing imports from source code
                existing_imports = set()

                # Find all "from typing import ..." lines
                typing_import_pattern = r"from\s+typing\s+import\s+([^\n]+)"
                matches = re.findall(typing_import_pattern, immutable_source_code)
                for match in matches:
                    # Split by comma and clean up
                    imported_types = [t.strip() for t in match.split(",") if t.strip()]
                    existing_imports.update(imported_types)

                # Determine which types need to be added
                needed_types = sorted(set(used_types) - existing_imports)

                # Always log for debugging (not just when debug_enabled)
                self.logger.debug(
                    "Typing imports analysis",
                    extra={
                        "used_types": sorted(set(used_types)),
                        "existing_imports": sorted(existing_imports),
                        "needed_types": needed_types,
                    },
                )

                if needed_types:
                    # Always add missing types before source code section
                    # This ensures they're available even if source code has partial imports
                    imports_str = ", ".join(needed_types)
                    test_content_lines.append(f"from typing import {imports_str}")
                    test_content_lines.append("")

                    self.logger.info(
                        "Added missing typing imports",
                        extra={
                            "added_imports": needed_types,
                            "import_statement": f"from typing import {imports_str}",
                        },
                    )
                else:
                    self.logger.debug(
                        "All typing types already imported",
                        extra={"used_types": sorted(set(used_types))},
                    )

            test_content_lines.append(SOURCE_MARKER_START)
            # Use immutable source code copy - never modify this
            test_content_lines.extend(immutable_source_code.split("\n"))
            test_content_lines.append(SOURCE_MARKER_END)
            test_content_lines.append("")
            test_content_lines.append(TEST_MARKER_START)
            test_content_lines.append("")

            # Check if any test uses pytest functions and add import if needed
            uses_pytest = any(
                "pytest." in test_case.code
                or "pytest.raises" in test_case.code
                or "pytest.fixture" in test_case.code
                or "pytest.mark" in test_case.code
                for test_case in test_cases
                if test_case.code
            )
            if uses_pytest:
                # Check if import pytest is already present in any test case
                # Look for various import patterns
                has_pytest_import = any(
                    "import pytest" in test_case.code
                    or "from pytest import" in test_case.code
                    for test_case in test_cases
                    if test_case.code
                )
                if not has_pytest_import:
                    test_content_lines.append("import pytest")
                    test_content_lines.append("")

            # Add test cases - they should already be validated and cleaned
            # But add extra safety check here to ensure no source code modifications

            valid_test_count = 0
            skipped_test_count = 0

            for test_case in test_cases:
                # Double-check: ensure this is a valid test function
                if not test_case.code or "def test_" not in test_case.code:
                    skipped_test_count += 1
                    if self.debug_enabled:
                        self.logger.debug(
                            f"Skipping invalid test case: {test_case.name}",
                            extra={"reason": "no test function found"},
                        )
                    continue

                # CRITICAL: Validate that it doesn't contain source function redefinitions
                try:
                    test_ast = ast.parse(test_case.code)
                    # Check for any non-test function definitions that match source
                    has_redefinition = any(
                        isinstance(node, ast.FunctionDef)
                        and node.name in source_function_names
                        and not node.name.startswith("test_")
                        for node in ast.walk(test_ast)
                    )
                    if has_redefinition:
                        skipped_test_count += 1
                        if self.debug_enabled:
                            self.logger.warning(
                                f"Skipping test case with redefinition: {test_case.name}",
                                extra={
                                    "test_case": test_case.name,
                                    "reason": "source function redefinition detected",
                                },
                            )
                        continue  # Skip this test case

                    # Check for any non-test function definitions at all
                    has_non_test_function = any(
                        isinstance(node, ast.FunctionDef)
                        and not node.name.startswith("test_")
                        for node in ast.walk(test_ast)
                    )
                    if has_non_test_function:
                        skipped_test_count += 1
                        if self.debug_enabled:
                            self.logger.warning(
                                f"Skipping test case with non-test function: {test_case.name}",
                                extra={"reason": "non-test function definition found"},
                            )
                        continue  # Skip this test case
                except SyntaxError as e:
                    skipped_test_count += 1
                    if self.debug_enabled:
                        self.logger.warning(
                            f"Skipping test case with syntax error: {test_case.name}",
                            extra={"error": str(e)},
                        )
                    continue  # Skip invalid syntax

                # Test case is valid - add it
                test_content_lines.extend(test_case.code.split("\n"))
                test_content_lines.append("")
                valid_test_count += 1

            test_content = "\n".join(test_content_lines)

            self.logger.debug(
                "Test content assembled",
                extra={
                    "valid_tests": valid_test_count,
                    "skipped_tests": skipped_test_count,
                    "total_lines": len(test_content.split("\n")),
                },
            )

            # Debug: save intermediate file
            if self.debug_enabled:
                debug_path = Path("/tmp/test_agent_before_cleanup.py")
                try:
                    debug_path.write_text(test_content)
                    self.logger.debug(f"Saved intermediate file to {debug_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to save debug file: {e}")

            # CRITICAL: Protect source code section - it must remain immutable
            # Split content into source and test parts using strict markers
            if (
                SOURCE_MARKER_START in test_content
                and SOURCE_MARKER_END in test_content
            ):
                # CRITICAL: Extract imports that were added before SOURCE_MARKER_START
                # These are the typing imports we added for missing types
                source_start_idx = test_content.find(SOURCE_MARKER_START)
                imports_before_source = test_content[:source_start_idx].strip()

                # CRITICAL: Extract source part - this must remain completely unchanged
                source_end_idx = test_content.find(SOURCE_MARKER_END) + len(
                    SOURCE_MARKER_END
                )
                source_part = test_content[source_start_idx:source_end_idx]

                # Verify source code integrity
                extracted_source = source_part[
                    len(SOURCE_MARKER_START) : source_part.find(SOURCE_MARKER_END)
                ].strip()
                if extracted_source != immutable_source_code:
                    self.logger.error(
                        "Source code integrity violation detected!",
                        extra={
                            "original_hash": source_code_hash,
                            "extracted_hash": hash(extracted_source),
                        },
                    )
                    raise Exception(
                        "CRITICAL: Source code was modified during processing. "
                        "This should never happen."
                    )

                # Extract test part (everything after source section)
                test_part = test_content[source_end_idx:]
                if TEST_MARKER_START in test_part:
                    test_part = test_part.split(TEST_MARKER_START, 1)[1]

                # Clean only the test part
                test_lines = test_part.split("\n")
                cleaned_test_lines = []
                skip_function = False
                function_indent = 0

                for line in test_lines:
                    stripped = line.strip()
                    current_indent = (
                        len(line) - len(line.lstrip()) if line.strip() else 0
                    )

                    # Check if this is a function definition
                    func_match = re.match(r"def\s+(\w+)\s*\(", stripped)
                    if func_match:
                        func_name = func_match.group(1)
                        # If it's a source function (not a test), skip it
                        if (
                            func_name in source_function_names
                            and not func_name.startswith("test_")
                        ):
                            skip_function = True
                            function_indent = current_indent
                            continue
                        else:
                            skip_function = False

                    # If we're skipping a function, continue until we're back at module level
                    if skip_function:
                        # If we hit a new top-level definition, stop skipping
                        if stripped.startswith("def ") or stripped.startswith("class "):
                            if current_indent == 0:
                                skip_function = False
                                # Include this line if it's a test function
                                if stripped.startswith("def test_"):
                                    cleaned_test_lines.append(line)
                        # If we're back at module level (same or less indent), stop skipping
                        elif current_indent <= function_indent and stripped:
                            skip_function = False
                            if stripped.startswith("def test_"):
                                cleaned_test_lines.append(line)
                        continue

                    # Keep all other lines
                    cleaned_test_lines.append(line)

                # CRITICAL: Rebuild content with imports + immutable source + cleaned tests
                # Source part must remain exactly as extracted
                # Include imports that were added before SOURCE_MARKER_START
                rebuilt_parts = []
                if imports_before_source:
                    rebuilt_parts.append(imports_before_source)
                    rebuilt_parts.append("")
                rebuilt_parts.append(source_part)
                rebuilt_parts.append("")
                rebuilt_parts.append(TEST_MARKER_START)
                rebuilt_parts.append("")
                rebuilt_parts.append("\n".join(cleaned_test_lines))

                test_content = "\n".join(rebuilt_parts)

                # Verify source code integrity again after rebuilding
                rebuilt_source = test_content[
                    test_content.find(SOURCE_MARKER_START)
                    + len(SOURCE_MARKER_START) : test_content.find(SOURCE_MARKER_END)
                ].strip()
                if rebuilt_source != immutable_source_code:
                    self.logger.error("Source code integrity violation after rebuild!")
                    raise Exception(
                        "CRITICAL: Source code was modified during rebuild. "
                        "This should never happen."
                    )
            else:
                # Fallback: clean entire content (should not happen)
                lines = test_content.split("\n")
                cleaned_lines = []
                skip_function = False
                function_indent = 0

                for line in lines:
                    stripped = line.strip()
                    current_indent = (
                        len(line) - len(line.lstrip()) if line.strip() else 0
                    )

                    func_match = re.match(r"def\s+(\w+)\s*\(", stripped)
                    if func_match:
                        func_name = func_match.group(1)
                        if (
                            func_name in source_function_names
                            and not func_name.startswith("test_")
                        ):
                            skip_function = True
                            function_indent = current_indent
                            continue
                        else:
                            skip_function = False

                    if skip_function:
                        if stripped.startswith("def ") or stripped.startswith("class "):
                            if current_indent == 0:
                                skip_function = False
                                if stripped.startswith("def test_"):
                                    cleaned_lines.append(line)
                        elif current_indent <= function_indent and stripped:
                            skip_function = False
                            if stripped.startswith("def test_"):
                                cleaned_lines.append(line)
                        continue

                    cleaned_lines.append(line)

                test_content = "\n".join(cleaned_lines)

            # CRITICAL: Final validation - ensure source code integrity
            # Extract and verify source code one more time before writing
            if (
                SOURCE_MARKER_START in test_content
                and SOURCE_MARKER_END in test_content
            ):
                final_source = test_content[
                    test_content.find(SOURCE_MARKER_START)
                    + len(SOURCE_MARKER_START) : test_content.find(SOURCE_MARKER_END)
                ].strip()
                if final_source != immutable_source_code:
                    self.logger.error(
                        "Final source code integrity check failed!",
                        extra={
                            "original_hash": source_code_hash,
                            "final_hash": hash(final_source),
                        },
                    )
                    raise Exception(
                        "CRITICAL: Source code integrity check failed before file write. "
                        "Source code was modified."
                    )

            # Validate syntax before writing
            try:
                # First, validate that immutable source code is still valid
                ast.parse(immutable_source_code)
                # Then validate full test content
                ast.parse(test_content)
            except SyntaxError as e:
                # Try to fix: remove problematic lines that are not Python code
                lines = test_content.split("\n")
                fixed_lines = []
                error_line_num = e.lineno if e.lineno else len(lines)

                for i, line in enumerate(lines, 1):
                    if i == error_line_num:
                        # Check if this line is actually Python code
                        stripped = line.strip()
                        is_python = (
                            any(
                                char in stripped
                                for char in [
                                    "=",
                                    "(",
                                    ")",
                                    "[",
                                    "]",
                                    ":",
                                    "def ",
                                    "import ",
                                    "assert ",
                                    "return ",
                                    "if ",
                                    "for ",
                                    "while ",
                                    "try ",
                                    "except ",
                                    "class ",
                                ]
                            )
                            or stripped.startswith("#")
                            or not stripped
                        )

                        if not is_python:
                            # Skip non-Python lines
                            continue
                    fixed_lines.append(line)

                test_content = "\n".join(fixed_lines)

                # Try parsing again
                try:
                    ast.parse(test_content)
                except SyntaxError as e2:
                    # If still fails, try to isolate the problem
                    # Check if source code is valid
                    try:
                        ast.parse(code_file.content)
                        source_valid = True
                    except SyntaxError:
                        source_valid = False
                        raise Exception(f"Source code has syntax errors: {e}") from e

                    # If source is valid, problem is in generated tests
                    # Try to extract and validate each test case separately
                    test_only_lines = []
                    in_source = True
                    source_end_marker = SOURCE_MARKER_END

                    for line in test_content.split("\n"):
                        if source_end_marker in line:
                            in_source = False
                            test_only_lines.append(line)
                            continue
                        if not in_source:
                            test_only_lines.append(line)

                    test_only_content = "\n".join(test_only_lines)

                    # Try to fix test code by removing non-Python lines
                    lines = test_only_content.split("\n")
                    final_lines = []
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            final_lines.append(line)
                            continue
                        # Keep only valid Python constructs
                        if (
                            stripped.startswith(
                                ("def ", "import ", "from ", "class ", "#", "@")
                            )
                            or any(
                                char in stripped
                                for char in [
                                    "=",
                                    "(",
                                    ")",
                                    "[",
                                    "]",
                                    "assert ",
                                    "return ",
                                    "if ",
                                    "for ",
                                    "while ",
                                    "try ",
                                    "except ",
                                ]
                            )
                            or stripped.endswith(":")
                            or stripped.startswith('"""')
                            or stripped.startswith("'''")
                        ):
                            final_lines.append(line)
                        # Skip lines that are clearly not Python
                        elif len(stripped) > 30 and not any(
                            char in stripped
                            for char in [
                                "=",
                                "(",
                                ")",
                                "[",
                                "]",
                                ":",
                                "def ",
                                "import ",
                                "assert ",
                            ]
                        ):
                            continue  # Skip long text lines

                    # CRITICAL: Rebuild test content with immutable source code
                    # Never use code_file.content directly - use immutable copy
                    cleaned_test_content = "\n".join(
                        [
                            SOURCE_MARKER_START,
                            *immutable_source_code.split("\n"),
                            SOURCE_MARKER_END,
                            "",
                            TEST_MARKER_START,
                            "",
                            *final_lines,
                        ]
                    )

                    # Verify source code integrity in cleaned content
                    cleaned_source = cleaned_test_content[
                        cleaned_test_content.find(SOURCE_MARKER_START)
                        + len(SOURCE_MARKER_START) : cleaned_test_content.find(
                            SOURCE_MARKER_END
                        )
                    ].strip()
                    if cleaned_source != immutable_source_code:
                        raise Exception(
                            "CRITICAL: Source code integrity violation in cleaned content"
                        )

                    try:
                        ast.parse(cleaned_test_content)
                        test_content = cleaned_test_content
                    except SyntaxError as e3:
                        # Last resort: raise with full context
                        error_context_lines = cleaned_test_content.split("\n")
                        context_start = max(0, e3.lineno - 5)
                        context_end = min(len(error_context_lines), e3.lineno + 5)
                        context = "\n".join(
                            f"{i+1:4d}: {line}"
                            for i, line in enumerate(
                                error_context_lines[context_start:context_end],
                                start=context_start + 1,
                            )
                        )
                        raise Exception(
                            f"Generated test file has syntax errors. "
                            f"Last error at line {e3.lineno}: {e3.msg}\n"
                            f"Problematic area:\n{context}"
                        ) from e3

            # FINAL CHECK: Verify source code integrity one last time
            if SOURCE_MARKER_START in test_content:
                final_check_source = test_content[
                    test_content.find(SOURCE_MARKER_START)
                    + len(SOURCE_MARKER_START) : test_content.find(SOURCE_MARKER_END)
                ].strip()
                if final_check_source != immutable_source_code:
                    self.logger.error("Final source code integrity check failed!")
                    raise Exception(
                        "CRITICAL: Source code was modified. Aborting file write."
                    )

            self.logger.debug(
                "Writing test file",
                extra={
                    "file_path": str(test_file),
                    "content_length": len(test_content),
                    "source_hash": source_code_hash,
                },
            )

            test_file.write_text(test_content)

            # For debugging: always save to a known location
            if self.debug_enabled:
                debug_path = Path("/tmp/test_agent_debug.py")
                try:
                    debug_path.write_text(test_content)
                    self.logger.debug(f"Saved debug file to {debug_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to save debug file: {e}")

            try:
                result = self.test_executor.execute(str(test_file))
                coverage = self.test_executor.get_coverage(str(test_file))

                return TestResult(
                    status=result.status,
                    test_count=result.test_count,
                    passed_count=result.passed_count,
                    failed_count=result.failed_count,
                    coverage=coverage,
                    errors=result.errors,
                )
            except Exception as e:
                raise Exception(f"Test execution failed: {e}") from e
