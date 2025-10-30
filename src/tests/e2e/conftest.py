"""Shared fixtures for E2E tests."""

import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.database.mongo import get_db, close_client


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    """Set test database environment variables."""
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv("MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))


@pytest.fixture(autouse=True)
async def _cleanup_db():
    """Clean up database before and after each test."""
    db = await get_db()
    await db.tasks.delete_many({})
    await db.channels.delete_many({})
    yield
    await db.tasks.delete_many({})
    await db.channels.delete_many({})
    await close_client()


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_telegram_bot():
    """Create mock Telegram bot for testing."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=1))
    return bot


@pytest.fixture
def unique_user_id():
    """Generate unique user ID for test isolation."""
    import random
    return random.randint(100000, 999999)


@pytest.fixture
def task_factory():
    """Factory function for creating test tasks."""
    def _create_task(user_id: int, title: str = "Test Task", **kwargs):
        return {
            "user_id": user_id,
            "title": title,
            "description": kwargs.get("description", ""),
            "deadline": kwargs.get("deadline"),
            "priority": kwargs.get("priority", "medium"),
            "tags": kwargs.get("tags", []),
            **kwargs
        }
    return _create_task


@pytest.fixture
def channel_factory():
    """Factory function for creating test channels."""
    def _create_channel(user_id: int, channel_username: str = "test_channel", **kwargs):
        return {
            "user_id": user_id,
            "channel_username": channel_username,
            "tags": kwargs.get("tags", []),
            "active": kwargs.get("active", True),
            **kwargs
        }
    return _create_channel

