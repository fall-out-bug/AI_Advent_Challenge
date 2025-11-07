"""Tests for CodeDiff value object."""

import pytest

from src.domain.value_objects.code_diff import CodeDiff


def test_code_diff_creation():
    """Test CodeDiff creation with valid data."""
    diff = CodeDiff(
        lines_added=10,
        lines_removed=5,
        lines_changed=8,
        change_ratio=15.5,
        functions_added=["new_func"],
        functions_removed=["old_func"],
        classes_changed=["MyClass"],
        imports_added=["import os"],
        imports_removed=["import sys"],
        complexity_delta=2,
        has_refactor=True,
        has_new_imports=True,
    )
    assert diff.lines_added == 10
    assert diff.lines_removed == 5
    assert diff.functions_added == ["new_func"]
    assert diff.has_refactor is True


def test_code_diff_minimal():
    """Test CodeDiff with minimal data."""
    diff = CodeDiff(
        lines_added=0,
        lines_removed=0,
        lines_changed=0,
        change_ratio=0.0,
    )
    assert diff.lines_added == 0
    assert diff.functions_added == []
    assert diff.has_refactor is False


def test_code_diff_validation_negative_lines():
    """Test CodeDiff validation fails with negative lines."""
    with pytest.raises(ValueError, match="lines_added must be non-negative"):
        CodeDiff(
            lines_added=-1,
            lines_removed=0,
            lines_changed=0,
            change_ratio=0.0,
        )


def test_code_diff_validation_invalid_ratio():
    """Test CodeDiff validation fails with invalid change_ratio."""
    with pytest.raises(ValueError, match="change_ratio must be between 0 and 100"):
        CodeDiff(
            lines_added=10,
            lines_removed=5,
            lines_changed=8,
            change_ratio=150.0,
        )

