"""Tests for model client adapter."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.core.model_client_adapter import ModelClientAdapter


class TestModelClientAdapter:
    """Test model client adapter functionality."""

    def setup_method(self):
        """Set up test adapter."""
        self.adapter = ModelClientAdapter()

    def test_init(self):
        """Test adapter initialization."""
        assert self.adapter is not None
        assert self.adapter.model_name == "starcoder"

    def test_init_with_custom_model(self):
        """Test adapter initialization with custom model."""
        adapter = ModelClientAdapter(model_name="mistral", timeout=30.0)
        assert adapter.model_name == "mistral"

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_make_request_success(self, mock_client_class):
        """Test successful model request."""
        # Mock response
        mock_response = Mock()
        mock_response.response = "def test(): pass"
        mock_response.input_tokens = 50
        mock_response.response_tokens = 100
        mock_response.total_tokens = 150
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.make_request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        result = await adapter.make_request(
            prompt="Create a test function",
            max_tokens=1000,
            temperature=0.7
        )

        assert result["response"] == "def test(): pass"
        assert result["input_tokens"] == 50
        assert result["response_tokens"] == 100
        assert result["total_tokens"] == 150

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_make_request_connection_error(self, mock_client_class):
        """Test model request with connection error."""
        from shared_package.exceptions.model_errors import ModelConnectionError
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.make_request.side_effect = ModelConnectionError("Connection failed")
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        with pytest.raises(Exception, match="Model request failed: Connection failed"):
            await adapter.make_request(
                prompt="Create a test function",
                max_tokens=1000,
                temperature=0.7
            )

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_make_request_timeout_error(self, mock_client_class):
        """Test model request with timeout error."""
        from shared_package.exceptions.model_errors import ModelTimeoutError
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.make_request.side_effect = ModelTimeoutError("Request timeout")
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        with pytest.raises(Exception, match="Model request failed: Request timeout"):
            await adapter.make_request(
                prompt="Create a test function",
                max_tokens=1000,
                temperature=0.7
            )

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_make_request_request_error(self, mock_client_class):
        """Test model request with request error."""
        from shared_package.exceptions.model_errors import ModelRequestError
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.make_request.side_effect = ModelRequestError("Invalid request")
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        with pytest.raises(Exception, match="Model request failed: Invalid request"):
            await adapter.make_request(
                prompt="Create a test function",
                max_tokens=1000,
                temperature=0.7
            )

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_check_availability_true(self, mock_client_class):
        """Test model availability check returning true."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.check_availability.return_value = True
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        result = await adapter.check_availability()
        assert result is True

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_check_availability_false(self, mock_client_class):
        """Test model availability check returning false."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.check_availability.return_value = False
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        result = await adapter.check_availability()
        assert result is False

    @patch("agents.core.model_client_adapter.UnifiedModelClient")
    async def test_close(self, mock_client_class):
        """Test closing client resources."""
        # Mock client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        adapter = ModelClientAdapter()
        adapter.client = mock_client

        await adapter.close()
        mock_client.close.assert_called_once()

    def test_model_name_property(self):
        """Test model name property."""
        adapter = ModelClientAdapter(model_name="qwen")
        assert adapter.model_name == "qwen"

    def test_client_property(self):
        """Test client property."""
        adapter = ModelClientAdapter()
        assert adapter.client is not None
