"""Integration tests for ConciergeSkillAdapter."""

import pytest

from src.application.personalization.personalization_service import (
    PersonalizationServiceImpl,
)
from src.application.personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase,
)
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.infrastructure.god_agent.adapters.concierge_skill_adapter import (
    ConciergeSkillAdapter,
)
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)


@pytest.fixture
def concierge_adapter(real_mongodb, llm_client):
    """Create ConciergeSkillAdapter with real dependencies."""
    client = real_mongodb.client
    profile_repo = MongoUserProfileRepository(client, real_mongodb.name)
    memory_repo = MongoUserMemoryRepository(client, real_mongodb.name)
    personalization_service = PersonalizationServiceImpl(profile_repo)
    personalized_reply_use_case = PersonalizedReplyUseCase(
        personalization_service=personalization_service,
        memory_repo=memory_repo,
        profile_repo=profile_repo,
        llm_client=llm_client,
    )
    return ConciergeSkillAdapter(
        personalized_reply_use_case=personalized_reply_use_case
    )


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="test_user_integration",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="Recent chat",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.mark.asyncio
async def test_end_to_end_concierge_flow(concierge_adapter, sample_memory_snapshot):
    """Test end-to-end concierge flow (text message → personalized response)."""
    input_data = {
        "message": "Hello, how are you?",
        "user_id": sample_memory_snapshot.user_id,
        "source": "telegram",
    }

    result = await concierge_adapter.execute(input_data, sample_memory_snapshot)

    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "reply" in result.output
    assert len(result.output["reply"]) > 0
