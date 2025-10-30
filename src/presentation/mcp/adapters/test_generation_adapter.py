"""Adapter for test generation."""
import sys
from pathlib import Path
from typing import Any, Dict
import re

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "shared"))

from src.presentation.mcp.exceptions import MCPValidationError, MCPAgentError


def _get_model_client_adapter():
    """Import ModelClientAdapter at runtime to avoid circular imports."""
    from src.presentation.mcp.adapters.model_client_adapter import ModelClientAdapter
    return ModelClientAdapter


class TestGenerationAdapter:
    """Adapter for generating tests from code."""

    def __init__(self, unified_client: Any, model_name: str = "mistral") -> None:
        """Initialize adapter."""
        self.unified_client = unified_client
        self.model_name = model_name

    async def generate_tests(self, code: str, test_framework: str = "pytest", coverage_target: int = 80) -> Dict[str, Any]:
        """Generate tests for provided code."""
        self._validate_inputs(code, test_framework)

        try:
            ModelClientAdapter = _get_model_client_adapter()
            adapter = ModelClientAdapter(self.unified_client, model_name=self.model_name)
            prompt = self._build_prompt(code, test_framework, coverage_target)
            result = await adapter.generate(prompt=prompt, max_tokens=1500, temperature=0.2)

            return self._parse_response(result.get("response", ""), test_framework)
        except (MCPValidationError, MCPAgentError):
            raise
        except Exception as e:
            raise MCPAgentError(f"Test generation failed: {e}")

    def _validate_inputs(self, code: str, test_framework: str) -> None:
        """Validate inputs."""
        if not code or not code.strip():
            raise MCPValidationError("code cannot be empty", field="code")
        if test_framework not in ["pytest", "unittest", "nose"]:
            raise MCPValidationError(
                f"test_framework must be pytest/unittest/nose, got {test_framework}",
                field="test_framework"
            )

    def _build_prompt(
        self, code: str, test_framework: str, coverage_target: int
    ) -> str:
        """Build prompt for test generation."""
        return f"""Generate comprehensive {test_framework} tests for this code:

```python
{code}
```

Requirements:
- Cover all functions and edge cases
- Target coverage: {coverage_target}%
- Use {test_framework} syntax
- Include docstrings
- Test both happy path and error cases

Return ONLY the test code, no explanations."""

    def _parse_response(self, text: str, test_framework: str) -> Dict[str, Any]:
        """Parse model response into structured dict."""
        # Extract test code (between markdown code blocks)
        test_code = self._extract_code(text)
        test_cases = self._extract_test_cases(test_code, test_framework)
        test_count = len(test_cases)

        # Estimate coverage based on number of test cases
        coverage_estimate = min(100, test_count * 15)  # Rough heuristic

        return {
            "success": True,
            "test_code": test_code,
            "test_count": test_count,
            "coverage_estimate": coverage_estimate,
            "test_cases": test_cases,
        }

    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown blocks."""
        # Try to find code in markdown blocks
        code_block = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()
        # If no block, assume entire text is code
        return text.strip()

    def _extract_test_cases(self, code: str, test_framework: str) -> list[str]:
        """Extract test function names from code."""
        if test_framework == "pytest":
            # Match def test_* patterns
            pattern = r"def (test_\w+)"
        elif test_framework == "unittest":
            # Match def test* patterns in TestCase classes
            pattern = r"def (test\w+)"
        else:
            pattern = r"def test\w+"

        matches = re.findall(pattern, code)
        return matches if isinstance(matches, list) else list(matches) if matches else []

