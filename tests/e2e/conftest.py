"""E2E test fixtures for review pipeline with real services."""

from __future__ import annotations

import os

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.config.settings import get_settings


@pytest.fixture(scope="session")
async def real_mongodb():
    """Real MongoDB connection for E2E tests.

    Purpose:
        Provides connection to test MongoDB database.
        Uses test database name to avoid conflicts.

    Yields:
        MongoDB database instance.

    Note:
        Requires MongoDB running on localhost:27017 or TEST_MONGODB_URL.
        Uses 'ai_challenge_test' database.
        Tests will be skipped if MongoDB is unavailable.
    """
    settings = get_settings()

    configured_test_url = os.getenv("TEST_MONGODB_URL") or settings.mongodb_url
    test_db_name = os.getenv("TEST_MONGODB_DB", "ai_challenge_test")
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    host = os.getenv("MONGODB_HOST", "shared-mongo")
    port = os.getenv("MONGODB_PORT", "27017")
    auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")

    if configured_test_url and not any(
        marker in configured_test_url for marker in ("localhost", "127.0.0.1")
    ):
        mongodb_url = configured_test_url
    else:
        if username and password:
            credentials = f"{username}:{password}@"
        else:
            credentials = ""
        query = f"?authSource={auth_source}" if auth_source else ""
        mongodb_url = f"mongodb://{credentials}{host}:{port}/{test_db_name}{query}"

    if "/" in mongodb_url.rstrip("/"):
        db_name_from_url = mongodb_url.rsplit("/", 1)[-1].split("?")[0]
        if db_name_from_url:
            test_db_name = db_name_from_url

    # Test connection
    try:
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=10000,  # Allow additional time for shared infra
        )
        # Try to connect
        await client.admin.command("ping")
    except Exception as e:
        pytest.skip(f"MongoDB unavailable: {e}")

    # Use test database
    db = client.get_database(test_db_name)

    yield db

    # Cleanup: close connection
    client.close()


@pytest.fixture(autouse=True)
async def cleanup_test_data(real_mongodb):
    """Cleanup test data after each test.

    Purpose:
        Removes test review tasks and sessions created during tests.

    Args:
        real_mongodb: Test MongoDB database.
    """
    yield

    # Cleanup test data
    # Clean up review tasks (CODE_REVIEW type) with test student IDs
    await real_mongodb.long_tasks.delete_many(
        {
            "task_type": "code_review",
            "metadata.student_id": {"$regex": "^test_|^999|^888|^123|^456|^789"},
        }
    )
    # Clean up homework reviews with test repo names
    await real_mongodb.homework_reviews.delete_many(
        {"repo_name": {"$regex": "^test_|^999_|^888_|^123_|^456_|^789_"}}
    )
