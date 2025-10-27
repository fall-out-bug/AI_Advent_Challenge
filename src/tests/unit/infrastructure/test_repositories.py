"""Unit tests for infrastructure repositories."""

import pytest
from pathlib import Path
import tempfile
import json

from src.infrastructure.repositories.json_agent_repository import (
    JsonAgentRepository,
)
from src.domain.entities.agent_task import AgentTask, TaskStatus, TaskType


@pytest.fixture
def temp_storage_path() -> Path:
    """Create temporary storage path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        return Path(f.name)


@pytest.fixture
def repository(temp_storage_path: Path) -> JsonAgentRepository:
    """Create repository instance."""
    repo = JsonAgentRepository(temp_storage_path)
    yield repo
    if temp_storage_path.exists():
        temp_storage_path.unlink()


@pytest.mark.asyncio
async def test_save_task(repository: JsonAgentRepository) -> None:
    """Test saving a task."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Test prompt",
    )
    await repository.save(task)
    assert repository.storage_path.exists()


@pytest.mark.asyncio
async def test_get_by_id(repository: JsonAgentRepository) -> None:
    """Test getting task by ID."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Test prompt",
    )
    await repository.save(task)

    retrieved = await repository.get_by_id("test_1")
    assert retrieved is not None
    assert retrieved.task_id == "test_1"


@pytest.mark.asyncio
async def test_get_all(repository: JsonAgentRepository) -> None:
    """Test getting all tasks."""
    task1 = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Test prompt 1",
    )
    task2 = AgentTask(
        task_id="test_2",
        task_type=TaskType.CODE_REVIEW,
        status=TaskStatus.PENDING,
        prompt="Test prompt 2",
    )

    await repository.save(task1)
    await repository.save(task2)

    all_tasks = await repository.get_all()
    assert len(all_tasks) == 2


@pytest.mark.asyncio
async def test_delete_task(repository: JsonAgentRepository) -> None:
    """Test deleting a task."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Test prompt",
    )
    await repository.save(task)

    result = await repository.delete("test_1")
    assert result is True

    retrieved = await repository.get_by_id("test_1")
    assert retrieved is None


@pytest.mark.asyncio
async def test_exists_check(repository: JsonAgentRepository) -> None:
    """Test existence check."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Test prompt",
    )
    await repository.save(task)

    assert await repository.exists("test_1") is True
    assert await repository.exists("nonexistent") is False
