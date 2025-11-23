"""Unit tests for IntentRouterService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.intent_router_service import IntentRouterService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.value_objects.intent import Intent, IntentType


@pytest.fixture
def mock_memory_fabric_service():
    """Mock IMemoryFabricService."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_embedding_gateway():
    """Mock IEmbeddingGateway."""
    gateway = AsyncMock()
    return gateway


@pytest.fixture
def intent_router_service(mock_memory_fabric_service, mock_embedding_gateway):
    """Create IntentRouterService instance."""
    return IntentRouterService(
        memory_fabric_service=mock_memory_fabric_service,
        embedding_gateway=mock_embedding_gateway,
    )


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="user_123",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="Recent chat about Python",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.mark.asyncio
async def test_route_intent_classifies_concierge(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent classifies concierge intent."""
    user_id = "user_123"
    message = "Hello, how are you?"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    assert intent.intent_type == IntentType.CONCIERGE
    assert 0.0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_classifies_research(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent classifies research intent."""
    user_id = "user_123"
    message = "What is Python? Explain how it works."

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    assert intent.intent_type == IntentType.RESEARCH
    assert 0.0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_classifies_build(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent classifies build intent."""
    user_id = "user_123"
    message = "Create a function that calculates fibonacci numbers"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    assert intent.intent_type == IntentType.BUILD
    assert 0.0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_classifies_review(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent classifies review intent."""
    user_id = "user_123"
    message = "Review my code in commit abc123"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    assert intent.intent_type == IntentType.REVIEW
    assert 0.0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_classifies_ops(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent classifies ops intent."""
    user_id = "user_123"
    message = "Check system status and metrics"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    assert intent.intent_type == IntentType.OPS
    assert 0.0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_fallback_to_concierge_low_confidence(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent falls back to concierge when confidence < 0.6."""
    user_id = "user_123"
    message = "Some ambiguous message that doesn't match any pattern"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)

    # Should fallback to concierge if confidence < 0.6
    if intent.confidence < 0.6:
        assert intent.intent_type == IntentType.CONCIERGE


@pytest.mark.asyncio
async def test_get_confidence_returns_float(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test get_confidence returns confidence value."""
    user_id = "user_123"
    message = "Hello"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    intent = await intent_router_service.route_intent(user_id, message)
    confidence = intent_router_service.get_confidence(intent)

    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_route_intent_uses_memory_snapshot(
    intent_router_service, mock_memory_fabric_service, sample_memory_snapshot
):
    """Test route_intent uses memory snapshot for context."""
    user_id = "user_123"
    message = "Continue our previous discussion"

    mock_memory_fabric_service.get_memory_snapshot.return_value = sample_memory_snapshot

    await intent_router_service.route_intent(user_id, message)

    mock_memory_fabric_service.get_memory_snapshot.assert_called_once_with(user_id)
