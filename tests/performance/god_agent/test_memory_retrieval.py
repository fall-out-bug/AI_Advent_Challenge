"""Performance tests for memory retrieval."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.memory_fabric_service import MemoryFabricService


@pytest.mark.asyncio
async def test_memory_retrieval_performance():
    """Test memory retrieval performance < 150ms."""
    # Setup
    mock_profile_repo = AsyncMock()
    mock_profile_repo.get_user_profile.return_value = None
    mock_memory_repo = AsyncMock()
    mock_memory_repo.get_recent_events.return_value = []
    mock_memory_repo.count_events.return_value = 0

    service = MemoryFabricService(mock_profile_repo, mock_memory_repo)

    # Measure
    start_time = time.perf_counter()
    snapshot = await service.get_memory_snapshot("123")
    duration = (time.perf_counter() - start_time) * 1000  # Convert to ms

    # Assert
    assert duration < 150, f"Memory retrieval took {duration}ms, expected < 150ms"
    assert snapshot is not None
