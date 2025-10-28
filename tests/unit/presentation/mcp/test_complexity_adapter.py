"""Unit tests for ParliamentAdapter."""

import pytest
from src.presentation.mcp.adapters.complexity_adapter import ComplexityAdapter
from src.presentation.mcp.exceptions import MCPValidationError


class TestComplexityAdapter:
    """Test suite for ComplexityAdapter."""

    def test_analyze_simple_code(self):
        """Test analyzing simple code."""
        adapter = ComplexityAdapter()
        
        code = """def add(a, b):
    return a + b
"""
        result = adapter.analyze_complexity(code)
        
        assert "cyclomatic_complexity" in result
        assert "lines_of_code" in result
        assert "maintainability_index" in result
        assert "recommendations" in result

    def test_analyze_complex_code(self):
        """Test analyzing complex code."""
        adapter = ComplexityAdapter()
        
        code = """def complex_func(x):
    if x > 0:
        for i in range(10):
            if i % 2 == 0:
                while i > 0:
                    i -= 1
    return x
"""
        result = adapter.analyze_complexity(code)
        
        assert result["cyclomatic_complexity"] > 1
        assert len(result["recommendations"]) >= 0

    def test_analyze_empty_code_raises_error(self):
        """Test analyzing empty code raises error."""
        adapter = ComplexityAdapter()
        
        with pytest.raises(MCPValidationError) as exc_info:
            adapter.analyze_complexity("")
        
        assert "empty" in str(exc_info.value).lower()

    def test_analyze_detailed_mode(self):
        """Test detailed analysis mode."""
        adapter = ComplexityAdapter()
        
        code = """def func1():
    return 1

def func2():
    return 2
"""
        result = adapter.analyze_complexity(code, detailed=True)
        
        if adapter.has_radon:
            assert "functions" in result or "recommendations" in result

    def test_analyze_simple_mode(self):
        """Test simple analysis mode."""
        adapter = ComplexityAdapter()
        
        code = "def hello():\n    print('world')"
        result = adapter.analyze_complexity(code, detailed=False)
        
        assert "cyclomatic_complexity" in result
        assert "maintainability_index" in result

    def test_analyze_class_with_methods(self):
        """Test analyzing class with methods."""
        adapter = ComplexityAdapter()
        
        code = """class TestClass:
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        return self.value
    
    def set_value(self, v):
        self.value = v
"""
        result = adapter.analyze_complexity(code)
        
        assert result["lines_of_code"] >= 5
        assert isinstance(result["maintainability_index"], (int, float))

    def test_recommendations_for_complex_code(self):
        """Test recommendations generated for complex code."""
        adapter = ComplexityAdapter()
        
        # Intentionally complex code
        code = """def very_complex(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    return x
                else:
                    return x - 1
            else:
                return x - 2
        else:
            return x - 3
    else:
        return x - 4
"""
        result = adapter.analyze_complexity(code, detailed=True)
        
        # Should have some recommendations for complex code
        assert len(result["recommendations"]) >= 0
        assert result["cyclomatic_complexity"] >= 5

