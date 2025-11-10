"""Unit tests for application use cases."""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.generate_code import GenerateCodeUseCase
from src.application.use_cases.review_code import ReviewCodeUseCase
from src.domain.entities.agent_task import TaskType


@pytest.fixture
def mock_agent_repo() -> AsyncMock:
    """Create mock agent repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_model_repo() -> AsyncMock:
    """Create mock model repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_model_client() -> AsyncMock:
    """Create mock model client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="def hello(): pass")
    return client


@pytest.mark.asyncio
async def test_generate_code_use_case(
    mock_agent_repo, mock_model_repo, mock_model_client
) -> None:
    """Test code generation use case."""
    use_case = GenerateCodeUseCase(
        agent_repository=mock_agent_repo,
        model_repository=mock_model_repo,
        model_client=mock_model_client,
    )

    task = await use_case.execute(
        prompt="Create a hello function",
        agent_name="test_agent",
    )

    assert task is not None
    assert task.prompt == "Create a hello function"
    assert task.agent_name == "test_agent"


@pytest.mark.asyncio
async def test_review_code_use_case(
    mock_agent_repo, mock_model_repo, mock_model_client
) -> None:
    """Test code review use case."""
    mock_model_client.generate = AsyncMock(return_value="Code quality is good.")

    use_case = ReviewCodeUseCase(
        agent_repository=mock_agent_repo,
        model_repository=mock_model_repo,
        model_client=mock_model_client,
    )

    task = await use_case.execute(
        code="def add(a, b): return a + b",
        agent_name="test_agent",
    )

    assert task is not None
    assert task.task_type == TaskType.CODE_REVIEW
    assert "add" in task.prompt.lower()


def test_generate_code_id_generation() -> None:
    """Test unique ID generation."""
    from src.application.use_cases.generate_code import GenerateCodeUseCase

    use_case = GenerateCodeUseCase(
        agent_repository=AsyncMock(),
        model_repository=AsyncMock(),
        model_client=AsyncMock(),
    )

    # Generate IDs and check they're different
    id1 = use_case._generate_id()
    id2 = use_case._generate_id()
    assert id1 != id2
    assert isinstance(id1, str)
    assert len(id1) == 36  # UUID length
