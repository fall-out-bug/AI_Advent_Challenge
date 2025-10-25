"""
Unit tests for communication adapters.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError, ClientTimeout

from shared_package.orchestration.adapters import (
    AdapterType,
    AdapterConfig,
    CommunicationAdapter,
    DirectAdapter,
    RestAdapter,
    AdapterFactory
)
from shared_package.agents.schemas import AgentRequest, AgentResponse, TaskMetadata


class TestAdapterConfig:
    """Test adapter configuration."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = AdapterConfig(adapter_type=AdapterType.DIRECT)
        
        assert config.adapter_type == AdapterType.DIRECT
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
    
    def test_custom_config(self):
        """Test custom configuration creation."""
        config = AdapterConfig(
            adapter_type=AdapterType.REST,
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.adapter_type == AdapterType.REST
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid timeout
        with pytest.raises(ValueError):
            AdapterConfig(adapter_type=AdapterType.DIRECT, timeout=0.05)
        
        # Test invalid max_retries
        with pytest.raises(ValueError):
            AdapterConfig(adapter_type=AdapterType.DIRECT, max_retries=-1)


class TestDirectAdapter:
    """Test direct adapter implementation."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock agent for testing."""
        agent = AsyncMock()
        agent.process = AsyncMock()
        return agent
    
    @pytest.fixture
    def adapter(self):
        """Create direct adapter for testing."""
        config = AdapterConfig(adapter_type=AdapterType.DIRECT)
        return DirectAdapter(config)
    
    def test_adapter_type(self, adapter):
        """Test adapter type."""
        assert adapter.get_adapter_type() == AdapterType.DIRECT
    
    def test_register_agent(self, adapter, mock_agent):
        """Test agent registration."""
        adapter.register_agent("test_agent", mock_agent)
        assert "test_agent" in adapter._agents
        assert adapter._agents["test_agent"] == mock_agent
    
    def test_unregister_agent(self, adapter, mock_agent):
        """Test agent unregistration."""
        adapter.register_agent("test_agent", mock_agent)
        adapter.unregister_agent("test_agent")
        assert "test_agent" not in adapter._agents
    
    def test_unregister_nonexistent_agent(self, adapter):
        """Test unregistering non-existent agent."""
        # Should not raise exception
        adapter.unregister_agent("nonexistent")
    
    @pytest.mark.asyncio
    async def test_is_available_registered(self, adapter, mock_agent):
        """Test availability check for registered agent."""
        adapter.register_agent("test_agent", mock_agent)
        assert await adapter.is_available("test_agent") is True
    
    @pytest.mark.asyncio
    async def test_is_available_not_registered(self, adapter):
        """Test availability check for unregistered agent."""
        assert await adapter.is_available("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_send_request_success(self, adapter, mock_agent):
        """Test successful request sending."""
        # Setup
        adapter.register_agent("test_agent", mock_agent)
        request = AgentRequest(task="test task")
        expected_response = AgentResponse(
            result="test result",
            success=True,
            metadata=TaskMetadata(
                task_id="test_id",
                task_type="test",
                timestamp=1234567890.0
            )
        )
        mock_agent.process.return_value = expected_response
        
        # Execute
        response = await adapter.send_request("test_agent", request)
        
        # Verify
        assert response == expected_response
        mock_agent.process.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_send_request_agent_not_registered(self, adapter):
        """Test request to unregistered agent."""
        request = AgentRequest(task="test task")
        
        with pytest.raises(ValueError, match="Agent test_agent not registered"):
            await adapter.send_request("test_agent", request)
    
    @pytest.mark.asyncio
    async def test_send_request_agent_error(self, adapter, mock_agent):
        """Test request when agent raises exception."""
        # Setup
        adapter.register_agent("test_agent", mock_agent)
        request = AgentRequest(task="test task")
        mock_agent.process.side_effect = Exception("Agent error")
        
        # Execute and verify
        with pytest.raises(Exception, match="Agent error"):
            await adapter.send_request("test_agent", request)


class TestRestAdapter:
    """Test REST adapter implementation."""
    
    @pytest.fixture
    def adapter(self):
        """Create REST adapter for testing."""
        config = AdapterConfig(adapter_type=AdapterType.REST)
        return RestAdapter("http://localhost:8000", config)
    
    def test_adapter_type(self, adapter):
        """Test adapter type."""
        assert adapter.get_adapter_type() == AdapterType.REST
    
    def test_base_url_normalization(self):
        """Test base URL normalization."""
        adapter = RestAdapter("http://localhost:8000/", AdapterConfig(adapter_type=AdapterType.REST))
        assert adapter.base_url == "http://localhost:8000"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_get_session_creation(self, mock_session_class, adapter):
        """Test HTTP session creation."""
        session = await adapter._get_session()
        assert session is not None
        assert isinstance(session, MagicMock)  # Mocked aiohttp.ClientSession
    
    @pytest.mark.asyncio
    async def test_close_session(self, adapter):
        """Test session closing."""
        await adapter._get_session()
        await adapter.close()
        # Session should be closed (mocked)
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_send_request_success(self, mock_get_session, adapter):
        """Test successful REST request."""
        # Setup mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "result": "test result",
            "success": True,
            "error": None,
            "metadata": None,
            "quality": None
        })
        
        # Create proper async context manager mock
        class AsyncContextManager:
            def __init__(self, return_value):
                self.return_value = return_value
            
            async def __aenter__(self):
                return self.return_value
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session = MagicMock()
        mock_session.post.return_value = AsyncContextManager(mock_response)
        mock_get_session.return_value = mock_session
        
        # Execute
        request = AgentRequest(task="test task")
        response = await adapter.send_request("test_agent", request)
        
        # Verify
        assert response.result == "test result"
        assert response.success is True
        mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_send_request_http_error(self, mock_get_session, adapter):
        """Test REST request with HTTP error."""
        # Setup mock
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        # Create proper async context manager mock
        class AsyncContextManager:
            def __init__(self, return_value):
                self.return_value = return_value
            
            async def __aenter__(self):
                return self.return_value
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session = MagicMock()
        mock_session.post.return_value = AsyncContextManager(mock_response)
        mock_get_session.return_value = mock_session
        
        # Execute and verify
        request = AgentRequest(task="test task")
        with pytest.raises(Exception, match="HTTP 500: Internal Server Error"):
            await adapter.send_request("test_agent", request)
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_send_request_retry_logic(self, mock_get_session, adapter):
        """Test REST request retry logic."""
        # Setup mock to fail first two attempts, succeed on third
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "result": "test result",
            "success": True,
            "error": None,
            "metadata": None,
            "quality": None
        })
        
        # Create proper async context manager mock
        class AsyncContextManager:
            def __init__(self, return_value):
                self.return_value = return_value
            
            async def __aenter__(self):
                return self.return_value
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session = MagicMock()
        # First two calls fail, third succeeds
        mock_session.post.side_effect = [
            ClientError("Connection failed"),
            ClientError("Connection failed"),
            AsyncContextManager(mock_response)
        ]
        mock_get_session.return_value = mock_session
        
        # Execute
        request = AgentRequest(task="test task")
        response = await adapter.send_request("test_agent", request)
        
        # Verify
        assert response.result == "test result"
        assert mock_session.post.call_count == 3
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_send_request_max_retries_exceeded(self, mock_get_session, adapter):
        """Test REST request when max retries exceeded."""
        # Setup mock to always fail
        mock_session = MagicMock()
        mock_session.post.side_effect = ClientError("Connection failed")
        mock_get_session.return_value = mock_session
        
        # Execute and verify
        request = AgentRequest(task="test task")
        with pytest.raises(ClientError, match="Connection failed"):
            await adapter.send_request("test_agent", request)
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_is_available_success(self, mock_get_session, adapter):
        """Test availability check success."""
        # Setup mock
        mock_response = AsyncMock()
        mock_response.status = 200
        
        # Create proper async context manager mock
        class AsyncContextManager:
            def __init__(self, return_value):
                self.return_value = return_value
            
            async def __aenter__(self):
                return self.return_value
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session = MagicMock()
        mock_session.get.return_value = AsyncContextManager(mock_response)
        mock_get_session.return_value = mock_session
        
        # Execute
        result = await adapter.is_available("test_agent")
        
        # Verify
        assert result is True
        mock_session.get.assert_called_once_with("http://localhost:8000/agents/test_agent/health")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_is_available_failure(self, mock_session_class, adapter):
        """Test availability check failure."""
        # Setup mock
        mock_session = AsyncMock()
        mock_session.get.side_effect = ClientError("Connection failed")
        mock_session_class.return_value = mock_session
        
        # Execute
        result = await adapter.is_available("test_agent")
        
        # Verify
        assert result is False


class TestAdapterFactory:
    """Test adapter factory."""
    
    def test_create_direct_adapter_default(self):
        """Test creating direct adapter with default config."""
        adapter = AdapterFactory.create_direct_adapter()
        
        assert isinstance(adapter, DirectAdapter)
        assert adapter.get_adapter_type() == AdapterType.DIRECT
    
    def test_create_direct_adapter_custom_config(self):
        """Test creating direct adapter with custom config."""
        config = AdapterConfig(
            adapter_type=AdapterType.DIRECT,
            timeout=60.0,
            max_retries=5
        )
        adapter = AdapterFactory.create_direct_adapter(config)
        
        assert isinstance(adapter, DirectAdapter)
        assert adapter.config.timeout == 60.0
        assert adapter.config.max_retries == 5
    
    def test_create_rest_adapter_default(self):
        """Test creating REST adapter with default config."""
        adapter = AdapterFactory.create_rest_adapter("http://localhost:8000")
        
        assert isinstance(adapter, RestAdapter)
        assert adapter.get_adapter_type() == AdapterType.REST
        assert adapter.base_url == "http://localhost:8000"
    
    def test_create_rest_adapter_custom_config(self):
        """Test creating REST adapter with custom config."""
        config = AdapterConfig(
            adapter_type=AdapterType.REST,
            timeout=60.0,
            max_retries=5
        )
        adapter = AdapterFactory.create_rest_adapter("http://localhost:8000", config)
        
        assert isinstance(adapter, RestAdapter)
        assert adapter.config.timeout == 60.0
        assert adapter.config.max_retries == 5
    
    def test_create_adapter_direct(self):
        """Test creating adapter by type - direct."""
        adapter = AdapterFactory.create_adapter(AdapterType.DIRECT)
        
        assert isinstance(adapter, DirectAdapter)
        assert adapter.get_adapter_type() == AdapterType.DIRECT
    
    def test_create_adapter_rest(self):
        """Test creating adapter by type - REST."""
        adapter = AdapterFactory.create_adapter(
            AdapterType.REST,
            base_url="http://localhost:8000"
        )
        
        assert isinstance(adapter, RestAdapter)
        assert adapter.get_adapter_type() == AdapterType.REST
    
    def test_create_adapter_rest_missing_base_url(self):
        """Test creating REST adapter without base_url."""
        with pytest.raises(ValueError, match="base_url is required for REST adapter"):
            AdapterFactory.create_adapter(AdapterType.REST)
    
    def test_create_adapter_unsupported_type(self):
        """Test creating adapter with unsupported type."""
        with pytest.raises(ValueError, match="Unsupported adapter type"):
            AdapterFactory.create_adapter("unsupported_type")


class TestIntegration:
    """Integration tests for communication adapters."""
    
    @pytest.mark.asyncio
    async def test_direct_adapter_workflow(self):
        """Test complete direct adapter workflow."""
        # Create adapter
        adapter = AdapterFactory.create_direct_adapter()
        
        # Create mock agent
        mock_agent = AsyncMock()
        expected_response = AgentResponse(
            result="Generated code",
            success=True,
            metadata=TaskMetadata(
                task_id="test_123",
                task_type="code_generation",
                timestamp=1234567890.0
            )
        )
        mock_agent.process.return_value = expected_response
        
        # Register agent
        adapter.register_agent("code_generator", mock_agent)
        
        # Test workflow
        assert await adapter.is_available("code_generator") is True
        
        request = AgentRequest(task="Generate a function")
        response = await adapter.send_request("code_generator", request)
        
        assert response.result == "Generated code"
        assert response.success is True
        mock_agent.process.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    @patch('shared_package.orchestration.adapters.RestAdapter._get_session')
    async def test_rest_adapter_workflow(self, mock_get_session):
        """Test complete REST adapter workflow."""
        # Setup mock
        mock_session = MagicMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "result": "Generated code",
            "success": True,
            "error": None,
            "metadata": {
                "task_id": "test_123",
                "task_type": "code_generation",
                "timestamp": 1234567890.0,
                "model_name": "gpt-4"
            },
            "quality": None
        })
        
        # Create proper async context manager mock
        class AsyncContextManager:
            def __init__(self, return_value):
                self.return_value = return_value
            
            async def __aenter__(self):
                return self.return_value
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        mock_session.post.return_value = AsyncContextManager(mock_response)
        mock_session.get.return_value = AsyncContextManager(mock_response)
        mock_get_session.return_value = mock_session
        
        # Create adapter
        adapter = AdapterFactory.create_rest_adapter("http://localhost:8000")
        
        # Test workflow
        assert await adapter.is_available("code_generator") is True
        
        request = AgentRequest(task="Generate a function")
        response = await adapter.send_request("code_generator", request)
        
        assert response.result == "Generated code"
        assert response.success is True
        
        # Verify HTTP calls
        mock_session.get.assert_called_once_with("http://localhost:8000/agents/code_generator/health")
        mock_session.post.assert_called_once()
