"""
Simple integration test for communication adapters.

Following Python Zen: "Simple is better than complex".
"""

import pytest
from unittest.mock import AsyncMock

from shared_package.orchestration.adapters import (
    AdapterType,
    AdapterConfig,
    DirectAdapter,
    RestAdapter,
    AdapterFactory
)
from shared_package.agents.schemas import AgentRequest, AgentResponse, TaskMetadata


class TestSimpleIntegration:
    """Simple integration tests for communication adapters."""
    
    @pytest.mark.asyncio
    async def test_direct_adapter_simple_workflow(self):
        """Test direct adapter with simple workflow."""
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
    
    def test_adapter_factory_creation(self):
        """Test adapter factory creates correct adapters."""
        # Test direct adapter creation
        direct_adapter = AdapterFactory.create_direct_adapter()
        assert isinstance(direct_adapter, DirectAdapter)
        assert direct_adapter.get_adapter_type() == AdapterType.DIRECT
        
        # Test REST adapter creation
        rest_adapter = AdapterFactory.create_rest_adapter("http://localhost:8000")
        assert isinstance(rest_adapter, RestAdapter)
        assert rest_adapter.get_adapter_type() == AdapterType.REST
        
        # Test adapter creation by type
        direct_adapter2 = AdapterFactory.create_adapter(AdapterType.DIRECT)
        assert isinstance(direct_adapter2, DirectAdapter)
        
        rest_adapter2 = AdapterFactory.create_adapter(
            AdapterType.REST,
            base_url="http://localhost:8000"
        )
        assert isinstance(rest_adapter2, RestAdapter)
    
    def test_adapter_config(self):
        """Test adapter configuration."""
        config = AdapterConfig(
            adapter_type=AdapterType.DIRECT,
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert config.adapter_type == AdapterType.DIRECT
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
