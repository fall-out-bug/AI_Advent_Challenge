"""Unit tests for TestCase entity."""

import pytest

from src.domain.test_agent.entities.test_case import TestCase


def test_test_case_creation_with_name():
    """Test TestCase creation with name."""
    test_case = TestCase(
        name="test_calculate_sum",
        code="def test_calculate_sum(): assert calculate_sum(1, 2) == 3",
    )

    assert test_case.name == "test_calculate_sum"
    assert "calculate_sum" in test_case.code
    assert test_case.metadata == {}


def test_test_case_creation_with_code():
    """Test TestCase creation with code."""
    code = """
def test_example():
    assert True
"""
    test_case = TestCase(
        name="test_example",
        code=code,
    )

    assert test_case.name == "test_example"
    assert test_case.code == code


def test_test_case_metadata():
    """Test TestCase metadata handling."""
    metadata = {"type": "unit", "coverage": "high"}
    test_case = TestCase(
        name="test_metadata",
        code="def test_metadata(): pass",
        metadata=metadata,
    )

    assert test_case.metadata == metadata
    assert test_case.metadata["type"] == "unit"
    assert test_case.metadata["coverage"] == "high"


def test_test_case_validation():
    """Test TestCase validation errors."""
    with pytest.raises(ValueError, match="name cannot be empty"):
        TestCase(name="", code="def test(): pass")

    with pytest.raises(ValueError, match="code cannot be None"):
        TestCase(name="test", code=None)  # type: ignore
