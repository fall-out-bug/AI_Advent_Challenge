"""Integration test fixtures for Butler Agent.

Following TDD principles: comprehensive fixtures for cross-layer testing.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.fixtures.butler_fixtures import (
    butler_orchestrator,
    mock_llm_client_protocol,
    mock_mongodb,
    mock_tool_client_protocol,
)


@pytest.fixture
async def integration_llm_client(mock_llm_client_protocol):
    """LLM client for integration tests with configurable responses.

    Args:
        mock_llm_client_protocol: Base mock LLM client.

    Returns:
        Configurable mock LLM client.
    """
    # Allow response configuration per test
    mock_llm_client_protocol.make_request = AsyncMock(
        side_effect=lambda *args, **kwargs: "TASK"
    )
    return mock_llm_client_protocol


@pytest.fixture
async def integration_tool_client(mock_tool_client_protocol):
    """Tool client for integration tests with configurable responses.

    Args:
        mock_tool_client_protocol: Base mock tool client.

    Returns:
        Configurable mock tool client.
    """
    # Allow tool call responses to be configured per test
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"success": True, "data": {"id": "test_123"}}
    )
    return mock_tool_client_protocol


@pytest.fixture
async def integration_orchestrator(
    butler_orchestrator, integration_llm_client, integration_tool_client
):
    """ButlerOrchestrator configured for integration tests.

    This fixture uses configurable mocks that can be adjusted
    in individual tests.

    Args:
        butler_orchestrator: Base butler orchestrator fixture.
        integration_llm_client: Configurable LLM client.
        integration_tool_client: Configurable tool client.

    Returns:
        ButlerOrchestrator instance for integration testing.
    """
    return butler_orchestrator


@pytest.fixture
async def integration_mongodb(mock_mongodb):
    """MongoDB for integration tests with state management.

    Args:
        mock_mongodb: Base mock MongoDB.

    Returns:
        Mock MongoDB with enhanced state tracking.
    """
    # Track stored contexts
    stored_contexts: Dict[str, Any] = {}

    async def find_one_mock(filter: Dict[str, Any]) -> Dict[str, Any] | None:
        """Find context by user_id and session_id."""
        user_id = filter.get("user_id")
        session_id = filter.get("session_id")
        key = f"{user_id}:{session_id}"
        return stored_contexts.get(key)

    async def insert_one_mock(doc: Dict[str, Any]) -> MagicMock:
        """Insert new context."""
        user_id = doc.get("user_id")
        session_id = doc.get("session_id")
        key = f"{user_id}:{session_id}"
        stored_contexts[key] = doc
        result = MagicMock()
        result.inserted_id = f"context_{len(stored_contexts)}"
        return result

    async def update_one_mock(
        filter: Dict[str, Any], update: Dict[str, Any], **kwargs
    ) -> MagicMock:
        """Update existing context."""
        user_id = filter.get("user_id")
        session_id = filter.get("session_id")
        key = f"{user_id}:{session_id}"
        if key in stored_contexts:
            stored_contexts[key].update(update.get("$set", {}))
            result = MagicMock()
            result.modified_count = 1
            return result
        result = MagicMock()
        result.modified_count = 0
        return result

    mock_mongodb.dialog_contexts.find_one = AsyncMock(side_effect=find_one_mock)
    mock_mongodb.dialog_contexts.insert_one = AsyncMock(side_effect=insert_one_mock)
    mock_mongodb.dialog_contexts.update_one = AsyncMock(side_effect=update_one_mock)

    return mock_mongodb


@pytest.fixture(scope="function")
async def real_mongodb(mongodb_database_async):
    """Real MongoDB connection for integration tests (deprecated - use mongodb_database_async).

    Purpose:
        Legacy alias for mongodb_database_async fixture.
        Provides per-test isolated MongoDB database.

    Yields:
        MongoDB database instance (AsyncIOMotorDatabase).

    Note:
        This fixture is kept for backward compatibility.
        New tests should use mongodb_database_async directly.
    """
    yield mongodb_database_async
