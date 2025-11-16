"""Shared pytest fixtures for testing."""

import asyncio
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import httpx
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient

from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo_client_factory import MongoClientFactory
from src.infrastructure.repositories.json_conversation_repository import (
    JsonConversationRepository,
)


@pytest.fixture
def mock_unified_client():
    """Create mock unified client for testing.

    Returns:
        Mock unified client with async methods
    """
    client = AsyncMock()
    client.check_availability = AsyncMock(return_value=True)
    client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"primary_goal": "test", "confidence": 0.9}',
            total_tokens=100,
            input_tokens=50,
            response_tokens=50,
        )
    )
    return client


@pytest.fixture
def conversation_repo(tmp_path):
    """Create conversation repository with temporary storage.

    Args:
        tmp_path: Temporary directory provided by pytest

    Returns:
        JsonConversationRepository instance
    """
    path = tmp_path / "test_conversations.json"
    repo = JsonConversationRepository(path)
    return repo


@pytest.fixture
async def mock_http_server():
    """Create mock HTTP server for local_models testing.

    Returns:
        Async context manager with mocked HTTP server
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        """Handle HTTP requests to local_models."""
        path = request.url.path

        # Mock health check
        if path == "/health":
            return httpx.Response(200, json={"status": "ok"})

        # Mock model list
        if path == "/models":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "mistral", "type": "chat"},
                        {"name": "starcoder", "type": "completion"},
                    ]
                },
            )

        # Mock model inference
        if path.startswith("/v1/models/"):
            model_name = path.split("/")[-1]
            body = request.read()
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"primary_goal": "test", "confidence": 0.9}'
                            }
                        }
                    ],
                    "usage": {
                        "total_tokens": 100,
                        "prompt_tokens": 50,
                        "completion_tokens": 50,
                    },
                },
            )

        return httpx.Response(404, json={"error": "Not found"})

    async with httpx.ASGITransport(app=None) as transport:
        yield handler


@pytest.fixture
def mcp_wrapper_mock():
    """Create mock MCP wrapper for testing.

    Returns:
        Mock MCP wrapper with execute_plan method
    """
    mock_wrapper = AsyncMock()
    mock_wrapper.execute_plan = AsyncMock(
        return_value=[{"code": "def hello(): return 'world'", "success": True}]
    )
    return mock_wrapper


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory.

    Args:
        tmp_path: Temporary directory provided by pytest

    Returns:
        Path to temporary data directory
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """Clean up test files after each test.

    Args:
        tmp_path: Temporary directory to clean
    """
    yield
    # Cleanup happens automatically via tmp_path fixture
    pass


# MongoDB fixtures (Cluster A - TL24-01)
@pytest.fixture(scope="session")
def mongodb_client() -> MongoClient:
    """Session-scoped MongoDB client fixture.

    Purpose:
        Provides an authenticated MongoDB client instance for all tests
        in the session. Uses test_mongodb_url from Settings.

    Returns:
        MongoClient: Configured MongoDB client for tests.
    """
    factory = MongoClientFactory()
    client = factory.create_sync_client(use_test_url=True)
    yield client
    client.close()


@pytest.fixture
def mongodb_database(mongodb_client: MongoClient, request: pytest.FixtureRequest) -> Any:
    """Function-scoped MongoDB database fixture with per-test isolation.

    Purpose:
        Creates a unique database per test (using test node ID hash) and
        ensures automatic cleanup after the test completes.

    Args:
        mongodb_client: Session-scoped MongoDB client fixture.
        request: Pytest request object to get test node ID.

    Returns:
        Database: Per-test MongoDB database instance (sync pymongo.Database).

    Note:
        Database name is derived from test node ID hash to ensure uniqueness
        while staying within MongoDB's 63 character limit.
    """
    # Generate unique database name from test node ID hash
    # MongoDB limit is 63 characters, so use hash instead of full node ID
    test_node_id = request.node.nodeid
    db_hash = str(hash(test_node_id))[-8:]  # Last 8 chars of hash (unique enough)
    # Get short test name (file + function)
    test_file = request.node.fspath.basename.replace(".py", "")
    test_func = request.node.name[:20]  # Limit function name length
    db_name = f"test_{test_file}_{test_func}_{db_hash}"[:63]  # Max 63 chars
    database = mongodb_client[db_name]

    yield database

    # Cleanup: Drop the test database after the test
    try:
        mongodb_client.drop_database(db_name)
    except Exception:
        # Ignore errors during cleanup (database might already be dropped)
        pass


@pytest.fixture
async def mongodb_database_async(
    mongodb_client: MongoClient, request: pytest.FixtureRequest
) -> AsyncIOMotorDatabase:
    """Function-scoped async MongoDB database fixture with per-test isolation.

    Purpose:
        Creates a unique async database per test (using test node ID hash) and
        ensures automatic cleanup after the test completes.
        Use this fixture for async tests that need AsyncIOMotorDatabase.

    Args:
        mongodb_client: Session-scoped MongoDB client fixture (sync).
        request: Pytest request object to get test node ID.

    Returns:
        AsyncIOMotorDatabase: Per-test async MongoDB database instance.

    Note:
        Database name is derived from test node ID hash to ensure uniqueness
        while staying within MongoDB's 63 character limit.
    """
    # Generate unique database name from test node ID hash
    # MongoDB limit is 63 characters, so use hash instead of full node ID
    test_node_id = request.node.nodeid
    db_hash = str(hash(test_node_id))[-8:]  # Last 8 chars of hash (unique enough)
    # Get short test name (file + function)
    test_file = request.node.fspath.basename.replace(".py", "")
    test_func = request.node.name[:20]  # Limit function name length
    db_name = f"test_{test_file}_{test_func}_{db_hash}"[:63]  # Max 63 chars

    # Create async client via factory
    from src.infrastructure.database.mongo_client_factory import MongoClientFactory

    factory = MongoClientFactory()
    async_client = factory.create_async_client(use_test_url=True)
    database = async_client[db_name]

    yield database

    # Cleanup: Drop the test database and close async client
    # Note: Cleanup happens before event loop closes, so async operations should work
    try:
        await database.client.drop_database(db_name)
    except Exception:
        # Ignore errors during database drop
        pass
    
    # Close async client (Motor clients can be closed even after operations)
    try:
        async_client.close()
    except Exception:
        # Ignore errors during client close
        pass


# Import MCP fixtures
from tests.fixtures.mcp_fixtures import (
    mock_mcp_client,
    sample_tools_metadata,
    sample_dialog_history,
    mock_mongodb,
    mock_llm_client,
    mock_agent_request,
    mock_agent_response,
)

# Import Butler fixtures
from tests.fixtures.butler_fixtures import (
    mock_llm_client_protocol,
    mock_tool_client_protocol,
    mock_mongodb as butler_mock_mongodb,
    mock_mode_classifier,
    mock_intent_orchestrator,
    mock_task_handler,
    mock_data_handler,
    mock_chat_handler,
    butler_orchestrator,
    sample_dialog_context,
    sample_task_message,
    sample_data_message,
    sample_idle_message,
    mock_telegram_bot,
    mock_telegram_dispatcher,
    mock_telegram_message,
    sample_user_id,
    sample_session_id,
)
