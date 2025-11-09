"""Shared fixtures for MCP and agent testing.

Following TDD principles and Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import pytest


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client for testing.

    Returns:
        Mock MCP client with discover_tools and call_tool methods
    """
    client = AsyncMock()
    client.discover_tools = AsyncMock(
        return_value=[
            {
                "name": "get_posts",
                "description": "Get posts from channel",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            },
            {
                "name": "generate_summary",
                "description": "Generate summary from posts",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "posts_text": {"type": "string"},
                        "channel_name": {"type": "string"},
                    },
                },
            },
        ]
    )
    client.call_tool = AsyncMock(return_value={"status": "success", "data": []})
    return client


@pytest.fixture
def sample_tools_metadata():
    """Sample tool metadata for testing.

    Returns:
        List of tool metadata dictionaries
    """
    return [
        {
            "name": "get_posts",
            "description": "Get posts from channel",
            "input_schema": {
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 100},
                },
                "required": ["channel_id"],
            },
        },
        {
            "name": "generate_summary",
            "description": "Generate summary from posts",
            "input_schema": {
                "type": "object",
                "properties": {
                    "posts_text": {"type": "string"},
                    "channel_name": {"type": "string"},
                    "language": {"type": "string", "default": "ru"},
                },
                "required": ["posts_text", "channel_name"],
            },
        },
        {
            "name": "export_pdf",
            "description": "Export summary to PDF",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary_text": {"type": "string"},
                    "title": {"type": "string"},
                    "date_range": {"type": "object"},
                },
                "required": ["summary_text", "title"],
            },
        },
    ]


@pytest.fixture
def sample_dialog_history():
    """Sample dialog history for testing.

    Returns:
        List of dialog messages
    """
    return [
        {
            "role": "user",
            "content": "Собери дайджест по Набоке за 3 дня",
            "timestamp": datetime(2025, 1, 30, 10, 0, 0),
            "tokens": 15,
        },
        {
            "role": "assistant",
            "content": "Получаю список подписок...",
            "timestamp": datetime(2025, 1, 30, 10, 0, 5),
            "tokens": 8,
        },
        {
            "role": "assistant",
            "content": "Нашел канал: onaboka",
            "timestamp": datetime(2025, 1, 30, 10, 0, 10),
            "tokens": 6,
        },
    ]


@pytest.fixture
async def mock_mongodb():
    """Create mock MongoDB connection for testing.

    Returns:
        Mock MongoDB database with collections
    """
    db = MagicMock()
    db.dialogs = MagicMock()
    db.dialogs.find_one = AsyncMock(return_value=None)
    db.dialogs.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    db.dialogs.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    db.dialogs.find = AsyncMock(
        return_value=MagicMock(to_list=AsyncMock(return_value=[]))
    )
    return db


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client for testing.

    Returns:
        Mock UnifiedModelClient with make_request method
    """
    from shared_package.clients.base_client import ModelResponse

    client = MagicMock()
    client.make_request = AsyncMock(
        return_value=ModelResponse(
            response="Mock LLM response",
            total_tokens=100,
            input_tokens=50,
            response_tokens=50,
            model_name="mistral",
            response_time=1.0,
        )
    )
    return client


@pytest.fixture
def mock_agent_request():
    """Create sample agent request for testing.

    Returns:
        Mock agent request dictionary
    """
    return {
        "user_id": 12345,
        "message": "Собери дайджест по Набоке за 3 дня",
        "session_id": "test_session_123",
        "context": {},
    }


@pytest.fixture
def mock_agent_response():
    """Create sample agent response for testing.

    Returns:
        Mock agent response dictionary
    """
    return {
        "success": True,
        "text": "Дайджест готов! Файл: /output/digest_onaboka.pdf",
        "tools_used": [
            "get_subscriptions",
            "get_posts",
            "generate_summary",
            "export_pdf",
        ],
        "tokens_used": 500,
    }
