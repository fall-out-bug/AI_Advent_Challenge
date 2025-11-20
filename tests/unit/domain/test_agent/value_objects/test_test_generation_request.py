"""Unit tests for TestGenerationRequest value object."""

import pytest

from src.domain.test_agent.value_objects.test_generation_request import (
    TestGenerationRequest,
)


def test_test_generation_request_creation():
    """Test TestGenerationRequest creation."""
    request = TestGenerationRequest(
        code_file_path="src/example.py",
        language="python",
    )

    assert request.code_file_path == "src/example.py"
    assert request.language == "python"
    assert request.metadata == {}


def test_test_generation_request_validation():
    """Test TestGenerationRequest validation errors."""
    with pytest.raises(ValueError, match="code_file_path cannot be empty"):
        TestGenerationRequest(code_file_path="", language="python")

    with pytest.raises(ValueError, match="language cannot be empty"):
        TestGenerationRequest(code_file_path="test.py", language="")


def test_test_generation_request_immutability():
    """Test TestGenerationRequest immutability."""
    request = TestGenerationRequest(
        code_file_path="test.py",
        language="python",
    )

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        request.code_file_path = "new.py"  # type: ignore

    with pytest.raises(AttributeError):
        request.language = "javascript"  # type: ignore
