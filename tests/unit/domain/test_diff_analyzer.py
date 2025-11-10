"""Tests for DiffAnalyzer service."""

import pytest

from src.domain.services.diff_analyzer import DiffAnalyzer
from src.domain.value_objects.code_diff import CodeDiff


def test_diff_analyzer_simple_text_diff():
    """Test simple text diff analysis."""
    analyzer = DiffAnalyzer()
    old_code = "def hello():\n    print('old')"
    new_code = "def hello():\n    print('new')\n    print('added')"
    diff = analyzer.analyze(old_code, new_code)
    assert isinstance(diff, CodeDiff)
    assert diff.lines_added > 0
    assert diff.lines_removed > 0


def test_diff_analyzer_identical_code():
    """Test diff analysis with identical code."""
    analyzer = DiffAnalyzer()
    code = "def hello():\n    pass"
    diff = analyzer.analyze(code, code)
    assert diff.lines_added == 0
    assert diff.lines_removed == 0
    assert diff.change_ratio == 0.0


def test_diff_analyzer_new_file():
    """Test diff analysis with new file (no old code)."""
    analyzer = DiffAnalyzer()
    diff = analyzer.analyze("", "def new_func():\n    pass")
    assert diff.lines_added > 0
    assert diff.lines_removed == 0


def test_diff_analyzer_ast_analysis_functions():
    """Test AST analysis detects function changes."""
    analyzer = DiffAnalyzer()
    old_code = "def old_func():\n    pass"
    new_code = "def old_func():\n    pass\ndef new_func():\n    pass"
    diff = analyzer.analyze(old_code, new_code)
    assert "new_func" in diff.functions_added


def test_diff_analyzer_ast_analysis_imports():
    """Test AST analysis detects import changes."""
    analyzer = DiffAnalyzer()
    old_code = "import os"
    new_code = "import os\nimport sys"
    diff = analyzer.analyze(old_code, new_code)
    assert diff.has_new_imports is True
    assert len(diff.imports_added) > 0


def test_diff_analyzer_ast_analysis_classes():
    """Test AST analysis detects class changes."""
    analyzer = DiffAnalyzer()
    old_code = "class Old:\n    pass"
    new_code = "class Old:\n    def new_method(self):\n        pass"
    diff = analyzer.analyze(old_code, new_code)
    assert "Old" in diff.classes_changed


def test_diff_analyzer_invalid_python():
    """Test diff analyzer handles invalid Python gracefully."""
    analyzer = DiffAnalyzer()
    old_code = "def broken("
    new_code = "def fixed():\n    pass"
    # Should not raise, fallback to text diff
    diff = analyzer.analyze(old_code, new_code)
    assert isinstance(diff, CodeDiff)


def test_diff_analyzer_empty_code():
    """Test diff analyzer with empty code."""
    analyzer = DiffAnalyzer()
    diff = analyzer.analyze("", "")
    assert diff.lines_added == 0
    assert diff.lines_removed == 0
    assert diff.change_ratio == 0.0
