"""Tests for formalize task adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.presentation.mcp.adapters.formalize_adapter import FormalizeAdapter


@pytest.fixture
def mock_unified_client():
    """Create mock unified client."""
    client = MagicMock()
    return client


def test_formalize_adapter_init(mock_unified_client):
    """Test adapter initialization."""
    adapter = FormalizeAdapter(mock_unified_client, model_name="mistral")
    assert adapter.unified_client == mock_unified_client
    assert adapter.model_name == "mistral"


def test_formalize_adapter_validate_inputs(mock_unified_client):
    """Test input validation."""
    adapter = FormalizeAdapter(mock_unified_client, model_name="mistral")

    # Should not raise for valid input
    adapter._validate_inputs("Create a calculator")

    # Should raise for empty input
    with pytest.raises(Exception):  # MCPValidationError
        adapter._validate_inputs("")

    with pytest.raises(Exception):  # MCPValidationError
        adapter._validate_inputs("   ")


def test_formalize_adapter_build_prompt(mock_unified_client):
    """Test prompt building."""
    adapter = FormalizeAdapter(mock_unified_client, model_name="mistral")

    prompt = adapter._build_prompt("Create a REST API", "Use FastAPI")

    assert "REST API" in prompt
    assert "FastAPI" in prompt
    assert "formalized_description" in prompt
    assert "requirements" in prompt
    assert "steps" in prompt
    assert "estimated_complexity" in prompt


def test_formalize_adapter_parse_response(mock_unified_client):
    """Test response parsing."""
    import json

    adapter = FormalizeAdapter(mock_unified_client, model_name="mistral")

    # Test valid JSON
    valid_json = json.dumps(
        {
            "formalized_description": "Build REST API",
            "requirements": ["endpoint", "auth"],
            "steps": ["setup", "implement"],
            "estimated_complexity": "medium",
        }
    )
    result = adapter._parse_response(valid_json)
    assert result["success"] is True
    assert "Build REST API" in result["formalized_description"]
    assert len(result["requirements"]) == 2

    # Test invalid JSON (fallback)
    result = adapter._parse_response("Not JSON")
    assert result["success"] is True  # Fallback succeeds


@pytest.mark.asyncio
async def test_formalize_adapter_formalize(mock_unified_client):
    """Test full formalize flow."""

    # Mock the model client adapter
    async def mock_generate(**kwargs):
        return {
            "response": '{"formalized_description": "Task", "requirements": ["req1"], "steps": ["step1"], "estimated_complexity": "low"}'
        }

    # Mock get_model_client_adapter
    with patch(
        "src.presentation.mcp.adapters.formalize_adapter._get_model_client_adapter"
    ) as mock_get:
        mock_adapter_class = MagicMock()
        mock_adapter = AsyncMock()
        mock_adapter.generate = AsyncMock(side_effect=mock_generate)
        mock_adapter_class.return_value = mock_adapter
        mock_get.return_value = mock_adapter_class

        adapter = FormalizeAdapter(mock_unified_client, model_name="mistral")
        result = await adapter.formalize("Create a calculator", "Use Python")

        assert result["success"] is True
        assert "Task" in result["formalized_description"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
