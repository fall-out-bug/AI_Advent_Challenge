"""Unit tests for MemorySnapshot entity."""

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot


def test_memory_snapshot_creation():
    """Test MemorySnapshot creation."""
    snapshot = MemorySnapshot(
        user_id="user1",
        profile_summary="User profile summary",
        conversation_summary="Recent conversation summary",
        rag_hits=[],
        artifact_refs=[],
    )

    assert snapshot.user_id == "user1"
    assert snapshot.profile_summary == "User profile summary"
    assert snapshot.conversation_summary == "Recent conversation summary"
    assert snapshot.rag_hits == []
    assert snapshot.artifact_refs == []


def test_memory_snapshot_compression():
    """Test MemorySnapshot compression logic."""
    snapshot = MemorySnapshot(
        user_id="user1",
        profile_summary="User profile summary",
        conversation_summary="Long conversation summary " * 100,  # Large summary
        rag_hits=[],
        artifact_refs=[],
    )

    # Compression should truncate long summaries
    compressed = snapshot.compress(max_length=100)
    assert len(compressed.conversation_summary) <= 100
    assert compressed.user_id == snapshot.user_id


def test_memory_snapshot_with_rag_hits():
    """Test MemorySnapshot with RAG hits."""
    rag_hits = [
        {"chunk_id": "chunk1", "score": 0.9},
        {"chunk_id": "chunk2", "score": 0.8},
    ]
    snapshot = MemorySnapshot(
        user_id="user1",
        profile_summary="Profile",
        conversation_summary="Conversation",
        rag_hits=rag_hits,
        artifact_refs=[],
    )

    assert len(snapshot.rag_hits) == 2
    assert snapshot.rag_hits[0]["chunk_id"] == "chunk1"
