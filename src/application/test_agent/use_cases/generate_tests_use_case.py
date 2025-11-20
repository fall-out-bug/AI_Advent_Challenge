"""Use case for generating test cases from code."""

import ast
import os
import re
from typing import List

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.interfaces.llm_service import ITestAgentLLMService
from src.domain.test_agent.interfaces.use_cases import IGenerateTestsUseCase
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.logging import get_logger


class GenerateTestsUseCase:
    """
    Use case for generating test cases from code analysis using LLM.

    Purpose:
        Generates test cases for given code using LLM, validates pytest syntax,
        and returns domain entities.

    Example:
        >>> use_case = GenerateTestsUseCase(llm_service=service, llm_client=client)
        >>> code_file = CodeFile(path="test.py", content="def add(a, b): return a + b")
        >>> test_cases = use_case.generate_tests(code_file)
        >>> len(test_cases)
        3
    """

    def __init__(
        self,
        llm_service: ITestAgentLLMService,
        llm_client: LLMClient,
    ) -> None:
        """Initialize use case.

        Args:
            llm_service: Test agent LLM service for prompt generation.
            llm_client: LLM client for generating test code.
        """
        self.llm_service = llm_service
        self.llm_client = llm_client
        self.logger = get_logger("test_agent.generate_tests")
        self.debug_enabled = os.getenv("TEST_AGENT_DEBUG_LLM", "").lower() in (
            "1",
            "true",
            "yes",
        )

    async def generate_tests(
        self, code_file: CodeFile
    ) -> List[TestCase]:  # noqa: PLR0911
        """Generate test cases from code file using multi-pass approach.

        Purpose:
            Uses multi-pass generation for autonomous and universal operation:
            - Pass 1: Generate initial tests
            - Pass 2: Validate and clean each test individually
            - Pass 3: Fix or regenerate if needed
            - Pass 4: Final validation

        Args:
            code_file: CodeFile domain entity with code to test.

        Returns:
            List of TestCase domain entities (all valid).

        Raises:
            ValueError: If no valid tests can be generated.
            Exception: If LLM generation fails.
        """
        # Pass 1: Initial generation
        self.logger.info(
            "Starting test generation",
            extra={
                "file_path": code_file.path,
                "code_length": len(code_file.content),
                "code_lines": len(code_file.content.split("\n")),
            },
        )

        prompt = self.llm_service.generate_tests_prompt(code_file.content)

        try:
            self.logger.debug("Calling LLM for test generation")
            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2048,  # Increased for better generation
            )
            self.logger.debug(
                "LLM response received",
                extra={
                    "response_length": len(response),
                    "response_lines": len(response.split("\n")),
                },
            )
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise Exception(f"LLM generation failed: {e}") from e

        # Debug: save LLM response
        if self.debug_enabled and hasattr(self.llm_service, "_save_debug_output"):
            self.llm_service._save_debug_output("response", response, code_file.content)

        # Pass 2: Parse and validate each test individually
        self.logger.debug("Parsing test cases from LLM response")
        test_cases = self._parse_test_cases(response, code_file)
        self.logger.debug(
            "Test cases parsed",
            extra={
                "total_parsed": len(test_cases),
                "test_names": [tc.name for tc in test_cases],
            },
        )

        valid_test_cases = self._validate_and_clean_tests(test_cases, code_file)
        self.logger.debug(
            "Test cases validated and cleaned",
            extra={
                "valid_count": len(valid_test_cases),
                "removed_count": len(test_cases) - len(valid_test_cases),
                "valid_names": [tc.name for tc in valid_test_cases],
            },
        )

        # Pass 3: If we have too few tests, try to fix or regenerate
        if len(valid_test_cases) < 2:
            self.logger.warning(
                "Too few valid tests, attempting regeneration",
                extra={"valid_count": len(valid_test_cases)},
            )
            # Try one more generation with stricter prompt
            try:
                stricter_prompt = (
                    prompt
                    + "\n\nIMPORTANT: Generate ONLY test functions starting with 'def test_'. Do NOT redefine source functions."
                )
                self.logger.debug("Calling LLM for regeneration with stricter prompt")
                response2 = await self.llm_client.generate(
                    prompt=stricter_prompt,
                    temperature=0.1,
                    max_tokens=1024,
                )
                additional_tests = self._parse_test_cases(response2, code_file)
                additional_valid = self._validate_and_clean_tests(
                    additional_tests, code_file
                )
                self.logger.debug(
                    "Regeneration completed",
                    extra={
                        "additional_valid": len(additional_valid),
                        "total_after_regeneration": len(valid_test_cases)
                        + len(additional_valid),
                    },
                )
                valid_test_cases.extend(additional_valid)
            except Exception as e:
                self.logger.warning(f"Regeneration failed: {e}")

        # Pass 4: Final validation
        if not valid_test_cases:
            self.logger.error("No valid test cases could be generated")
            raise ValueError("No valid test cases could be generated")

        self.logger.info(
            "Test generation completed",
            extra={
                "final_count": len(valid_test_cases),
                "test_names": [tc.name for tc in valid_test_cases],
            },
        )

        return valid_test_cases

    def _parse_test_cases(
        self, llm_response: str, code_file: CodeFile
    ) -> List[TestCase]:
        """Parse test cases from LLM response.

        Args:
            llm_response: Raw response from LLM.
            code_file: Source code file to check against.

        Returns:
            List of TestCase domain entities.
        """
        # Remove markdown code blocks if present
        llm_response = re.sub(r"```python\s*\n", "", llm_response)
        llm_response = re.sub(r"```\s*\n", "", llm_response)
        llm_response = re.sub(r"```", "", llm_response)

        # Remove explanatory text that's not Python code
        lines = llm_response.split("\n")
        cleaned_lines = []
        in_test_function = False
        indent_level = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Keep empty lines
            if not stripped:
                if in_test_function:
                    cleaned_lines.append(line)
                continue

            # Start of a test function - mark as valid code
            if stripped.startswith("def test_"):
                in_test_function = True
                indent_level = len(line) - len(line.lstrip())
                cleaned_lines.append(line)
                continue

            # If we're in a test function, keep the line if it's properly indented
            if in_test_function:
                current_indent = len(line) - len(line.lstrip())
                # If we hit a new top-level definition (not a test), stop
                if (
                    stripped.startswith("def ") or stripped.startswith("class ")
                ) and current_indent == 0:
                    if not stripped.startswith("def test_"):
                        # End of test functions
                        break
                    else:
                        # Another test function
                        cleaned_lines.append(line)
                        continue
                # Keep properly indented lines within test function
                if (
                    current_indent > indent_level
                    or line.startswith(" ")
                    or line.startswith("\t")
                ):
                    cleaned_lines.append(line)
                    continue
                # If we're back at module level and it's not a test function, stop
                if current_indent == 0 and not stripped.startswith("def test_"):
                    break

            # Skip lines that are clearly explanatory text
            if any(
                stripped.startswith(phrase)
                for phrase in [
                    "Note:",
                    "However:",
                    "But based on",
                    "However,",
                    "But",
                    "Since",
                    "Based on",
                    "The",
                    "This",
                    "These",
                    "We may",
                    "CRITICAL",
                    "Requirements:",
                    "Example:",
                    "If the source",
                    "Generate",
                    "Follow",
                    "Use pytest",
                    "Write test",
                ]
            ):
                continue

            # Skip long text lines without Python syntax
            if (
                len(stripped) > 60
                and not any(
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
                        "#",
                        "@",
                    ]
                )
                and not stripped.startswith("def ")
                and not stripped.startswith("import ")
                and not stripped.startswith("from ")
            ):
                continue

            # If it looks like Python code, keep it
            if (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("def ")
                or stripped.startswith("class ")
                or stripped.startswith("@")
                or "=" in stripped
                or "(" in stripped
            ):
                cleaned_lines.append(line)
                in_test_function = True  # Assume we're in code now

        llm_response = "\n".join(cleaned_lines)

        # Final cleanup: remove any remaining non-Python text at the end
        # Split by test functions and keep only valid Python
        test_blocks = re.split(r"(def test_\w+)", llm_response)
        cleaned_blocks = []
        for block in test_blocks:
            if block.strip().startswith("def test_"):
                cleaned_blocks.append(block)
            elif block.strip() and any(
                char in block
                for char in ["=", "(", ")", "[", "]", ":", "assert", "import", "from"]
            ):
                cleaned_blocks.append(block)

        llm_response = "".join(cleaned_blocks)

        # Extract source function names to avoid redefinitions
        source_function_names = set()
        try:
            source_tree = ast.parse(code_file.content)
            for node in ast.walk(source_tree):
                if isinstance(node, ast.FunctionDef):
                    source_function_names.add(node.name)
        except SyntaxError:
            pass  # If source is invalid, we can't check

        test_cases: List[TestCase] = []
        lines = llm_response.split("\n")
        current_test: List[str] = []
        current_name = ""
        base_indent = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments at module level
            if not stripped or stripped.startswith("#"):
                if current_test:
                    current_test.append(line)
                continue

            # CRITICAL: Skip function definitions that are NOT test functions
            # These are likely redefinitions of source functions
            if stripped.startswith("def ") and not stripped.startswith("def test_"):
                # Skip this function and everything until we find a test function
                # Skip lines until we find a test function or reach end
                skip_until_test = True
                for j in range(i + 1, len(lines)):
                    next_stripped = lines[j].strip()
                    if next_stripped.startswith("def test_"):
                        # Found a test function, process it
                        i = j - 1  # Will be incremented by loop
                        break
                    elif next_stripped.startswith(
                        "def "
                    ) and not next_stripped.startswith("def test_"):
                        # Another non-test function, continue skipping
                        continue
                continue

            # Check if this is a new test function definition
            if stripped.startswith("def test_"):
                # Save previous test if exists and validate it
                if current_test and current_name:
                    test_code = "\n".join(current_test).strip()
                    if test_code:  # Only add non-empty tests
                        # Validate before adding
                        if self._is_valid_test_code(test_code, source_function_names):
                            test_cases.append(
                                TestCase(
                                    name=current_name,
                                    code=test_code,
                                )
                            )

                # Start new test
                current_test = [line]
                base_indent = len(line) - len(line.lstrip())

                match = re.search(r"def (test_\w+)", line)
                if match:
                    current_name = match.group(1)
                else:
                    current_name = "test_unknown"
            elif current_test:
                # Check if we've moved to a new top-level definition (end of current test)
                if stripped.startswith("def ") or stripped.startswith("class "):
                    # This is a new function/class, save current test
                    if current_name:
                        test_code = "\n".join(current_test).strip()
                        if test_code:
                            # Validate before adding
                            if self._is_valid_test_code(
                                test_code, source_function_names
                            ):
                                test_cases.append(
                                    TestCase(
                                        name=current_name,
                                        code=test_code,
                                    )
                                )
                    # Start new test if it's a test function
                    if stripped.startswith("def test_"):
                        current_test = [line]
                        base_indent = len(line) - len(line.lstrip())
                        match = re.search(r"def (test_\w+)", line)
                        if match:
                            current_name = match.group(1)
                        else:
                            current_name = "test_unknown"
                    else:
                        # Not a test function, clear current test
                        current_test = []
                        current_name = ""
                else:
                    # Continue current test
                    current_test.append(line)

        # Save last test
        if current_test and current_name:
            test_code = "\n".join(current_test).strip()
            if test_code:
                # Validate before adding
                if self._is_valid_test_code(test_code, source_function_names):
                    test_cases.append(
                        TestCase(
                            name=current_name,
                            code=test_code,
                        )
                    )

        return test_cases

    def _is_valid_test_code(
        self, test_code: str, source_function_names: set[str]
    ) -> bool:
        """Check if test code is valid and doesn't redefine source functions.

        Enhanced AST validation:
        - Checks all function definition types (FunctionDef, AsyncFunctionDef)
        - Checks for class definitions that might shadow source
        - Validates nested definitions
        - Provides detailed logging for debugging

        Args:
            test_code: Test code to validate.
            source_function_names: Set of source function names to avoid.

        Returns:
            True if test code is valid, False otherwise.
        """
        if not test_code or not test_code.strip():
            if self.debug_enabled:
                self.logger.debug("Test code is empty")
            return False

        try:
            tree = ast.parse(test_code)

            # Enhanced: Check for test function (including async)
            has_test_function = False
            test_function_names = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_"):
                        has_test_function = True
                        test_function_names.append(node.name)

            if not has_test_function:
                if self.debug_enabled:
                    self.logger.debug(
                        "No test function found in code",
                        extra={"code_preview": test_code[:100]},
                    )
                return False

            # Enhanced: Check for ALL function definition types
            all_function_defs = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    all_function_defs.append(node.name)

            # Enhanced: Check for source function redefinitions (all types)
            redefinitions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in source_function_names and not node.name.startswith(
                        "test_"
                    ):
                        redefinitions.append(node.name)

            if redefinitions:
                if self.debug_enabled:
                    self.logger.warning(
                        "Source function redefinitions detected",
                        extra={
                            "redefinitions": redefinitions,
                            "source_functions": list(source_function_names),
                            "test_functions": test_function_names,
                        },
                    )
                return False

            # Enhanced: Check for any non-test function definitions
            non_test_functions = [
                name
                for name in all_function_defs
                if not name.startswith("test_") and name not in source_function_names
            ]
            if non_test_functions:
                if self.debug_enabled:
                    self.logger.warning(
                        "Non-test function definitions found",
                        extra={
                            "non_test_functions": non_test_functions,
                            "test_functions": test_function_names,
                        },
                    )
                return False

            if self.debug_enabled:
                self.logger.debug(
                    "Test code validation passed",
                    extra={
                        "test_functions": test_function_names,
                        "total_functions": len(all_function_defs),
                    },
                )

            return True
        except SyntaxError as e:
            if self.debug_enabled:
                self.logger.warning(
                    "Syntax error in test code",
                    extra={"error": str(e), "code_preview": test_code[:200]},
                )
            return False

    def _validate_and_clean_tests(
        self, test_cases: List[TestCase], code_file: CodeFile
    ) -> List[TestCase]:
        """Validate and clean test cases individually (Pass 2).

        Purpose:
            Validates each test case separately, removes invalid ones,
            and filters out any function redefinitions.

        Args:
            test_cases: List of test cases to validate.
            code_file: Source code file to check against.

        Returns:
            List of valid TestCase entities.
        """
        if not test_cases:
            return []

        # Extract source function names to avoid redefinitions
        source_function_names = set()
        try:
            source_tree = ast.parse(code_file.content)
            for node in ast.walk(source_tree):
                if isinstance(node, ast.FunctionDef):
                    source_function_names.add(node.name)
        except SyntaxError:
            pass  # If source is invalid, we can't check

        valid_tests = []

        for test_case in test_cases:
            if not test_case.code or not test_case.code.strip():
                continue

            # Clean the test code
            cleaned_code = self._clean_test_code(test_case.code, source_function_names)

            if not cleaned_code or not cleaned_code.strip():
                continue

            # Enhanced AST validation
            try:
                tree = ast.parse(cleaned_code)

                # Enhanced: Check for test function (including async)
                has_test_function = False
                test_function_names = []
                all_function_defs = []
                redefinitions = []

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        all_function_defs.append(node.name)
                        if node.name.startswith("test_"):
                            has_test_function = True
                            test_function_names.append(node.name)
                        elif node.name in source_function_names:
                            redefinitions.append(node.name)

                if not has_test_function:
                    if self.debug_enabled:
                        self.logger.debug(
                            f"Skipping test case: {test_case.name} - no test function"
                        )
                    continue

                if redefinitions:
                    if self.debug_enabled:
                        self.logger.warning(
                            f"Skipping test case: {test_case.name} - redefinitions found",
                            extra={"redefinitions": redefinitions},
                        )
                    continue

                # Enhanced: Check for any non-test function definitions
                non_test_functions = [
                    name
                    for name in all_function_defs
                    if not name.startswith("test_")
                    and name not in source_function_names
                ]
                if non_test_functions:
                    if self.debug_enabled:
                        self.logger.warning(
                            f"Skipping test case: {test_case.name} - non-test functions",
                            extra={"non_test_functions": non_test_functions},
                        )
                    continue

                # Enhanced: Check for class definitions that might shadow source
                class_definitions = [
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                ]
                if class_definitions:
                    # Check if any class name matches source function names
                    conflicting_classes = [
                        name
                        for name in class_definitions
                        if name in source_function_names
                    ]
                    if conflicting_classes:
                        if self.debug_enabled:
                            self.logger.warning(
                                f"Skipping test case: {test_case.name} - conflicting class",
                                extra={"conflicting_classes": conflicting_classes},
                            )
                        continue

                # Test is valid
                if self.debug_enabled:
                    self.logger.debug(
                        f"Test case validated: {test_case.name}",
                        extra={
                            "test_functions": test_function_names,
                            "code_length": len(cleaned_code),
                        },
                    )
                valid_tests.append(TestCase(name=test_case.name, code=cleaned_code))

            except SyntaxError as e:
                if self.debug_enabled:
                    self.logger.warning(
                        f"Skipping test case: {test_case.name} - syntax error",
                        extra={"error": str(e)},
                    )
                continue

        return valid_tests

    def _clean_test_code(self, test_code: str, source_function_names: set[str]) -> str:
        """Clean test code by removing invalid parts.

        Enhanced filtering:
        - Removes function redefinitions more aggressively
        - Handles nested functions and classes
        - Filters explanatory text more effectively
        - Preserves valid test code structure

        Args:
            test_code: Raw test code to clean.
            source_function_names: Set of source function names to avoid.

        Returns:
            Cleaned test code.
        """
        if not test_code or not test_code.strip():
            return ""

        lines = test_code.split("\n")
        cleaned_lines = []
        skip_function = False
        skip_class = False
        function_indent = 0
        class_indent = 0
        in_multiline_string = False
        multiline_string_char = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 0

            # Track multiline strings to avoid false positives
            if not in_multiline_string:
                if '"""' in line or "'''" in line:
                    # Check if it's opening or closing
                    quote_count = line.count('"""') + line.count("'''")
                    if quote_count % 2 == 1:  # Odd number means toggle
                        in_multiline_string = not in_multiline_string
                        if in_multiline_string:
                            multiline_string_char = '"""' if '"""' in line else "'''"
            else:
                # Inside multiline string - check for closing
                if multiline_string_char in line:
                    quote_count = line.count(multiline_string_char)
                    if quote_count % 2 == 1:  # Odd number means closing
                        in_multiline_string = False
                        multiline_string_char = None
                # Skip processing lines inside multiline strings
                cleaned_lines.append(line)
                continue

            # Enhanced: Skip non-test function definitions (including async)
            # Only skip if it's at module level (indent == 0) or if it's a source redefinition
            if stripped.startswith(("def ", "async def ")) and not stripped.startswith(
                ("def test_", "async def test_")
            ):
                # Check if it's a source function redefinition
                func_match = re.search(r"(?:async\s+)?def\s+(\w+)\s*\(", stripped)
                if func_match:
                    func_name = func_match.group(1)
                    if func_name in source_function_names:
                        # Always skip source function redefinitions
                        skip_function = True
                        function_indent = current_indent
                        if self.debug_enabled:
                            self.logger.debug(
                                f"Skipping function redefinition: {func_name}",
                                extra={"line": i + 1, "function": func_name},
                            )
                        continue
                    # Only skip non-test functions at module level (not nested)
                    if not func_name.startswith("test_") and current_indent == 0:
                        skip_function = True
                        function_indent = current_indent
                        continue
                    # Nested functions are OK (they're inside test functions)

            # Enhanced: Skip class definitions that might conflict
            if stripped.startswith("class ") and not stripped.startswith("class Test"):
                class_match = re.search(r"class\s+(\w+)", stripped)
                if class_match:
                    class_name = class_match.group(1)
                    if class_name in source_function_names:
                        skip_class = True
                        class_indent = current_indent
                        if self.debug_enabled:
                            self.logger.debug(
                                f"Skipping conflicting class: {class_name}",
                                extra={"line": i + 1, "class": class_name},
                            )
                        continue

            # If skipping a function, continue until we're back at module level
            if skip_function:
                # Check if we hit a new top-level definition
                if (
                    stripped.startswith(("def ", "async def ", "class "))
                    and current_indent == 0
                ):
                    skip_function = False
                    # Include this line if it's a test function
                    if stripped.startswith(("def test_", "async def test_")):
                        cleaned_lines.append(line)
                # If we're back at module level (same or less indent), stop skipping
                elif current_indent <= function_indent and stripped:
                    skip_function = False
                    if stripped.startswith(("def test_", "async def test_")):
                        cleaned_lines.append(line)
                continue

            # If skipping a class, continue until we're back at module level
            if skip_class:
                # Check if we hit a new top-level definition
                if (
                    stripped.startswith(("def ", "async def ", "class "))
                    and current_indent == 0
                ):
                    skip_class = False
                    # Include this line if it's a test function
                    if stripped.startswith(("def test_", "async def test_")):
                        cleaned_lines.append(line)
                # If we're back at module level (same or less indent), stop skipping
                elif current_indent <= class_indent and stripped:
                    skip_class = False
                    # Include this line if it's a test function
                    if stripped.startswith(("def test_", "async def test_")):
                        cleaned_lines.append(line)
                continue

            # Enhanced: Skip explanatory text with better patterns
            if stripped and not stripped.startswith(
                ("#", "def ", "class ", "import ", "from ", "@")
            ):
                # Check for common explanatory phrases (at start of line)
                explanatory_patterns = [
                    r"^(Note|However|But|Since|Based on|The|This|These|We may|CRITICAL|Requirements|Example|Generate|Follow|Use pytest|Write test)[:.,]",
                    r"^If the source",
                    r"^The source code",
                    r"^You should",
                    r"^Make sure",
                ]
                matches_pattern = any(
                    re.match(pattern, stripped, re.IGNORECASE)
                    for pattern in explanatory_patterns
                )
                if matches_pattern:
                    # Skip explanatory lines (both short and long)
                    if self.debug_enabled:
                        self.logger.debug(
                            f"Skipping explanatory text: {stripped[:50]}",
                            extra={"line": i + 1},
                        )
                    continue

            # Enhanced: Skip lines that are clearly not Python code
            if stripped and len(stripped) > 60:
                # Check if it looks like Python code
                python_indicators = [
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
                    "@",
                    "yield ",
                    "async ",
                    "await ",
                ]
                if not any(indicator in stripped for indicator in python_indicators):
                    # Likely explanatory text
                    if self.debug_enabled:
                        self.logger.debug(
                            f"Skipping non-Python line: {stripped[:50]}",
                            extra={"line": i + 1},
                        )
                    continue

            # Keep valid Python code
            cleaned_lines.append(line)

        cleaned_code = "\n".join(cleaned_lines).strip()

        if self.debug_enabled and len(cleaned_code) != len(test_code):
            self.logger.debug(
                "Test code cleaned",
                extra={
                    "original_length": len(test_code),
                    "cleaned_length": len(cleaned_code),
                    "removed_lines": len(lines) - len(cleaned_lines),
                },
            )

        return cleaned_code

    def _validate_pytest_syntax(self, test_cases: List[TestCase]) -> None:
        """Validate pytest syntax using enhanced AST validation.

        Enhanced validation:
        - Checks all function definition types
        - Validates test function naming
        - Provides detailed error messages

        Args:
            test_cases: List of test cases to validate.

        Raises:
            ValueError: If any test case has invalid syntax.
        """
        if not test_cases:
            raise ValueError("No test cases generated")

        for test_case in test_cases:
            if not test_case.code or not test_case.code.strip():
                raise ValueError(f"Empty test case: {test_case.name}")

            try:
                tree = ast.parse(test_case.code)

                # Enhanced: Check for function definitions (all types)
                has_function = any(
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    for node in ast.walk(tree)
                )
                if not has_function:
                    raise ValueError(
                        f"Test case {test_case.name} does not contain a function definition"
                    )

                # Enhanced: Verify at least one test function exists
                has_test_function = any(
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name.startswith("test_")
                    for node in ast.walk(tree)
                )
                if not has_test_function:
                    raise ValueError(
                        f"Test case {test_case.name} does not contain a test function (name must start with 'test_')"
                    )

            except SyntaxError as e:
                error_msg = str(e)
                if hasattr(e, "lineno") and e.lineno:
                    lines = test_case.code.split("\n")
                    if e.lineno <= len(lines):
                        error_msg += (
                            f"\nProblematic line {e.lineno}: {lines[e.lineno - 1]}"
                        )

                if self.debug_enabled:
                    self.logger.error(
                        f"Syntax error in test case: {test_case.name}",
                        extra={"error": error_msg, "code": test_case.code[:500]},
                    )

                raise ValueError(
                    f"Invalid pytest syntax in {test_case.name}: {error_msg}"
                ) from e
