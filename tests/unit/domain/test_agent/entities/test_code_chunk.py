"""Unit tests for CodeChunk entity."""

import pytest

from src.domain.test_agent.entities.code_chunk import CodeChunk


def test_code_chunk_creation_with_all_fields():
    """Test CodeChunk creation with all fields."""
    # Arrange & Act
    chunk = CodeChunk(
        code="def hello(): pass",
        context="Module-level context",
        dependencies=["os", "sys"],
        location="src/example.py",
        start_line=1,
        end_line=5,
    )

    # Assert
    assert chunk.code == "def hello(): pass"
    assert chunk.context == "Module-level context"
    assert chunk.dependencies == ["os", "sys"]
    assert chunk.location == "src/example.py"
    assert chunk.start_line == 1
    assert chunk.end_line == 5


def test_code_chunk_with_code_content():
    """Test CodeChunk with code content."""
    # Arrange
    code_content = """
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""

    # Act
    chunk = CodeChunk(
        code=code_content,
        context="",
        dependencies=[],
        location="test.py",
        start_line=10,
        end_line=15,
    )

    # Assert
    assert "calculate_sum" in chunk.code
    assert chunk.code == code_content
    assert chunk.start_line == 10
    assert chunk.end_line == 15


def test_code_chunk_with_context_metadata():
    """Test CodeChunk with context metadata."""
    # Arrange & Act
    chunk = CodeChunk(
        code="def test(): pass",
        context="This function is part of the test suite",
        dependencies=["pytest"],
        location="tests/test_example.py",
        start_line=1,
        end_line=3,
    )

    # Assert
    assert chunk.context == "This function is part of the test suite"
    assert "pytest" in chunk.dependencies


def test_code_chunk_with_dependencies_list():
    """Test CodeChunk with dependencies list."""
    # Arrange & Act
    chunk = CodeChunk(
        code="import os, sys",
        context="",
        dependencies=["os", "sys", "pathlib"],
        location="src/utils.py",
        start_line=1,
        end_line=1,
    )

    # Assert
    assert len(chunk.dependencies) == 3
    assert "os" in chunk.dependencies
    assert "sys" in chunk.dependencies
    assert "pathlib" in chunk.dependencies


def test_code_chunk_location_info():
    """Test CodeChunk location information."""
    # Arrange & Act
    chunk = CodeChunk(
        code="def func(): pass",
        context="",
        dependencies=[],
        location="src/domain/test_agent/entities/code_chunk.py",
        start_line=42,
        end_line=50,
    )

    # Assert
    assert chunk.location == "src/domain/test_agent/entities/code_chunk.py"
    assert chunk.start_line == 42
    assert chunk.end_line == 50


def test_code_chunk_to_dict():
    """Test CodeChunk serialization to dictionary."""
    # Arrange
    chunk = CodeChunk(
        code="def test(): pass",
        context="Test context",
        dependencies=["pytest"],
        location="test.py",
        start_line=1,
        end_line=3,
    )

    # Act
    result = chunk.to_dict()

    # Assert
    assert isinstance(result, dict)
    assert result["code"] == "def test(): pass"
    assert result["context"] == "Test context"
    assert result["dependencies"] == ["pytest"]
    assert result["location"] == "test.py"
    assert result["start_line"] == 1
    assert result["end_line"] == 3


def test_code_chunk_from_dict():
    """Test CodeChunk deserialization from dictionary."""
    # Arrange
    data = {
        "code": "def test(): pass",
        "context": "Test context",
        "dependencies": ["pytest"],
        "location": "test.py",
        "start_line": 1,
        "end_line": 3,
    }

    # Act
    chunk = CodeChunk.from_dict(data)

    # Assert
    assert chunk.code == "def test(): pass"
    assert chunk.context == "Test context"
    assert chunk.dependencies == ["pytest"]
    assert chunk.location == "test.py"
    assert chunk.start_line == 1
    assert chunk.end_line == 3


def test_code_chunk_equality():
    """Test CodeChunk equality comparison."""
    # Arrange
    chunk1 = CodeChunk(
        code="def test(): pass",
        context="",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=3,
    )
    chunk2 = CodeChunk(
        code="def test(): pass",
        context="",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=3,
    )
    chunk3 = CodeChunk(
        code="def other(): pass",
        context="",
        dependencies=[],
        location="test.py",
        start_line=1,
        end_line=3,
    )

    # Act & Assert
    assert chunk1 == chunk2
    assert chunk1 != chunk3


def test_code_chunk_validation_empty_code():
    """Test CodeChunk validation for empty code."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="code cannot be empty"):
        CodeChunk(
            code="",
            context="",
            dependencies=[],
            location="test.py",
            start_line=1,
            end_line=3,
        )


def test_code_chunk_validation_invalid_location():
    """Test CodeChunk validation for invalid location."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="location cannot be empty"):
        CodeChunk(
            code="def test(): pass",
            context="",
            dependencies=[],
            location="",
            start_line=1,
            end_line=3,
        )

    with pytest.raises(ValueError, match="start_line must be positive"):
        CodeChunk(
            code="def test(): pass",
            context="",
            dependencies=[],
            location="test.py",
            start_line=0,
            end_line=3,
        )

    with pytest.raises(ValueError, match="end_line must be >= start_line"):
        CodeChunk(
            code="def test(): pass",
            context="",
            dependencies=[],
            location="test.py",
            start_line=5,
            end_line=3,
        )
