"""Unit tests for GodAgentMemoryRepository interface."""

import pytest

from src.domain.god_agent.interfaces.memory_repository import IGodAgentMemoryRepository


def test_interface_methods():
    """Test that IGodAgentMemoryRepository interface has required methods."""
    # Check that interface exists and has required methods
    assert hasattr(IGodAgentMemoryRepository, "save_task_timeline")
    assert hasattr(IGodAgentMemoryRepository, "get_task_timeline")
    assert hasattr(IGodAgentMemoryRepository, "save_artifact_ref")
    assert hasattr(IGodAgentMemoryRepository, "get_artifact_refs")


def test_interface_is_protocol():
    """Test that IGodAgentMemoryRepository is a Protocol."""
    from typing import Protocol

    assert issubclass(IGodAgentMemoryRepository, Protocol)
