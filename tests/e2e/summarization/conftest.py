"""E2E test fixtures for summarization system with real services."""

from __future__ import annotations

import os

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.clients.llm_client import get_llm_client
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient


@pytest.fixture(scope="session")
async def real_mongodb():
    """Real MongoDB connection for E2E tests.

    Purpose:
        Provides connection to test MongoDB database.
        Uses test database name to avoid conflicts.

    Yields:
        MongoDB database instance.

    Note:
        Requires MONGODB_URL environment variable or default localhost:27017.
        Uses 'ai_challenge_test' database.
    """
    settings = get_settings()
    mongodb_url = os.getenv("TEST_MONGODB_URL", settings.mongodb_url)

    # Use test database
    client = AsyncIOMotorClient(mongodb_url)
    db = client.get_database("ai_challenge_test")

    yield db

    # Cleanup: close connection
    client.close()


@pytest.fixture(scope="session")
async def real_llm_client():
    """Real LLM client for E2E tests.

    Purpose:
        Provides ResilientLLMClient configured for testing.
        Checks LLM_URL environment variable.

    Yields:
        ResilientLLMClient instance.

    Note:
        Requires LLM_URL environment variable or will use fallback.
        Tests will be skipped if LLM_URL not configured.
    """
    llm_url = os.getenv("TEST_LLM_URL", os.getenv("LLM_URL", ""))

    if not llm_url:
        pytest.skip("LLM_URL not configured for E2E tests")

    client = ResilientLLMClient(url=llm_url)

    # Test connection
    try:
        await client.generate("test", max_tokens=10)
    except Exception as e:
        pytest.skip(f"LLM service unavailable: {e}")

    yield client


@pytest.fixture(scope="session")
def telegram_test_channel():
    """Test Telegram channel configuration.

    Purpose:
        Provides test channel username for E2E tests.

    Returns:
        Dictionary with test channel configuration:
        - username: Channel username
        - api_id: Telegram API ID (if available)
        - api_hash: Telegram API hash (if available)

    Note:
        Requires TEST_CHANNEL_USERNAME environment variable.
        Tests will be skipped if not configured.
    """
    channel_username = os.getenv("TEST_CHANNEL_USERNAME", "")

    if not channel_username:
        pytest.skip("TEST_CHANNEL_USERNAME not configured for E2E tests")

    return {
        "username": channel_username.lstrip("@"),
        "api_id": os.getenv("TELEGRAM_API_ID"),
        "api_hash": os.getenv("TELEGRAM_API_HASH"),
    }


@pytest.fixture(scope="session")
def test_user_id():
    """Test user ID for E2E tests.

    Returns:
        Test user ID (default: 12345, can be overridden via TEST_USER_ID env var).
    """
    return int(os.getenv("TEST_USER_ID", "12345"))


@pytest.fixture(autouse=True)
async def cleanup_test_data(real_mongodb):
    """Cleanup test data after each test.

    Purpose:
        Removes test posts and channels created during tests.

    Args:
        real_mongodb: Test MongoDB database.
    """
    yield

    # Cleanup test data
    # Note: Be careful not to delete production data
    # Only delete data with test markers
    await real_mongodb.posts.delete_many({"test_data": True})
    await real_mongodb.channels.delete_many({"test_data": True})
    await real_mongodb.tasks.delete_many({"test_data": True})
