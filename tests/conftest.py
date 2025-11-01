"""Shared pytest fixtures for testing."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any, Dict

import pytest
import httpx

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
            response_tokens=50
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
            return httpx.Response(200, json={
                "models": [
                    {"name": "mistral", "type": "chat"},
                    {"name": "starcoder", "type": "completion"}
                ]
            })
        
        # Mock model inference
        if path.startswith("/v1/models/"):
            model_name = path.split("/")[-1]
            body = request.read()
            return httpx.Response(200, json={
                "choices": [{
                    "message": {
                        "content": '{"primary_goal": "test", "confidence": 0.9}'
                    }
                }],
                "usage": {
                    "total_tokens": 100,
                    "prompt_tokens": 50,
                    "completion_tokens": 50
                }
            })
        
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
        return_value=[
            {"code": "def hello(): return 'world'", "success": True}
        ]
    )
    return mock_wrapper


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests.
    
    Returns:
        Event loop for the test session
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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

