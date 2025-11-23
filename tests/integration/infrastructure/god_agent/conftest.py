"""Test fixtures for God Agent integration tests."""

import pytest

from src.infrastructure.god_agent.repositories.god_agent_memory_repository import (
    GodAgentMemoryRepository,
)


@pytest.fixture
def god_agent_memory_repo(real_mongodb):
    """Provide GodAgentMemoryRepository instance.

    Args:
        real_mongodb: Real MongoDB database fixture from conftest.

    Returns:
        GodAgentMemoryRepository instance.
    """
    # Access client from database
    client = real_mongodb.client
    return GodAgentMemoryRepository(client, real_mongodb.name)
