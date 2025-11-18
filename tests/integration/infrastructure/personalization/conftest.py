"""Test fixtures for personalization integration tests."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)


@pytest.fixture
def profile_repo(real_mongodb):
    """Provide MongoUserProfileRepository instance.

    Args:
        real_mongodb: Real MongoDB database fixture from conftest.

    Returns:
        MongoUserProfileRepository instance.
    """
    # Access client from database
    client = real_mongodb.client
    return MongoUserProfileRepository(client, real_mongodb.name)


@pytest.fixture
def memory_repo(real_mongodb):
    """Provide MongoUserMemoryRepository instance.

    Args:
        real_mongodb: Real MongoDB database fixture from conftest.

    Returns:
        MongoUserMemoryRepository instance.
    """
    # Access client from database
    client = real_mongodb.client
    return MongoUserMemoryRepository(client, real_mongodb.name)
