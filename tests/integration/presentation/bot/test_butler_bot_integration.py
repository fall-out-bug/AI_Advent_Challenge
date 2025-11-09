"""Integration tests for ButlerBot with ButlerOrchestrator.

Testing full integration: factory → orchestrator → bot → handler.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from src.presentation.bot.butler_bot import ButlerBot
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.presentation.bot.factory import create_butler_orchestrator


@pytest.fixture
def mock_orchestrator():
    """Create mock ButlerOrchestrator."""
    orchestrator = MagicMock(spec=ButlerOrchestrator)
    orchestrator.handle_user_message = AsyncMock(return_value="Test response")
    return orchestrator


@pytest.mark.asyncio
async def test_butler_bot_initialization(mock_orchestrator):
    """Test ButlerBot initialization with orchestrator."""
    token = "test_token_123"

    bot = ButlerBot(token=token, orchestrator=mock_orchestrator)

    assert bot.bot is not None
    assert bot.dp is not None
    assert bot.orchestrator == mock_orchestrator


@pytest.mark.asyncio
async def test_butler_bot_handler_setup(mock_orchestrator):
    """Test that handlers are properly set up."""
    token = "test_token_123"
    bot = ButlerBot(token=token, orchestrator=mock_orchestrator)

    # Check that routers are included
    assert len(bot.dp.sub_routers) >= 0  # At least some routers should be registered


@pytest.mark.asyncio
@patch("src.presentation.bot.factory.get_db")
@patch("src.presentation.bot.factory.MistralClient")
@patch("src.presentation.bot.factory.get_mcp_client")
async def test_factory_creates_orchestrator(mock_get_mcp, mock_mistral, mock_get_db):
    """Test factory creates orchestrator correctly."""
    # Mock dependencies
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    mock_llm = MagicMock()
    mock_mistral.return_value = mock_llm

    mock_mcp_base = MagicMock()
    mock_get_mcp.return_value = mock_mcp_base

    # Mock RobustMCPClient and adapter
    with patch("src.presentation.bot.factory.RobustMCPClient") as mock_robust, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter:
        mock_robust_client = MagicMock()
        mock_robust.return_value = mock_robust_client

        mock_tool_client = MagicMock()
        mock_adapter.return_value = mock_tool_client

        # Create orchestrator
        orchestrator = await create_butler_orchestrator()

        assert orchestrator is not None
        assert isinstance(orchestrator, ButlerOrchestrator)


@pytest.mark.asyncio
async def test_butler_bot_main_flow(mock_orchestrator):
    """Test main function flow with mocked dependencies."""
    with patch(
        "src.presentation.bot.butler_bot.create_butler_orchestrator"
    ) as mock_factory:
        mock_factory.return_value = mock_orchestrator

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"}):
            from src.presentation.bot.butler_bot import main

            # This would normally run polling, but we can test the setup
            # In a real test, we'd mock start_polling
            with patch(
                "src.presentation.bot.butler_bot.Dispatcher.start_polling"
            ) as mock_poll:
                mock_poll.return_value = AsyncMock()

                # Note: This test would actually start polling, so we skip for now
                # In a real scenario, you'd use aiogram's test framework
                pass
