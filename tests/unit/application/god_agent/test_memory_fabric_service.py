"""Unit tests for MemoryFabricService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.memory_fabric_service import MemoryFabricService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile


@pytest.fixture
def mock_profile_repo():
    """Mock UserProfileRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_memory_repo():
    """Mock IGodAgentMemoryRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_embedding_gateway():
    """Mock IEmbeddingGateway."""
    gateway = AsyncMock()
    return gateway


@pytest.fixture
def memory_fabric_service(mock_profile_repo, mock_memory_repo):
    """Create MemoryFabricService instance."""
    return MemoryFabricService(
        profile_repo=mock_profile_repo,
        memory_repo=mock_memory_repo,
    )


@pytest.mark.asyncio
async def test_get_memory_snapshot_aggregates_all_sources(
    memory_fabric_service, mock_profile_repo, mock_memory_repo
):
    """Test get_memory_snapshot aggregates profile, memory, RAG hits, artifacts."""
    user_id = "user_123"

    # Setup mocks
    profile = UserProfile.create_default_profile(user_id)
    mock_profile_repo.get.return_value = profile

    events = [UserMemoryEvent.create_user_event(user_id, "Hello")]
    memory_slice = MemorySlice(events=events, summary="Previous chat")
    mock_memory_repo.get_recent_events.return_value = events
    mock_memory_repo.count_events.return_value = 1

    # Mock artifact refs - return different values for different types
    async def mock_get_artifact_refs(user_id: str, artifact_type: str):
        if artifact_type == "code_diff":
            return ["commit_hash_1"]
        return []

    mock_memory_repo.get_artifact_refs = AsyncMock(side_effect=mock_get_artifact_refs)

    # Get snapshot
    snapshot = await memory_fabric_service.get_memory_snapshot(user_id)

    assert snapshot.user_id == user_id
    assert snapshot.profile_summary is not None
    assert snapshot.conversation_summary is not None
    assert len(snapshot.artifact_refs) == 1


@pytest.mark.asyncio
async def test_get_memory_snapshot_with_rag_hits(
    memory_fabric_service, mock_profile_repo, mock_memory_repo
):
    """Test get_memory_snapshot includes RAG hits."""
    user_id = "user_123"

    profile = UserProfile.create_default_profile(user_id)
    mock_profile_repo.get.return_value = profile

    events = []
    mock_memory_repo.get_recent_events.return_value = events
    mock_memory_repo.count_events.return_value = 0
    mock_memory_repo.get_artifact_refs.return_value = []

    # Mock RAG hits (will be passed via method parameter or service state)
    snapshot = await memory_fabric_service.get_memory_snapshot(
        user_id, rag_hits=[{"chunk_id": "chunk1", "score": 0.9}]
    )

    assert len(snapshot.rag_hits) == 1
    assert snapshot.rag_hits[0]["chunk_id"] == "chunk1"


@pytest.mark.asyncio
async def test_update_memory_handles_events(memory_fabric_service, mock_memory_repo):
    """Test update_memory handles new events."""
    user_id = "user_123"
    event = UserMemoryEvent.create_user_event(user_id, "New message")

    # Mock count_events to return low number (no compression)
    mock_memory_repo.count_events.return_value = 10

    await memory_fabric_service.update_memory(user_id, event)

    mock_memory_repo.append_events.assert_called_once_with([event])


@pytest.mark.asyncio
async def test_compress_memory_triggers_when_over_50_events(
    memory_fabric_service, mock_memory_repo, mock_profile_repo
):
    """Test compress_memory triggers when >50 events, keeps 20."""
    user_id = "user_123"

    # Mock 60 events
    mock_memory_repo.count_events.return_value = 60
    events = [
        UserMemoryEvent.create_user_event(user_id, f"Message {i}") for i in range(20)
    ]
    mock_memory_repo.get_recent_events.return_value = events

    profile = UserProfile.create_default_profile(user_id)
    mock_profile_repo.get.return_value = profile

    await memory_fabric_service.compress_memory(user_id)

    # Should compress: keep 20, delete rest
    mock_memory_repo.compress.assert_called_once()
    call_kwargs = mock_memory_repo.compress.call_args.kwargs
    assert call_kwargs["keep_last_n"] == 20  # keep_last_n = 20


@pytest.mark.asyncio
async def test_compress_memory_skips_when_under_50_events(
    memory_fabric_service, mock_memory_repo
):
    """Test compress_memory skips when <=50 events."""
    user_id = "user_123"

    # Mock 30 events
    mock_memory_repo.count_events.return_value = 30

    await memory_fabric_service.compress_memory(user_id)

    # Should not compress
    mock_memory_repo.compress.assert_not_called()


@pytest.mark.asyncio
async def test_get_memory_snapshot_handles_missing_profile(
    memory_fabric_service, mock_profile_repo, mock_memory_repo
):
    """Test get_memory_snapshot handles missing profile gracefully."""
    user_id = "user_123"

    # Profile not found
    mock_profile_repo.get.return_value = None

    events = []
    mock_memory_repo.get_recent_events.return_value = events
    mock_memory_repo.count_events.return_value = 0

    async def mock_get_artifact_refs_empty(user_id: str, artifact_type: str):
        return []

    mock_memory_repo.get_artifact_refs = AsyncMock(
        side_effect=mock_get_artifact_refs_empty
    )

    snapshot = await memory_fabric_service.get_memory_snapshot(user_id)

    assert snapshot.user_id == user_id
    assert snapshot.profile_summary == ""  # Empty when no profile
