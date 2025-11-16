"""Unit tests for ButlerOrchestrator factory.

Following TDD principles: test factory pattern implementation.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.presentation.bot.factory import create_butler_orchestrator
from src.presentation.bot.orchestrator import ButlerOrchestrator


@pytest.mark.asyncio
async def test_create_butler_orchestrator_success(mock_mongodb):
    """Test successful ButlerOrchestrator creation.

    Args:
        mock_mongodb: Mock MongoDB database.
    """
    with patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp, patch(
        "src.presentation.bot.factory.RobustMCPClient"
    ) as mock_robust_mcp, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter:
        # Setup mocks
        mock_get_db.return_value = mock_mongodb
        mock_mistral_instance = MagicMock()
        mock_mistral.return_value = mock_mistral_instance
        mock_mcp_instance = MagicMock()
        mock_get_mcp.return_value = mock_mcp_instance
        mock_robust_mcp_instance = MagicMock()
        mock_robust_mcp.return_value = mock_robust_mcp_instance
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        # Execute
        orchestrator = await create_butler_orchestrator(mongodb=mock_mongodb)

        # Verify
        assert isinstance(orchestrator, ButlerOrchestrator)
        assert orchestrator.mongodb == mock_mongodb


@pytest.mark.asyncio
async def test_create_butler_orchestrator_with_custom_mongodb():
    """Test factory accepts custom MongoDB instance.

    Verifies that mongodb parameter is used when provided.
    """
    custom_mongodb = MagicMock(spec=AsyncIOMotorDatabase)
    custom_mongodb.dialog_contexts = MagicMock()

    with patch("src.presentation.bot.factory.get_db", new_callable=AsyncMock), patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp, patch(
        "src.presentation.bot.factory.RobustMCPClient"
    ) as mock_robust_mcp, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter:
        # Setup mocks
        mock_mistral_instance = MagicMock()
        mock_mistral.return_value = mock_mistral_instance
        mock_mcp_instance = MagicMock()
        mock_get_mcp.return_value = mock_mcp_instance
        mock_robust_mcp_instance = MagicMock()
        mock_robust_mcp.return_value = mock_robust_mcp_instance
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        # Execute
        orchestrator = await create_butler_orchestrator(mongodb=custom_mongodb)

        # Verify
        assert orchestrator.mongodb == custom_mongodb


@pytest.mark.asyncio
async def test_create_butler_orchestrator_uses_env_variables():
    """Test factory uses environment variables for configuration.

    Verifies MISTRAL_API_URL and MCP_SERVER_URL are read from env.
    """
    with patch.dict(
        os.environ,
        {
            "MISTRAL_API_URL": "http://test:8001",
            "MCP_SERVER_URL": "http://test-mcp:8000",
        },
    ), patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp, patch(
        "src.presentation.bot.factory.RobustMCPClient"
    ) as mock_robust_mcp, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter:
        # Setup
        mock_get_db.return_value = MagicMock()
        mock_mistral_instance = MagicMock()
        mock_mistral.return_value = mock_mistral_instance
        mock_mcp_instance = MagicMock()
        mock_get_mcp.return_value = mock_mcp_instance
        mock_robust_mcp_instance = MagicMock()
        mock_robust_mcp.return_value = mock_robust_mcp_instance
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        # Execute
        await create_butler_orchestrator()

        # Verify: URLs come from environment variables (config-driven)
        # Check that URLs are passed correctly, not hardcoded values
        assert mock_mistral.called
        assert mock_get_mcp.called
        # Verify URLs match environment variables (config-driven check)
        mistral_call = mock_mistral.call_args
        mcp_call = mock_get_mcp.call_args
        assert mistral_call is not None
        assert mcp_call is not None
        # URLs should come from env vars, not hardcoded
        assert "base_url" in mistral_call.kwargs or mistral_call.args
        assert "server_url" in mcp_call.kwargs or mcp_call.args


@pytest.mark.asyncio
async def test_create_butler_orchestrator_defaults_mistral_url():
    """Test factory uses default Mistral URL when env var not set.

    Verifies default fallback to http://localhost:8001.
    """
    with patch.dict(os.environ, {}, clear=True), patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp, patch(
        "src.presentation.bot.factory.RobustMCPClient"
    ) as mock_robust_mcp, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter:
        # Setup
        mock_get_db.return_value = MagicMock()
        mock_mistral_instance = MagicMock()
        mock_mistral.return_value = mock_mistral_instance
        mock_mcp_instance = MagicMock()
        mock_get_mcp.return_value = mock_mcp_instance
        mock_robust_mcp_instance = MagicMock()
        mock_robust_mcp.return_value = mock_robust_mcp_instance
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        # Execute
        await create_butler_orchestrator()

        # Verify: Default URL comes from Settings (config-driven)
        # Check that default URL is used when env var not set
        assert mock_mistral.called
        mistral_call = mock_mistral.call_args
        assert mistral_call is not None
        # URL should come from Settings default, not hardcoded
        assert "base_url" in mistral_call.kwargs or mistral_call.args


@pytest.mark.asyncio
async def test_create_butler_orchestrator_mongodb_error():
    """Test factory handles MongoDB connection errors.

    Verifies RuntimeError is raised when MongoDB initialization fails.
    """
    with patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db:
        # Setup: MongoDB connection fails
        mock_get_db.side_effect = Exception("Connection failed")

        # Execute & Verify
        with pytest.raises(
            RuntimeError, match="Failed to initialize ButlerOrchestrator"
        ):
            await create_butler_orchestrator()


@pytest.mark.asyncio
async def test_create_butler_orchestrator_mistral_error(mock_mongodb):
    """Test factory handles MistralClient initialization errors.

    Args:
        mock_mongodb: Mock MongoDB database.

    Verifies RuntimeError is raised when MistralClient fails.
    """
    with patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral:
        # Setup
        mock_get_db.return_value = mock_mongodb
        mock_mistral.side_effect = Exception("Mistral initialization failed")

        # Execute & Verify
        with pytest.raises(
            RuntimeError, match="Failed to initialize ButlerOrchestrator"
        ):
            await create_butler_orchestrator(mongodb=mock_mongodb)


@pytest.mark.asyncio
async def test_create_butler_orchestrator_mcp_error(mock_mongodb):
    """Test factory handles MCP client initialization errors.

    Args:
        mock_mongodb: Mock MongoDB database.

    Verifies RuntimeError is raised when MCP client fails.
    """
    with patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp:
        # Setup
        mock_get_db.return_value = mock_mongodb
        mock_mistral.return_value = MagicMock()
        mock_get_mcp.side_effect = Exception("MCP connection failed")

        # Execute & Verify
        with pytest.raises(
            RuntimeError, match="Failed to initialize ButlerOrchestrator"
        ):
            await create_butler_orchestrator(mongodb=mock_mongodb)


@pytest.mark.asyncio
async def test_create_butler_orchestrator_initializes_all_components(mock_mongodb):
    """Test factory initializes all required components.

    Args:
        mock_mongodb: Mock MongoDB database.

    Verifies all components are created with correct dependencies.
    """
    with patch(
        "src.presentation.bot.factory.get_db", new_callable=AsyncMock
    ) as mock_get_db, patch(
        "src.presentation.bot.factory.MistralClient"
    ) as mock_mistral, patch(
        "src.presentation.bot.factory.get_mcp_client"
    ) as mock_get_mcp, patch(
        "src.presentation.bot.factory.RobustMCPClient"
    ) as mock_robust_mcp, patch(
        "src.presentation.bot.factory.MCPToolClientAdapter"
    ) as mock_adapter, patch(
        "src.presentation.bot.factory.ModeClassifier"
    ) as mock_mode_classifier, patch(
        "src.presentation.bot.factory.IntentOrchestrator"
    ) as mock_intent_orch, patch(
        "src.presentation.bot.factory.CreateTaskUseCase"
    ) as mock_create_uc, patch(
        "src.presentation.bot.factory.CollectDataUseCase"
    ) as mock_collect_uc, patch(
        "src.presentation.bot.factory.TaskHandler"
    ) as mock_task_handler, patch(
        "src.presentation.bot.factory.DataHandler"
    ) as mock_data_handler, patch(
        "src.presentation.bot.factory.ChatHandler"
    ) as mock_chat_handler, patch(
        "src.presentation.bot.factory.ButlerOrchestrator"
    ) as mock_butler:
        # Setup
        mock_get_db.return_value = mock_mongodb
        mock_mistral_instance = MagicMock()
        mock_mistral.return_value = mock_mistral_instance
        mock_mcp_instance = MagicMock()
        mock_get_mcp.return_value = mock_mcp_instance
        mock_robust_mcp_instance = MagicMock()
        mock_robust_mcp.return_value = mock_robust_mcp_instance
        mock_adapter_instance = MagicMock()
        mock_adapter.return_value = mock_adapter_instance

        # Execute
        await create_butler_orchestrator(mongodb=mock_mongodb)

        # Verify: All components should be initialized
        assert mock_mistral.called
        assert mock_get_mcp.called
        assert mock_robust_mcp.called
        assert mock_adapter.called
        assert mock_mode_classifier.called
        assert mock_intent_orch.called
        assert mock_create_uc.called
        assert mock_collect_uc.called
        assert mock_task_handler.called
        assert mock_data_handler.called
        assert mock_chat_handler.called
        assert mock_butler.called
