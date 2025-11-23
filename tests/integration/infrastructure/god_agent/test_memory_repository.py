"""Integration tests for GodAgentMemoryRepository with MongoDB."""

import pytest

from src.infrastructure.god_agent.repositories.god_agent_memory_repository import (
    GodAgentMemoryRepository,
)


@pytest.mark.asyncio
async def test_save_and_get_task_timeline(god_agent_memory_repo):
    """Test saving and retrieving task timeline."""
    user_id = "test_user_123"
    task_id = "task_456"
    timeline = {
        "task_id": task_id,
        "steps": [
            {"step_id": "step1", "status": "completed"},
            {"step_id": "step2", "status": "running"},
        ],
        "created_at": "2025-01-27T10:00:00Z",
    }

    # Save timeline
    await god_agent_memory_repo.save_task_timeline(user_id, task_id, timeline)

    # Retrieve timeline
    retrieved = await god_agent_memory_repo.get_task_timeline(user_id, task_id)

    assert retrieved is not None
    assert retrieved["task_id"] == task_id
    assert len(retrieved["steps"]) == 2
    assert retrieved["steps"][0]["step_id"] == "step1"


@pytest.mark.asyncio
async def test_get_task_timeline_not_found(god_agent_memory_repo):
    """Test getting non-existent task timeline returns None."""
    user_id = "test_user_123"
    task_id = "non_existent_task"

    retrieved = await god_agent_memory_repo.get_task_timeline(user_id, task_id)

    assert retrieved is None


@pytest.mark.asyncio
async def test_save_and_get_artifact_refs(god_agent_memory_repo):
    """Test saving and retrieving artifact references."""
    user_id = "test_user_123"
    artifact_type = "code_diff"
    artifact_ref = "commit_hash_abc123"

    # Save artifact ref
    await god_agent_memory_repo.save_artifact_ref(user_id, artifact_type, artifact_ref)

    # Retrieve artifact refs
    refs = await god_agent_memory_repo.get_artifact_refs(user_id, artifact_type)

    assert len(refs) == 1
    assert refs[0] == artifact_ref


@pytest.mark.asyncio
async def test_multiple_artifact_refs(god_agent_memory_repo):
    """Test saving and retrieving multiple artifact references."""
    user_id = "test_user_123"
    artifact_type = "code_diff"

    # Save multiple refs
    refs_to_save = ["commit_hash_1", "commit_hash_2", "commit_hash_3"]
    for ref in refs_to_save:
        await god_agent_memory_repo.save_artifact_ref(user_id, artifact_type, ref)

    # Retrieve all refs
    retrieved = await god_agent_memory_repo.get_artifact_refs(user_id, artifact_type)

    assert len(retrieved) == 3
    assert all(ref in retrieved for ref in refs_to_save)


@pytest.mark.asyncio
async def test_get_artifact_refs_empty(god_agent_memory_repo):
    """Test getting artifact refs when none exist returns empty list."""
    user_id = "test_user_123"
    artifact_type = "code_diff"

    refs = await god_agent_memory_repo.get_artifact_refs(user_id, artifact_type)

    assert refs == []


@pytest.mark.asyncio
async def test_multiple_users_isolated(god_agent_memory_repo):
    """Test that task timelines and artifact refs are isolated per user."""
    user_id_1 = "test_user_1"
    user_id_2 = "test_user_2"
    task_id = "task_123"

    # Save timeline for user 1
    timeline_1 = {"task_id": task_id, "user": "user_1"}
    await god_agent_memory_repo.save_task_timeline(user_id_1, task_id, timeline_1)

    # Save timeline for user 2
    timeline_2 = {"task_id": task_id, "user": "user_2"}
    await god_agent_memory_repo.save_task_timeline(user_id_2, task_id, timeline_2)

    # Retrieve for user 1
    retrieved_1 = await god_agent_memory_repo.get_task_timeline(user_id_1, task_id)
    assert retrieved_1["user"] == "user_1"

    # Retrieve for user 2
    retrieved_2 = await god_agent_memory_repo.get_task_timeline(user_id_2, task_id)
    assert retrieved_2["user"] == "user_2"


@pytest.mark.asyncio
async def test_no_breaking_changes_to_user_memory_repo(god_agent_memory_repo):
    """Test that GodAgentMemoryRepository doesn't break UserMemoryRepository functionality."""
    from src.domain.personalization.user_memory_event import UserMemoryEvent

    user_id = "test_user_123"

    # Test that we can still use UserMemoryRepository methods
    events = [UserMemoryEvent.create_user_event(user_id, "Hello")]
    await god_agent_memory_repo.append_events(events)

    retrieved = await god_agent_memory_repo.get_recent_events(user_id, limit=10)
    assert len(retrieved) == 1
    assert retrieved[0].content == "Hello"
