"""Unit tests for ConciergeSkillAdapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.god_agent.adapters.concierge_skill_adapter import (
    ConciergeSkillAdapter,
)


@pytest.fixture
def mock_personalized_reply_use_case():
    """Mock PersonalizedReplyUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def concierge_adapter(mock_personalized_reply_use_case):
    """Create ConciergeSkillAdapter instance."""
    return ConciergeSkillAdapter(
        personalized_reply_use_case=mock_personalized_reply_use_case
    )


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="user_123",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="Recent chat",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.mark.asyncio
async def test_execute_calls_personalized_reply_use_case(
    concierge_adapter, mock_personalized_reply_use_case, sample_memory_snapshot
):
    """Test execute calls PersonalizedReplyUseCase."""
    from src.application.personalization.dtos import (
        PersonalizedReplyInput,
        PersonalizedReplyOutput,
    )

    # Setup mock
    mock_output = PersonalizedReplyOutput(
        reply="Hello, how can I help you?",
        used_persona=True,
        memory_events_used=5,
        compressed=False,
    )
    mock_personalized_reply_use_case.execute.return_value = mock_output

    # Execute
    input_data = {"message": "Hello", "user_id": "user_123"}
    result = await concierge_adapter.execute(input_data, sample_memory_snapshot)

    # Verify
    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "reply" in result.output
    mock_personalized_reply_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_use_case_error(
    concierge_adapter, mock_personalized_reply_use_case, sample_memory_snapshot
):
    """Test execute handles PersonalizedReplyUseCase errors."""
    # Setup mock to raise error
    mock_personalized_reply_use_case.execute.side_effect = Exception("Use case error")

    # Execute
    input_data = {"message": "Hello", "user_id": "user_123"}
    result = await concierge_adapter.execute(input_data, sample_memory_snapshot)

    # Should return failure result
    assert result.status == SkillResultStatus.FAILURE
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.asyncio
async def test_get_skill_id_returns_concierge(
    concierge_adapter,
):
    """Test get_skill_id returns concierge."""
    skill_id = concierge_adapter.get_skill_id()

    assert skill_id == SkillType.CONCIERGE.value


@pytest.mark.asyncio
async def test_execute_creates_personalized_reply_input(
    concierge_adapter, mock_personalized_reply_use_case, sample_memory_snapshot
):
    """Test execute creates PersonalizedReplyInput correctly."""
    from src.application.personalization.dtos import (
        PersonalizedReplyInput,
        PersonalizedReplyOutput,
    )

    mock_output = PersonalizedReplyOutput(
        reply="Response",
        used_persona=True,
        memory_events_used=0,
        compressed=False,
    )
    mock_personalized_reply_use_case.execute.return_value = mock_output

    input_data = {"message": "Hello", "user_id": "user_123", "source": "telegram"}
    await concierge_adapter.execute(input_data, sample_memory_snapshot)

    # Verify PersonalizedReplyInput was created correctly
    call_args = mock_personalized_reply_use_case.execute.call_args
    assert call_args is not None
    input_obj = call_args[0][0]
    assert isinstance(input_obj, PersonalizedReplyInput)
    assert input_obj.user_id == "user_123"
    assert input_obj.text == "Hello"
