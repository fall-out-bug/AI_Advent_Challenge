"""Tests for external API provider functionality."""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from agents.core.external_api_config import (
    ExternalAPIConfig,
    ProviderConfig,
    ProviderType,
)
from agents.core.external_api_provider import (
    ChatGPTProvider,
    ChadGPTProvider,
    ExternalAPIProvider,
)
from agents.core.unified_model_adapter import ModelProviderFactory, UnifiedModelAdapter


class TestExternalAPIProvider:
    """Test external API provider base class."""

    def test_provider_initialization(self):
        """Test provider initialization."""
        provider = ChatGPTProvider("test-key", "gpt-3.5-turbo")

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.timeout == 60.0
        assert provider.stats["total_requests"] == 0

    def test_stats_update(self):
        """Test statistics update."""
        provider = ChatGPTProvider("test-key")

        provider._update_stats(True, 100, 1.5)
        assert provider.stats["total_requests"] == 1
        assert provider.stats["successful_requests"] == 1
        assert provider.stats["total_tokens_used"] == 100
        assert len(provider.stats["response_times"]) == 1

        provider._update_stats(False, 0, 2.0)
        assert provider.stats["total_requests"] == 2
        assert provider.stats["failed_requests"] == 1

    def test_average_response_time(self):
        """Test average response time calculation."""
        provider = ChatGPTProvider("test-key")

        # No requests yet
        assert provider.get_average_response_time() == 0.0

        # Add some response times
        provider.stats["response_times"] = [1.0, 2.0, 3.0]
        assert provider.get_average_response_time() == 2.0

    def test_success_rate(self):
        """Test success rate calculation."""
        provider = ChatGPTProvider("test-key")

        # No requests yet
        assert provider.get_success_rate() == 0.0

        # Add some requests
        provider.stats["total_requests"] = 10
        provider.stats["successful_requests"] = 8
        assert provider.get_success_rate() == 80.0


class TestChatGPTProvider:
    """Test ChatGPT API provider."""

    @pytest.fixture
    def provider(self):
        """Create ChatGPT provider instance."""
        return ChatGPTProvider("test-key", "gpt-3.5-turbo")

    @pytest.mark.asyncio
    async def test_make_request_success(self, provider):
        """Test successful API request."""
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response_obj

            async with provider:
                result = await provider.make_request("test prompt", 100, 0.7)

            assert result["response"] == "Test response"
            assert result["input_tokens"] == 10
            assert result["response_tokens"] == 5
            assert result["total_tokens"] == 15
            assert provider.stats["successful_requests"] == 1

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, provider):
        """Test API request with HTTP error."""
        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 401
            mock_response_obj.text = "Unauthorized"
            mock_response_obj.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response_obj
            )
            mock_client.post.return_value = mock_response_obj

            async with provider:
                with pytest.raises(Exception, match="HTTP error 401"):
                    await provider.make_request("test prompt", 100, 0.7)

            assert provider.stats["failed_requests"] == 1

    @pytest.mark.asyncio
    async def test_check_availability_success(self, provider):
        """Test successful availability check."""
        mock_response = {
            "choices": [{"message": {"content": "test"}}],
        }

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response_obj

            async with provider:
                result = await provider.check_availability()

            assert result is True

    @pytest.mark.asyncio
    async def test_check_availability_failure(self, provider):
        """Test failed availability check."""
        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock()
            mock_client.post.side_effect = Exception("Network error")

            async with provider:
                result = await provider.check_availability()

            assert result is False


class TestChadGPTProvider:
    """Test ChadGPT API provider."""

    @pytest.fixture
    def provider(self):
        """Create ChadGPT provider instance."""
        return ChadGPTProvider("test-key", "gpt-3.5-turbo")

    @pytest.mark.asyncio
    async def test_make_request_success(self, provider):
        """Test successful API request."""
        mock_response = {
            "content": [{"text": "Test response"}],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
            },
        }

        with patch.object(provider, "_client") as mock_client:
            mock_client.post = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response_obj

            async with provider:
                result = await provider.make_request("test prompt", 100, 0.7)

            assert result["response"] == "Test response"
            assert result["input_tokens"] == 10
            assert result["response_tokens"] == 5
            assert result["total_tokens"] == 15
            assert provider.stats["successful_requests"] == 1


class TestExternalAPIConfig:
    """Test external API configuration."""

    def test_config_initialization(self):
        """Test configuration initialization."""
        config = ExternalAPIConfig()
        assert isinstance(config.providers, dict)
        assert config.default_provider is None

    def test_add_provider(self):
        """Test adding a provider."""
        config = ExternalAPIConfig()
        provider_config = ProviderConfig(
            provider_type=ProviderType.CHATGPT,
            api_key="test-key",
            model="gpt-3.5-turbo",
        )

        config.add_provider("test-provider", provider_config)

        assert "test-provider" in config.providers
        assert config.default_provider == "test-provider"

    def test_remove_provider(self):
        """Test removing a provider."""
        config = ExternalAPIConfig()
        provider_config = ProviderConfig(
            provider_type=ProviderType.CHATGPT,
            api_key="test-key",
            model="gpt-3.5-turbo",
        )

        config.add_provider("test-provider", provider_config)
        assert "test-provider" in config.providers

        result = config.remove_provider("test-provider")
        assert result is True
        assert "test-provider" not in config.providers

    def test_get_provider(self):
        """Test getting a provider."""
        config = ExternalAPIConfig()
        provider_config = ProviderConfig(
            provider_type=ProviderType.CHATGPT,
            api_key="test-key",
            model="gpt-3.5-turbo",
        )

        config.add_provider("test-provider", provider_config)

        retrieved = config.get_provider("test-provider")
        assert retrieved is not None
        assert retrieved.api_key == "test-key"

        # Test default provider
        config.default_provider = "test-provider"
        default = config.get_provider()
        assert default is not None

    def test_validation(self):
        """Test configuration validation."""
        config = ExternalAPIConfig()

        # Empty config should have warnings
        results = config.validate_config()
        assert results["valid"] is True  # Empty config is valid
        assert len(results["warnings"]) > 0

        # Add invalid provider
        invalid_config = ProviderConfig(
            provider_type=ProviderType.CHATGPT,
            api_key="",  # Invalid: empty key
            model="gpt-3.5-turbo",
            max_tokens=-1,  # Invalid: negative tokens
        )
        config.add_provider("invalid", invalid_config)

        results = config.validate_config()
        assert results["valid"] is False
        assert len(results["providers"]["invalid"]["errors"]) > 0

    def test_load_from_environment(self):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-openai-key",
                "OPENAI_MODEL": "gpt-4",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
                "ANTHROPIC_MODEL": "claude-3-opus-20240229",
                "DEFAULT_EXTERNAL_PROVIDER": "chatgpt",
            },
        ):
            config = ExternalAPIConfig()
            config._load_from_environment()

            assert "chatgpt" in config.providers
            assert "claude" in config.providers
            assert config.providers["chatgpt"].api_key == "test-openai-key"
            assert config.providers["chatgpt"].model == "gpt-4"
            assert config.default_provider == "chatgpt"

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            # Create and save config
            config1 = ExternalAPIConfig(config_file)
            provider_config = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key="test-key",
                model="gpt-3.5-turbo",
            )
            config1.add_provider("test-provider", provider_config)
            config1.save_config()

            # Load config
            config2 = ExternalAPIConfig(config_file)
            assert "test-provider" in config2.providers
            assert config2.providers["test-provider"].api_key == "test-key"

        finally:
            os.unlink(config_file)


class TestUnifiedModelAdapter:
    """Test unified model adapter."""

    def test_local_adapter_initialization(self):
        """Test local adapter initialization."""
        adapter = UnifiedModelAdapter("starcoder")

        assert adapter.model_name == "starcoder"
        assert adapter.external_provider is None
        assert adapter.local_adapter is not None
        assert adapter.external_adapter is None

    def test_external_adapter_initialization(self):
        """Test external adapter initialization."""
        # Mock config to avoid actual API calls
        with patch("agents.core.unified_model_adapter.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_provider_config = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key="test-key",
                model="gpt-3.5-turbo",
            )
            mock_config.get_provider.return_value = mock_provider_config
            mock_get_config.return_value = mock_config

            adapter = UnifiedModelAdapter("starcoder", external_provider="chatgpt")

            assert adapter.external_provider == "chatgpt"
            assert adapter.external_adapter is not None
            assert adapter.local_adapter is None

    @pytest.mark.asyncio
    async def test_make_request_local(self):
        """Test making request with local adapter."""
        adapter = UnifiedModelAdapter("starcoder")

        # Mock local adapter
        mock_response = {
            "response": "Test response",
            "total_tokens": 100,
        }
        adapter.local_adapter.make_request = AsyncMock(return_value=mock_response)

        result = await adapter.make_request("test prompt", 100, 0.7)

        assert result["response"] == "Test response"
        assert result["total_tokens"] == 100

    @pytest.mark.asyncio
    async def test_make_request_external(self):
        """Test making request with external adapter."""
        with patch("agents.core.unified_model_adapter.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_provider_config = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key="test-key",
                model="gpt-3.5-turbo",
            )
            mock_config.get_provider.return_value = mock_provider_config
            mock_get_config.return_value = mock_config

            adapter = UnifiedModelAdapter("starcoder", external_provider="chatgpt")

            # Mock external adapter
            mock_response = {
                "response": "Test response",
                "total_tokens": 100,
            }
            adapter.external_adapter.make_request = AsyncMock(
                return_value=mock_response
            )

            # Mock context manager
            adapter.external_adapter.__aenter__ = AsyncMock(
                return_value=adapter.external_adapter
            )
            adapter.external_adapter.__aexit__ = AsyncMock(return_value=None)

            result = await adapter.make_request("test prompt", 100, 0.7)

            assert result["response"] == "Test response"
            assert result["total_tokens"] == 100


class TestModelProviderFactory:
    """Test model provider factory."""

    def test_create_local_adapter(self):
        """Test creating local adapter."""
        adapter = ModelProviderFactory.create_local_adapter("starcoder")

        assert adapter.model_name == "starcoder"
        assert adapter.external_provider is None
        assert adapter.local_adapter is not None

    def test_create_external_adapter(self):
        """Test creating external adapter."""
        with patch("agents.core.unified_model_adapter.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_provider_config = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key="test-key",
                model="gpt-3.5-turbo",
            )
            mock_config.get_provider.return_value = mock_provider_config
            mock_get_config.return_value = mock_config

            adapter = ModelProviderFactory.create_external_adapter("chatgpt")

            assert adapter.external_provider == "chatgpt"
            assert adapter.external_adapter is not None

    def test_create_external_adapter_not_found(self):
        """Test creating external adapter when provider not found."""
        with patch("agents.core.unified_model_adapter.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.get_provider.return_value = None
            mock_get_config.return_value = mock_config

            with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
                ModelProviderFactory.create_external_adapter("nonexistent")

    @pytest.mark.asyncio
    async def test_create_auto_adapter(self):
        """Test creating auto adapter."""
        with patch("agents.core.unified_model_adapter.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_provider_config = ProviderConfig(
                provider_type=ProviderType.CHATGPT,
                api_key="test-key",
                model="gpt-3.5-turbo",
            )
            mock_config.get_provider.return_value = mock_provider_config
            mock_config.default_provider = "chatgpt"
            mock_config.get_enabled_providers.return_value = {
                "chatgpt": mock_provider_config
            }
            mock_get_config.return_value = mock_config

            # Mock adapter creation and availability check
            with patch(
                "agents.core.unified_model_adapter.UnifiedModelAdapter"
            ) as mock_adapter_class:
                mock_adapter = MagicMock()
                mock_adapter.check_availability = AsyncMock(return_value=True)
                mock_adapter_class.return_value = mock_adapter

                adapter = await ModelProviderFactory.create_auto_adapter()

                assert adapter is not None


if __name__ == "__main__":
    pytest.main([__file__])
