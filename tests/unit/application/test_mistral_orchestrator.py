"""Unit tests for Mistral orchestrator."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.domain.entities.conversation import IntentAnalysis
from src.infrastructure.repositories.json_conversation_repository import (
    JsonConversationRepository,
)


@pytest.fixture
def mock_unified_client():
    """Create mock unified client."""
    client = AsyncMock()
    client.make_request = AsyncMock(
        return_value=MagicMock(response='{"primary_goal": "test", "confidence": 0.9}')
    )
    return client


@pytest.fixture
def conversation_repo():
    """Create conversation repository."""
    curator = JsonConversationRepository(Path("data/test_convs.json"))
    return curator


@pytest.fixture
def orchestrator(mock_unified_client, conversation_repo):
    """Create orchestrator instance."""
    return MistralChatOrchestrator(
        unified_client=mock_unified_client,
        conversation_repo=conversation_repo,
        model_name="mistral",
    )


@pytest.mark.asyncio
async def test_parse_intent_json_valid(orchestrator):
    """Test parsing valid intent JSON."""
    valid_json = '{"primary_goal": "generate code", "tools_needed": ["generate_code"], "confidence": 0.9}'
    intent = orchestrator._parse_intent_json(valid_json)
    assert intent.primary_goal == "generate code"
    assert "generate_code" in intent.tools_needed
    assert intent.confidence == 0.9


@pytest.mark.asyncio
async def test_parse_intent_json_invalid(orchestrator):
    """Test parsing invalid intent JSON."""
    invalid_json = "not json"
    intent = orchestrator._parse_intent_json(invalid_json)
    assert intent.needs_clarification is True
    assert intent.confidence == 0.5


@pytest.mark.asyncio
async def test_check_clarification_needed_high_confidence(orchestrator):
    """Test high confidence doesn't need clarification."""
    intent = IntentAnalysis(
        primary_goal="test", confidence=0.9, needs_clarification=False
    )
    result = await orchestrator._check_clarification_needed(intent)
    assert result is False


@pytest.mark.asyncio
async def test_check_clarification_needed_low_confidence(orchestrator):
    """Test low confidence needs clarification."""
    intent = IntentAnalysis(
        primary_goal="test", confidence=0.5, needs_clarification=False
    )
    result = await orchestrator._check_clarification_needed(intent)
    assert result is True

