"""Unit tests for CodeFile entity."""

import pytest

from src.domain.test_agent.entities.code_file import CodeFile


def test_code_file_creation_with_valid_path():
    """Test CodeFile creation with valid path."""
    code_file = CodeFile(
        path="src/domain/test_agent/entities/code_file.py",
        content="def hello(): pass",
    )

    assert code_file.path == "src/domain/test_agent/entities/code_file.py"
    assert code_file.content == "def hello(): pass"
    assert code_file.metadata == {}


def test_code_file_creation_with_content():
    """Test CodeFile creation with content."""
    content = """
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""
    code_file = CodeFile(
        path="test.py",
        content=content,
    )

    assert code_file.path == "test.py"
    assert "calculate_sum" in code_file.content
    assert code_file.content == content


def test_code_file_metadata_handling():
    """Test CodeFile metadata handling."""
    metadata = {"language": "python", "lines": 10, "complexity": "low"}
    code_file = CodeFile(
        path="test.py",
        content="def test(): pass",
        metadata=metadata,
    )

    assert code_file.metadata == metadata
    assert code_file.metadata["language"] == "python"
    assert code_file.metadata["lines"] == 10
    assert code_file.metadata["complexity"] == "low"


def test_code_file_validation_errors():
    """Test CodeFile validation errors."""
    with pytest.raises(ValueError, match="path cannot be empty"):
        CodeFile(path="", content="def test(): pass")

    with pytest.raises(ValueError, match="content cannot be None"):
        CodeFile(path="test.py", content=None)  # type: ignore
