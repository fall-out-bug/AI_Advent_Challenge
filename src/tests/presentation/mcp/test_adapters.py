"""Unit tests for MCP adapters."""
from unittest.mock import AsyncMock, Mock

import pytest

from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
from src.presentation.mcp.adapters.model_adapter import ModelAdapter
from src.presentation.mcp.adapters.orchestration_adapter import OrchestrationAdapter
from src.presentation.mcp.adapters.review_adapter import ReviewAdapter
from src.presentation.mcp.adapters.token_adapter import TokenAdapter
from src.presentation.mcp.exceptions import MCPModelError, MCPValidationError


@pytest.fixture
def mock_unified_client():
    """Create mock unified client."""
    client = Mock()
    client.check_availability = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_token_analyzer():
    """Create mock token analyzer."""
    analyzer = Mock()
    analyzer.count_tokens = Mock(return_value=42)
    return analyzer


class TestModelAdapter:
    """Tests for ModelAdapter."""

    @pytest.mark.asyncio
    async def test_list_available_models_success(self):
        """Test successful model listing."""
        adapter = ModelAdapter(mock_unified_client())
        result = adapter.list_available_models()

        assert "local_models" in result
        assert "api_models" in result
        assert isinstance(result["local_models"], list)
        assert isinstance(result["api_models"], list)

    @pytest.mark.asyncio
    async def test_check_model_availability_success(self, mock_unified_client):
        """Test successful model availability check."""
        adapter = ModelAdapter(mock_unified_client)
        result = await adapter.check_model_availability("mistral")

        assert "available" in result
        assert result["available"] is True

    @pytest.mark.asyncio
    async def test_check_model_availability_failure(self):
        """Test model availability check with error."""
        mock_client = Mock()
        mock_client.check_availability = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        adapter = ModelAdapter(mock_client)

        with pytest.raises(MCPModelError):
            await adapter.check_model_availability("nonexistent")


class TestTokenAdapter:
    """Tests for TokenAdapter."""

    def test_count_text_tokens_success(self, mock_token_analyzer):
        """Test successful token counting."""
        adapter = TokenAdapter(mock_token_analyzer)
        result = adapter.count_text_tokens("Hello world")

        assert "count" in result
        assert result["count"] == 42

    def test_count_text_tokens_error(self):
        """Test token counting with error."""
        mock_analyzer = Mock()
        mock_analyzer.count_tokens = Mock(side_effect=Exception("Invalid text"))

        adapter = TokenAdapter(mock_analyzer)

        from src.presentation.mcp.exceptions import MCPAdapterError

        with pytest.raises(MCPAdapterError):
            adapter.count_text_tokens("")


class TestGenerationAdapter:
    """Tests for GenerationAdapter."""

    @pytest.mark.asyncio
    async def test_generate_code_validation_error(self):
        """Test generation with invalid input."""
        mock_client = Mock()
        adapter = GenerationAdapter(mock_client, model_name="mistral")

        with pytest.raises(MCPValidationError):
            await adapter.generate_code("")

    def test_validate_description_empty(self):
        """Test validation with empty description."""
        mock_client = Mock()
        adapter = GenerationAdapter(mock_client, model_name="mistral")

        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_description("")

        assert exc_info.value.context["field"] == "description"


class TestReviewAdapter:
    """Tests for ReviewAdapter."""

    @pytest.mark.asyncio
    async def test_review_code_validation_error(self):
        """Test review with invalid input."""
        mock_client = Mock()
        adapter = ReviewAdapter(mock_client, model_name="mistral")

        with pytest.raises(MCPValidationError):
            await adapter.review_code("")

    def test_validate_code_empty_string(self):
        """Test validation with empty code."""
        mock_client = Mock()
        adapter = ReviewAdapter(mock_client, model_name="mistral")

        with pytest.raises(MCPValidationError):
            adapter._validate_code("")


class TestOrchestrationAdapter:
    """Tests for OrchestrationAdapter."""

    @pytest.mark.asyncio
    async def test_orchestrate_validation_error_empty_description(self):
        """Test orchestration with empty description."""
        mock_client = Mock()
        adapter = OrchestrationAdapter(mock_client)

        with pytest.raises(MCPValidationError):
            await adapter.orchestrate_generation_and_review("", "mistral", "mistral")

    @pytest.mark.asyncio
    async def test_orchestrate_validation_error_empty_gen_model(self):
        """Test orchestration with empty generation model."""
        mock_client = Mock()
        adapter = OrchestrationAdapter(mock_client)

        with pytest.raises(MCPValidationError):
            await adapter.orchestrate_generation_and_review(
                "Create a todo list", "", "mistral"
            )

    @pytest.mark.asyncio
    async def test_orchestrate_validation_error_empty_review_model(self):
        """Test orchestration with empty review model."""
        mock_client = Mock()
        adapter = OrchestrationAdapter(mock_client)

        with pytest.raises(MCPValidationError):
            await adapter.orchestrate_generation_and_review(
                "Create a todo list", "mistral", ""
            )
