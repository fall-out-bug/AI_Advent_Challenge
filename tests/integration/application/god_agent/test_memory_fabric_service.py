"""Integration tests for MemoryFabricService with MongoDB."""

import time

import pytest

from src.application.god_agent.services.memory_fabric_service import MemoryFabricService
from src.domain.personalization.user_memory_event import UserMemoryEvent
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
def memory_fabric_service(real_mongodb):
    """Create MemoryFabricService with real MongoDB."""
    client = real_mongodb.client
    profile_repo = MongoUserProfileRepository(client, real_mongodb.name)
    memory_repo = GodAgentMemoryRepository(client, real_mongodb.name)
    return MemoryFabricService(
        profile_repo=profile_repo,
        memory_repo=memory_repo,
    )


@pytest.mark.asyncio
async def test_get_memory_snapshot_latency_under_150ms(
    memory_fabric_service,
):
    """Test get_memory_snapshot retrieval latency < 150ms."""
    user_id = "test_user_latency"

    start_time = time.time()
    snapshot = await memory_fabric_service.get_memory_snapshot(user_id)
    elapsed_ms = (time.time() - start_time) * 1000

    assert elapsed_ms < 150, f"Latency {elapsed_ms}ms exceeds 150ms threshold"
    assert snapshot.user_id == user_id


@pytest.mark.asyncio
async def test_get_memory_snapshot_with_real_data(
    memory_fabric_service,
):
    """Test get_memory_snapshot with real MongoDB data."""
    user_id = "test_user_real"

    # Add some events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(5)
    ]
    for event in events:
        await memory_fabric_service.update_memory(user_id, event)

    # Get snapshot
    snapshot = await memory_fabric_service.get_memory_snapshot(user_id)

    assert snapshot.user_id == user_id
    assert len(snapshot.artifact_refs) >= 0
    assert snapshot.profile_summary is not None


@pytest.mark.asyncio
async def test_compress_memory_integration(memory_fabric_service):
    """Test compress_memory with real MongoDB."""
    user_id = "test_user_compress"

    # Add 60 events
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(60)
    ]
    await memory_fabric_service.memory_repo.append_events(events)

    # Compress
    await memory_fabric_service.compress_memory(user_id)

    # Verify only 20 remain
    count = await memory_fabric_service.memory_repo.count_events(user_id)
    assert count == 20
