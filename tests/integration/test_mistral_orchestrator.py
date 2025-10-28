"""Integration tests for Mistral orchestrator."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.infrastructure.repositories.json_conversation_repository import (
    JsonConversationRepository,
)


@pytest.fixture
def mock_unified_client():
    """Create mock unified client."""
    client = AsyncMock()
    client.check_availability = AsyncMock(return_value=True)
    client.make_request = AsyncMock(
        return_value=MagicMock(response='{"primary_goal": "test", "confidence": 0.9}')
    )
    return client


@pytest.fixture
def conversation_repo():
    """Create conversation repository."""
    path = Path("data/test_conversations.json")
    repo = JsonConversationRepository(path)
    return repo


@pytest.fixture
def orchestrator(mock_unified_client, conversation_repo):
    """Create orchestrator instance."""
    return MistralChatOrchestrator(
        unified_client=mock_unified_client,
        conversation_repo=conversation_repo,
        model_name="mistral",
    )


@pytest.mark.asyncio
async def test_initialize(orchestrator):
    """Test orchestrator initialization."""
    await orchestrator.initialize()
    assert orchestrator.model_available is True


@pytest.mark.asyncio
async def test_handle_message_basic(orchestrator):
    """Test basic message handling."""
    await orchestrator.initialize()
    response = await orchestrator.handle_message("hello", "test_conv")
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_conversation_persistence(orchestrator):
    """Test conversation is persisted."""
    await orchestrator.initialize()
    conv_id = "test_persist"
    
    await orchestrator.handle_message("first message", conv_id)
    
    conversation = await orchestrator.conversation_repo.get_by_id(conv_id)
    assert conversation is not None
    assert len(conversation.messages) == 2  # user + assistant


@pytest.mark.asyncio
async def test_conversation_history(orchestrator):
    """Test conversation history is maintained."""
    await orchestrator.initialize()
    conv_id = "test_history"
    
    await orchestrator.handle_message("message 1", conv_id)
    await orchestrator.handle_message("message 2", conv_id)
    
    history = await orchestrator.conversation_repo.get_recent_messages(conv_id, limit=10)
    assert len(history) >= 4  # 2 user + 2 assistant


@pytest.mark.asyncio
async def test_clarification_needed():
    """Test clarification flow for low confidence."""
    mock_client = AsyncMock()
    mock_client.check_availability = AsyncMock(return_value=True)
    mock_client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"primary_goal": "unclear", "confidence": 0.4, "needs_clarification": true}'
        )
    )
    
    repo = JsonConversationRepository(Path("data/test_clarify.json"))
    orch = MistralChatOrchestrator(
        unified_client=mock_client,
        conversation_repo=repo,
        confidence_threshold=0.7,
    )
    
    await orch.initialize()
    response = await orch.handle_message("vague request", "test_clarify_conv")
    
    assert response is not None
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_intent_parsing():
    """Test intent parsing returns correct structure."""
    mock_client = AsyncMock()
    mock_client.check_availability = AsyncMock(return_value=True)
    mock_client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"primary_goal": "build a calculator", "tools_needed": ["generate_code"], "confidence": 0.9}'
        )
    )
    
    repo = JsonConversationRepository(Path("data/test_intent.json"))
    orch = MistralChatOrchestrator(
        unified_client=mock_client,
        conversation_repo=repo,
    )
    
    await orch.initialize()
    intent = await orch._parse_intent("build a calculator", [])
    
    assert intent.primary_goal == "build a calculator"
    assert "generate_code" in intent.tools_needed
    assert intent.confidence == 0.9
