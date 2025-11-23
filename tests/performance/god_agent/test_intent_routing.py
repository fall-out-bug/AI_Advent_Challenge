"""Performance tests for intent routing."""

import time
from unittest.mock import AsyncMock

import pytest

from src.application.god_agent.services.intent_router_service import IntentRouterService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot


@pytest.mark.asyncio
async def test_intent_routing_performance():
    """Test intent routing performance < 5s."""
    # Setup
    mock_memory_fabric = AsyncMock()
    mock_memory_fabric.get_memory_snapshot = AsyncMock(
        return_value=MemorySnapshot(
            user_id="123",
            profile_summary="",
            conversation_summary="",
            rag_hits=[],
            artifact_refs=[],
        )
    )

    service = IntentRouterService(
        memory_fabric_service=mock_memory_fabric,
        embedding_gateway=None,
    )

    # Measure
    start_time = time.perf_counter()
    intent = await service.route_intent("123", "What is Python?")
    duration = time.perf_counter() - start_time

    # Assert
    assert duration < 5.0, f"Intent routing took {duration}s, expected < 5s"
    assert intent is not None
