"""Integration tests for IntentRouterService."""

import time

import pytest

from src.application.god_agent.services.intent_router_service import IntentRouterService
from src.application.god_agent.services.memory_fabric_service import MemoryFabricService
from src.domain.god_agent.value_objects.intent import IntentType
from src.infrastructure.god_agent.repositories.god_agent_memory_repository import (
    GodAgentMemoryRepository,
)
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)


@pytest.fixture
def intent_router_service(real_mongodb):
    """Create IntentRouterService with real MongoDB."""
    client = real_mongodb.client
    profile_repo = MongoUserProfileRepository(client, real_mongodb.name)
    memory_repo = GodAgentMemoryRepository(client, real_mongodb.name)
    memory_fabric_service = MemoryFabricService(
        profile_repo=profile_repo,
        memory_repo=memory_repo,
    )
    # Mock embedding gateway for now (will be implemented later)
    from unittest.mock import AsyncMock

    embedding_gateway = AsyncMock()
    return IntentRouterService(
        memory_fabric_service=memory_fabric_service,
        embedding_gateway=embedding_gateway,
    )


@pytest.mark.asyncio
async def test_route_intent_response_time_under_5s(intent_router_service):
    """Test route_intent response time < 5s."""
    user_id = "test_user_latency"
    message = "Hello, how are you?"

    start_time = time.time()
    intent = await intent_router_service.route_intent(user_id, message)
    elapsed_seconds = time.time() - start_time

    assert (
        elapsed_seconds < 5.0
    ), f"Response time {elapsed_seconds}s exceeds 5s threshold"
    assert intent.intent_type in IntentType


@pytest.mark.asyncio
async def test_route_intent_fallback_to_concierge_low_confidence_integration(
    intent_router_service,
):
    """Test route_intent falls back to concierge when confidence < 0.6 (integration)."""
    user_id = "test_user_fallback"
    message = "Some very ambiguous message that doesn't match clear patterns"

    intent = await intent_router_service.route_intent(user_id, message)

    # Should fallback to concierge if confidence < 0.6
    if intent.confidence < 0.6:
        assert intent.intent_type == IntentType.CONCIERGE
