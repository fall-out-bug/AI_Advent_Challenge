"""Integration tests for code generator.

Testing with real-like scenarios following the Zen of Python.
"""

import pytest
from unittest.mock import AsyncMock

from src.domain.messaging.message_schema import CodeGenerationRequest


@pytest.mark.asyncio
async def test_end_to_end_generation():
    """Test end-to-end code generation workflow."""
    # This would test the full integration once we implement
    # the actual code generator agent
    pass


@pytest.mark.asyncio
async def test_generation_with_custom_requirements():
    """Test generation with custom requirements."""
    request = CodeGenerationRequest(
        task_description="Create a sorting function",
        language="python",
        requirements=["use built-in sort", "add type hints", "include docstring"],
        max_tokens=2000,
        model_name="starcoder",
    )

    assert request.requirements == [
        "use built-in sort",
        "add type hints",
        "include docstring",
    ]
    assert request.max_tokens == 2000


@pytest.mark.asyncio
async def test_generation_different_languages():
    """Test generation for different languages."""
    python_request = CodeGenerationRequest(
        task_description="Create a function",
        language="python",
    )

    javascript_request = CodeGenerationRequest(
        task_description="Create a function",
        language="javascript",
    )

    assert python_request.language == "python"
    assert javascript_request.language == "javascript"


@pytest.mark.asyncio
async def test_generation_with_defaults():
    """Test generation with default values."""
    request = CodeGenerationRequest(task_description="Test")

    assert request.language == "python"
    assert request.model_name == "starcoder"
    assert request.max_tokens == 1000
    assert request.requirements == []
