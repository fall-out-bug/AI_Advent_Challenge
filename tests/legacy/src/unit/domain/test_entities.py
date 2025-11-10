"""Unit tests for domain entities."""

from src.domain.entities.agent_task import AgentTask, TaskStatus, TaskType


def test_agent_task_creation() -> None:
    """Test agent task creation."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Create a function",
    )
    assert task.task_id == "test_1"
    assert task.task_type == TaskType.CODE_GENERATION
    assert task.status == TaskStatus.PENDING


def test_agent_task_mark_in_progress() -> None:
    """Test marking task as in progress."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Create a function",
    )
    task.mark_in_progress()
    assert task.status == TaskStatus.IN_PROGRESS


def test_agent_task_mark_completed() -> None:
    """Test marking task as completed."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.IN_PROGRESS,
        prompt="Create a function",
    )
    task.mark_completed("def hello(): pass")
    assert task.status == TaskStatus.COMPLETED
    assert task.response == "def hello(): pass"


def test_agent_task_mark_failed() -> None:
    """Test marking task as failed."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.IN_PROGRESS,
        prompt="Create a function",
    )
    task.mark_failed()
    assert task.status == TaskStatus.FAILED


def test_agent_task_is_completed() -> None:
    """Test is_completed check."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.COMPLETED,
        prompt="Create a function",
    )
    assert task.is_completed()
    assert not task.is_failed()


def test_agent_task_add_metadata() -> None:
    """Test adding metadata to task."""
    task = AgentTask(
        task_id="test_1",
        task_type=TaskType.CODE_GENERATION,
        status=TaskStatus.PENDING,
        prompt="Create a function",
    )
    task.add_metadata("key", "value")
    assert task.metadata["key"] == "value"
