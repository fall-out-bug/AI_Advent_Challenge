"""Unit tests for FormatAdapter."""

import pytest

from src.presentation.mcp.adapters.format_adapter import FormatAdapter
from src.presentation.mcp.exceptions import MCPValidationError


class TestFormatAdapter:
    """Test suite for FormatAdapter."""

    def test_format_valid_code(self):
        """Test formatting valid Python code."""
        adapter = FormatAdapter()

        code = "def hello():\n    print('world')"
        result = adapter.format_code(code)

        assert "formatted_code" in result
        assert "formatter_used" in result
        assert result["formatter_used"] == "black"

    def test_format_code_with_changes(self):
        """Test formatting code that needs changes."""
        adapter = FormatAdapter()

        # Code with inconsistent spacing
        code = "def hello( ):\n    print( 'world' )"
        result = adapter.format_code(code)

        assert result["formatter_used"] == "black"
        assert "changes_made" in result

    def test_format_empty_code_raises_error(self):
        """Test formatting empty code raises validation error."""
        adapter = FormatAdapter()

        with pytest.raises(MCPValidationError) as exc_info:
            adapter.format_code("")

        assert "empty" in str(exc_info.value).lower()

    def test_format_invalid_line_length_raises_error(self):
        """Test invalid line length raises error."""
        adapter = FormatAdapter()

        code = "def hello():\n    print('world')"

        with pytest.raises(MCPValidationError) as exc_info:
            adapter.format_code(code, line_length=10)

        assert "line_length" in str(exc_info.value).lower()

    def test_unsupported_formatter_raises_error(self):
        """Test unsupported formatter raises error."""
        adapter = FormatAdapter()

        code = "def hello():\n    print('world')"

        with pytest.raises(MCPValidationError) as exc_info:
            adapter.format_code(code, formatter="autopep8")

        assert "not supported" in str(exc_info.value).lower()

    def test_format_invalid_syntax_handles_gracefully(self):
        """Test invalid syntax is handled gracefully."""
        adapter = FormatAdapter()

        if not adapter.has_black:
            pytest.skip("black not installed")

        invalid_code = "def hello(:\n    print('world')"

        # Should not crash, may raise validation error
        try:
            result = adapter.format_code(invalid_code)
            # If it doesn't raise, that's also acceptable
            assert "formatted_code" in result
        except MCPValidationError:
            # This is also acceptable behavior
            pass

    def test_format_preserves_functionality(self):
        """Test formatting preserves code functionality."""
        adapter = FormatAdapter()

        if not adapter.has_black:
            pytest.skip("black not installed")

        code = "def add(a,b):\n    return a+b"
        result = adapter.format_code(code)

        # Key functionality should be preserved
        assert "def add" in result["formatted_code"]
        assert (
            "return a+b" in result["formatted_code"]
            or "return a + b" in result["formatted_code"]
        )
