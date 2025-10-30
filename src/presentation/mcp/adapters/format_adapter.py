"""Adapter for code formatting using black."""
import sys
from pathlib import Path
from typing import Any, Dict

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from src.presentation.mcp.exceptions import MCPValidationError


class FormatAdapter:
    """Adapter for code formatting using black."""

    def __init__(self) -> None:
        """Initialize format adapter."""
        try:
            import black
            self.black = black
            self.has_black = True
        except ImportError:
            self.has_black = False

    def format_code(self, code: str, formatter: str = "black", line_length: int = 100) -> Dict[str, Any]:
        """Format code using specified formatter."""
        self._validate_inputs(code, formatter, line_length)

        if formatter == "black":
            return self._format_with_black(code, line_length)
        else:
            raise MCPValidationError(
                f"Formatter '{formatter}' not supported. Use 'black'.",
                field="formatter"
            )

    def _validate_inputs(self, code: str, formatter: str, line_length: int) -> None:
        """Validate inputs."""
        if not code or not code.strip():
            raise MCPValidationError("code cannot be empty", field="code")
        if line_length < 20 or line_length > 200:
            raise MCPValidationError(
                "line_length must be between 20 and 200",
                restricted_to=["code", "line_length"]
            )

    def _format_with_black(self, code: str, line_length: int) -> Dict[str, Any]:
        """Format code with black."""
        if not self.has_black:
            raise MCPValidationError(
                "black package not installed. Run: pip install black",
                field="formatter"
            )

        try:
            mode = self.black.Mode(line_length=line_length)
            formatted = self.black.format_str(code, mode=mode)
            
            # Determine if changes were made
            changes_made = 0 if code == formatted else 1
            
            return {
                "formatted_code": formatted,
                "changes_made": changes_made,
                "formatter_used": "black",
            }
        except self.black.InvalidInput as e:
            raise MCPValidationError(
                f"Black formatting error: {e}",
                field="code"
            )
        except Exception as e:
            raise MCPValidationError(
                f"Formatting failed: {e}",
                field="code"
            )
