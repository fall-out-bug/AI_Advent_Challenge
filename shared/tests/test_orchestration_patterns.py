"""
Comprehensive tests for orchestration patterns.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".

Tests cover all orchestration patterns with proper mocking,
error handling, edge cases, and adapter pattern switching.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from shared_package.orchestration import (
    BaseOrchestrator,
    SequentialOrchestrator,
    ParallelOrchestrator
)
from shared_package.orchestration.adapters import (
    DirectAdapter,
    RestAdapter,
    CommunicationAdapter,
    AdapterType
)
from shared_package.agents import (
    CodeGeneratorAgent,
    CodeReviewerAgent,
    AgentRequest,
    AgentResponse,
    TaskMetadata,
    QualityMetrics
)
from shared_package.clients.unified_client import UnifiedModelClient
from shared_package.clients.base_client import ModelResponse
from shared_package.exceptions.model_errors import ModelConnectionError


@pytest.fixture
def mock_client():
    """Create mock UnifiedModelClient."""
    return MagicMock(spec=UnifiedModelClient)


@pytest.fixture
def mock_model_response():
    """Create mock model response."""
    return ModelResponse(
        response="```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
        response_tokens=25,
        input_tokens=15,
        total_tokens=40,
        model_name="qwen",
        response_time=1.5
    )


@pytest.fixture
def mock_review_response():
    """Create mock review response."""
    return ModelResponse(
        response="This code is well-structured and follows Python best practices.",
        response_tokens=20,
        input_tokens=30,
        total_tokens=50,
        model_name="mistral",
        response_time=2.0
    )


@pytest.fixture
def direct_adapter():
    """Create DirectAdapter for testing."""
    return DirectAdapter()


@pytest.fixture
def rest_adapter():
    """Create RestAdapter for testing."""
    return RestAdapter(base_url="http://localhost:8000")


@pytest.fixture
def generator_agent(mock_model_response):
    """Create CodeGeneratorAgent for testing."""
    mock_client = MagicMock(spec=UnifiedModelClient)
    mock_client.make_request = AsyncMock(return_value=mock_model_response)
    return CodeGeneratorAgent(mock_client, model_name="qwen")


@pytest.fixture
def reviewer_agent(mock_review_response):
    """Create CodeReviewerAgent for testing."""
    mock_client = MagicMock(spec=UnifiedModelClient)
    mock_client.make_request = AsyncMock(return_value=mock_review_response)
    return CodeReviewerAgent(mock_client, model_name="mistral")


@pytest.fixture
def sample_request():
    """Create sample agent request."""
    return AgentRequest(
        task_id="test_001",
        task_type="code_generation",
        task="Create a Python function to calculate fibonacci",
        context={"language": "python", "style": "recursive"},
        timestamp=datetime.now()
    )


class MockAgent:
    """Mock agent for testing orchestration patterns."""
    
    def __init__(self, agent_id: str, success: bool = True, delay: float = 0.0):
        self.agent_id = agent_id
        self.success = success
        self.delay = delay
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Mock agent processing."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        self.stats["total_requests"] += 1
        
        if self.success:
            self.stats["successful_requests"] += 1
            return AgentResponse(
                task_id=request.task_id,
                result=f"Mock result from {self.agent_id}",
                success=True,
                metadata=TaskMetadata(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    agent_name=self.agent_id,
                    model_name="mock_model",
                    timestamp=datetime.now()
                )
            )
        else:
            self.stats["failed_requests"] += 1
            return AgentResponse(
                task_id=request.task_id,
                result=None,
                success=False,
                error=f"Mock error from {self.agent_id}",
                metadata=TaskMetadata(
                    task_id=request.task_id,
                    task_type=request.task_type,
                    agent_name=self.agent_id,
                    model_name="mock_model",
                    timestamp=datetime.now()
                )
            )
    
    def get_stats(self):
        """Get agent statistics."""
        return {
            "agent_name": self.agent_id,
            **self.stats
        }


class TestDirectAdapter:
    """Test DirectAdapter functionality."""
    
    def test_direct_adapter_initialization(self):
        """Test DirectAdapter initialization."""
        adapter = DirectAdapter()
        assert adapter.adapter_type == "direct"
        assert adapter.get_adapter_type() == AdapterType.DIRECT
    
    @pytest.mark.asyncio
    async def test_direct_adapter_send_request(self, generator_agent, sample_request):
        """Test DirectAdapter send_request."""
        adapter = DirectAdapter()
        adapter.register_agent("generator", generator_agent)
        
        result = await adapter.send_request("generator", sample_request)
        
        assert result.success is True
        assert "fibonacci" in result.result
    
    @pytest.mark.asyncio
    async def test_direct_adapter_error_handling(self, mock_client):
        """Test DirectAdapter error handling."""
        # Create agent that will fail
        mock_client.make_request = AsyncMock(side_effect=ModelConnectionError("Connection failed"))
        failing_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        
        adapter = DirectAdapter()
        adapter.register_agent("failing_agent", failing_agent)
        
        request = AgentRequest(
            task_id="error_001",
            task_type="code_generation",
            task="This will fail"
        )
        
        result = await adapter.send_request("failing_agent", request)
        assert result.success is False
        assert "Connection failed" in result.error


class TestRestAdapter:
    """Test RestAdapter functionality."""
    
    def test_rest_adapter_initialization(self):
        """Test RestAdapter initialization."""
        adapter = RestAdapter(base_url="http://localhost:8000")
        assert adapter.adapter_type == "rest"
        assert adapter.base_url == "http://localhost:8000"
    
    def test_rest_adapter_get_adapter_type(self):
        """Test RestAdapter adapter type."""
        adapter = RestAdapter(base_url="http://localhost:8000")
        assert adapter.get_adapter_type() == AdapterType.REST
    
    @pytest.mark.asyncio
    async def test_rest_adapter_send_request_mock(self, sample_request):
        """Test RestAdapter send_request with mocked HTTP."""
        adapter = RestAdapter(base_url="http://localhost:8000")
        
        # Mock HTTP response
        with patch('shared_package.orchestration.adapters.RestAdapter._get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "result": "Generated code",
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
            
            mock_session.post.return_value = AsyncContextManager(mock_response)
            mock_get_session.return_value = mock_session
            
            result = await adapter.send_request("test_agent", sample_request)
            
            assert result.success is True
            assert result.result == "Generated code"


class TestSequentialOrchestrator:
    """Test SequentialOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_sequential_execution_success(self, direct_adapter, generator_agent, reviewer_agent, sample_request):
        """Test successful sequential execution."""
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        agents = [generator_agent, reviewer_agent]
        result = await orchestrator.execute(sample_request, agents)
        
        assert len(result) == 2
        assert result[0].success is True
        assert result[1].success is True
        assert "fibonacci" in result[0].result
        assert "well-structured" in result[1].result.lower()
    
    @pytest.mark.asyncio
    async def test_sequential_execution_with_failure(self, direct_adapter, mock_client):
        """Test sequential execution with agent failure."""
        # Create failing agent
        mock_client.make_request = AsyncMock(side_effect=ModelConnectionError("Connection failed"))
        failing_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        request = AgentRequest(
            task_id="fail_001",
            task_type="code_generation",
            task="This will fail"
        )
        
        result = await orchestrator.execute(request, [failing_agent])
        
        assert len(result) == 1
        assert result[0].success is False
        assert "Connection failed" in result[0].error
    
    @pytest.mark.asyncio
    async def test_sequential_execution_empty_agents(self, direct_adapter, sample_request):
        """Test sequential execution with empty agent list."""
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        result = await orchestrator.execute(sample_request, [])
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_sequential_execution_cancellation(self, direct_adapter, generator_agent, sample_request):
        """Test sequential execution cancellation."""
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        # Start execution
        task = asyncio.create_task(
            orchestrator.execute(sample_request, [generator_agent])
        )
        
        # Cancel immediately
        orchestrator.cancel()
        
        result = await task
        
        # Should handle cancellation gracefully
        assert len(result) == 0 or result[0].success is False


class TestParallelOrchestrator:
    """Test ParallelOrchestrator functionality."""
    
    @pytest.mark.asyncio
    async def test_parallel_execution_success(self, direct_adapter, generator_agent, reviewer_agent, sample_request):
        """Test successful parallel execution."""
        orchestrator = ParallelOrchestrator(direct_adapter)
        
        agents = [generator_agent, reviewer_agent]
        result = await orchestrator.execute(sample_request, agents)
        
        assert len(result) == 2
        assert result[0].success is True
        assert result[1].success is True
        # Both should complete (parallel execution)
        assert "fibonacci" in result[0].result
        assert "well-structured" in result[1].result.lower()
    
    @pytest.mark.asyncio
    async def test_parallel_execution_with_failure(self, direct_adapter, mock_client, sample_request):
        """Test parallel execution with agent failure."""
        # Create mixed success/failure agents
        mock_client.make_request = AsyncMock(side_effect=[
            ModelResponse(response="Success", response_tokens=10, input_tokens=5, total_tokens=15, model_name="qwen", response_time=1.0),
            ModelConnectionError("Connection failed")
        ])
        
        success_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        failing_agent = CodeReviewerAgent(mock_client, model_name="mistral")
        
        orchestrator = ParallelOrchestrator(direct_adapter)
        
        result = await orchestrator.execute(sample_request, [success_agent, failing_agent])
        
        assert len(result) == 2
        # One should succeed, one should fail
        success_count = sum(1 for r in result if r.success)
        failure_count = sum(1 for r in result if not r.success)
        assert success_count == 1
        assert failure_count == 1
    
    @pytest.mark.asyncio
    async def test_parallel_execution_timeout(self, direct_adapter, mock_client, sample_request):
        """Test parallel execution timeout."""
        # Create slow agent
        slow_response = ModelResponse(
            response="Slow response",
            response_tokens=10,
            input_tokens=5,
            total_tokens=15,
            model_name="qwen",
            response_time=2.0
        )
        
        async def slow_request(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate slow response
            return slow_response
        
        mock_client.make_request = AsyncMock(side_effect=slow_request)
        slow_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        
        from shared_package.orchestration.base_orchestrator import OrchestrationConfig
        config = OrchestrationConfig(timeout=1.0)
        orchestrator = ParallelOrchestrator(direct_adapter, config=config)
        
        result = await orchestrator.execute(sample_request, [slow_agent])
        
        # Should timeout
        assert len(result) == 1
        assert result[0].success is False
        assert "timeout" in result[0].error.lower()
    
    @pytest.mark.asyncio
    async def test_parallel_execution_empty_agents(self, direct_adapter, sample_request):
        """Test parallel execution with empty agent list."""
        orchestrator = ParallelOrchestrator(direct_adapter)
        
        result = await orchestrator.execute(sample_request, [])
        
        assert len(result) == 0


class TestOrchestrationIntegration:
    """Integration tests for orchestration patterns."""
    
    @pytest.mark.asyncio
    async def test_generator_to_reviewer_workflow(self, direct_adapter):
        """Test complete workflow from generation to review."""
        # Create a separate generator agent with factorial mock
        mock_client = MagicMock(spec=UnifiedModelClient)
        factorial_response = ModelResponse(
            response="```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)\n```",
            response_tokens=25,
            input_tokens=15,
            total_tokens=40,
            model_name="qwen",
            response_time=1.5
        )
        mock_client.make_request = AsyncMock(return_value=factorial_response)
        factorial_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        
        # Create reviewer agent
        mock_review_client = MagicMock(spec=UnifiedModelClient)
        review_response = ModelResponse(
            response="This code is well-structured and follows Python best practices.",
            response_tokens=20,
            input_tokens=30,
            total_tokens=50,
            model_name="mistral",
            response_time=2.0
        )
        mock_review_client.make_request = AsyncMock(return_value=review_response)
        reviewer_agent = CodeReviewerAgent(mock_review_client, model_name="mistral")
        
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        # First generate code
        gen_request = AgentRequest(
            task_id="workflow_001",
            task_type="code_generation",
            task="Create a Python function to calculate factorial",
            context={"language": "python", "style": "recursive"}
        )
        
        gen_result = await orchestrator.execute(gen_request, [factorial_agent])
        assert gen_result[0].success is True
        assert "factorial" in gen_result[0].result.lower()
        
        # Then review the generated code
        review_request = AgentRequest(
            task_id="workflow_002",
            task_type="code_review",
            task=gen_result[0].result,
            context={"language": "python", "focus_areas": ["readability", "performance"]}
        )
        
        review_result = await orchestrator.execute(review_request, [reviewer_agent])
        assert review_result[0].success is True
        assert "well-structured" in review_result[0].result.lower()
    
    @pytest.mark.asyncio
    async def test_model_comparison_workflow(self, direct_adapter, sample_request):
        """Test parallel execution for model comparison."""
        # Create multiple generators with different models and separate mock clients
        mock_responses = [
            ModelResponse(response="Qwen result", response_tokens=10, input_tokens=5, total_tokens=15, model_name="qwen", response_time=1.0),
            ModelResponse(response="Mistral result", response_tokens=10, input_tokens=5, total_tokens=15, model_name="mistral", response_time=1.2),
            ModelResponse(response="TinyLlama result", response_tokens=10, input_tokens=5, total_tokens=15, model_name="tinyllama", response_time=0.8)
        ]
        
        agents = []
        for i, response in enumerate(mock_responses):
            mock_client = MagicMock(spec=UnifiedModelClient)
            mock_client.make_request = AsyncMock(return_value=response)
            agent = CodeGeneratorAgent(mock_client, model_name=response.model_name)
            # Set unique agent_name to avoid conflicts
            agent.agent_name = f"code_generator_{response.model_name}"
            agents.append(agent)
        
        orchestrator = ParallelOrchestrator(direct_adapter)
        
        result = await orchestrator.execute(sample_request, agents)
        
        assert len(result) == 3
        assert all(r.success for r in result)
        
        # Verify different models were used
        model_names = [r.metadata.model_name for r in result]
        assert "qwen" in model_names
        assert "mistral" in model_names
        assert "tinyllama" in model_names
    
    @pytest.mark.asyncio
    async def test_adapter_switching(self, generator_agent, sample_request):
        """Test switching between different adapters."""
        # Test DirectAdapter
        direct_adapter = DirectAdapter()
        direct_adapter.register_agent("code_generator", generator_agent)
        direct_orchestrator = SequentialOrchestrator(direct_adapter)
        
        direct_result = await direct_orchestrator.execute(sample_request, [generator_agent])
        assert direct_result[0].success is True
        
        # Test RestAdapter (with mocked HTTP) - this simulates calling a remote agent
        rest_adapter = RestAdapter(base_url="http://localhost:8000")
        rest_orchestrator = SequentialOrchestrator(rest_adapter)
        
        with patch('shared_package.orchestration.adapters.RestAdapter._get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "success": True,
                "result": "REST generated code",
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
            mock_session.get.return_value = AsyncContextManager(mock_response)  # For health check
            mock_get_session.return_value = mock_session
            
            # Create a mock agent that will be "called" via REST
            mock_rest_agent = MagicMock()
            mock_rest_agent.agent_name = "code_generator"
            mock_rest_agent.agent_id = "code_generator"
            
            rest_result = await rest_orchestrator.execute(sample_request, [mock_rest_agent])
            assert rest_result[0].success is True
            assert rest_result[0].result == "REST generated code"
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, direct_adapter, mock_client, sample_request):
        """Test error propagation through orchestration."""
        # Create failing agent
        mock_client.make_request = AsyncMock(side_effect=ModelConnectionError("Network error"))
        failing_agent = CodeGeneratorAgent(mock_client, model_name="qwen")
        
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        result = await orchestrator.execute(sample_request, [failing_agent])
        
        assert len(result) == 1
        assert result[0].success is False
        assert "Network error" in result[0].error
    
    @pytest.mark.asyncio
    async def test_statistics_aggregation(self, direct_adapter, generator_agent, reviewer_agent, sample_request):
        """Test statistics aggregation across orchestration."""
        orchestrator = SequentialOrchestrator(direct_adapter)
        
        # Execute workflow
        result = await orchestrator.execute(sample_request, [generator_agent, reviewer_agent])
        
        # Verify statistics are updated
        gen_stats = generator_agent.get_stats()
        rev_stats = reviewer_agent.get_stats()
        
        assert gen_stats["total_requests"] >= 1
        assert rev_stats["total_requests"] >= 1
        assert gen_stats["successful_requests"] >= 1
        assert rev_stats["successful_requests"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
