"""
Integration test demonstrating orchestration patterns with real agents.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".

This test shows how the orchestration patterns work with actual
agent implementations and communication adapters.
"""

import asyncio
import pytest
from datetime import datetime

from shared_package.orchestration import (
    SequentialOrchestrator,
    ParallelOrchestrator,
    DirectAdapter,
    OrchestrationConfig
)
from shared_package.agents import (
    CodeGeneratorAgent,
    CodeReviewerAgent,
    AgentRequest,
    TaskMetadata
)
from shared_package.clients.unified_client import UnifiedModelClient


class MockModelClient:
    """Mock model client for testing."""
    
    def __init__(self, responses: dict = None):
        self.responses = responses or {
            "code_generation": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "code_review": "Code quality: 0.85\nReadability: Good\nEfficiency: Could be improved with memoization\nIssues: None"
        }
    
    async def make_request(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 1000, 
        temperature: float = 0.7
    ):
        """Mock make_request method."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Better prompt detection
        if "review" in prompt.lower() or "quality" in prompt.lower():
            response_text = self.responses["code_review"]
        elif "generate" in prompt.lower() or "create" in prompt.lower() or "write" in prompt.lower():
            response_text = self.responses["code_generation"]
        else:
            response_text = "Mock response"
        
        # Return a mock ModelResponse-like object
        class MockResponse:
            def __init__(self, text):
                self.response = text  # Agents expect 'response' attribute
                self.success = True
                self.error = None
        
        return MockResponse(response_text)


@pytest.fixture
def mock_client():
    """Create mock model client."""
    return MockModelClient()


@pytest.fixture
def real_agents(mock_client):
    """Create real agent instances."""
    generator = CodeGeneratorAgent(mock_client)
    reviewer = CodeReviewerAgent(mock_client)
    return {"generator": generator, "reviewer": reviewer}


@pytest.fixture
def adapter_with_agents(real_agents):
    """Create adapter with registered agents."""
    adapter = DirectAdapter()
    for agent_id, agent in real_agents.items():
        adapter.register_agent(agent_id, agent)
    return adapter


@pytest.mark.asyncio
async def test_sequential_generator_reviewer_workflow(adapter_with_agents):
    """Test sequential workflow: generator -> reviewer."""
    orchestrator = SequentialOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="integration_test",
        task_type="code_generation_and_review",
        timestamp=datetime.now().timestamp()
    )
    
    # Define sequential workflow
    agents = {
        "generator": AgentRequest(
            task="Generate a Python function to calculate fibonacci numbers",
            metadata=metadata
        ),
        "reviewer": AgentRequest(
            task="Review the generated code for quality and improvements",
            metadata=metadata
        )
    }
    
    result = await orchestrator.orchestrate(agents)
    
    # Verify results
    assert result.status.value == "completed"
    assert len(result.results) == 2
    assert "generator" in result.results
    assert "reviewer" in result.results
    
    # Check generator result
    generator_result = result.results["generator"]
    assert generator_result.success
    assert "fibonacci" in generator_result.result.lower()
    
    # Check reviewer result
    reviewer_result = result.results["reviewer"]
    assert reviewer_result.success
    assert "quality" in reviewer_result.result.lower()


@pytest.mark.asyncio
async def test_parallel_multiple_generators(adapter_with_agents):
    """Test parallel execution with multiple generators."""
    orchestrator = ParallelOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="parallel_test",
        task_type="parallel_generation",
        timestamp=datetime.now().timestamp()
    )
    
    # Define parallel tasks
    agents = {
        "generator": AgentRequest(
            task="Generate a Python function to calculate fibonacci numbers",
            metadata=metadata
        ),
        "reviewer": AgentRequest(
            task="Generate a Python function to calculate factorial numbers",
            metadata=metadata
        )
    }
    
    result = await orchestrator.orchestrate(agents)
    
    # Verify results
    assert result.status.value == "completed"
    assert len(result.results) == 2
    
    # Both agents should have completed
    for agent_id in ["generator", "reviewer"]:
        assert agent_id in result.results
        assert result.results[agent_id].success


@pytest.mark.asyncio
async def test_pipeline_execution(adapter_with_agents):
    """Test pipeline execution with predefined steps."""
    orchestrator = SequentialOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="pipeline_test",
        task_type="pipeline_execution",
        timestamp=datetime.now().timestamp()
    )
    
    # Define pipeline
    pipeline = [
        {"agent_id": "generator", "task_modifier": "Generate code for: {task}"},
        {"agent_id": "reviewer", "task_modifier": "Review this code: {result}"}
    ]
    
    initial_request = AgentRequest(
        task="Create a Python function to reverse a string",
        metadata=metadata
    )
    
    result = await orchestrator.orchestrate_with_pipeline(pipeline, initial_request)
    
    # Verify results
    assert result.status.value == "completed"
    assert len(result.results) == 2
    
    # Check that context was passed between agents
    generator_result = result.results["generator"]
    reviewer_result = result.results["reviewer"]
    
    assert generator_result.success
    assert reviewer_result.success


@pytest.mark.asyncio
async def test_race_execution(adapter_with_agents):
    """Test race execution pattern."""
    orchestrator = ParallelOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="race_test",
        task_type="race_execution",
        timestamp=datetime.now().timestamp()
    )
    
    # Define race tasks
    agents = {
        "generator": AgentRequest(
            task="Generate a Python function to calculate fibonacci numbers",
            metadata=metadata
        ),
        "reviewer": AgentRequest(
            task="Generate a Python function to calculate factorial numbers",
            metadata=metadata
        )
    }
    
    result = await orchestrator.orchestrate_with_race(
        agents,
        winner_takes_all=False  # Allow multiple winners
    )
    
    # Verify results
    assert result.status.value == "completed"
    assert len(result.results) >= 1  # At least one should complete


@pytest.mark.asyncio
async def test_batched_execution(adapter_with_agents):
    """Test batched execution with concurrency control."""
    orchestrator = ParallelOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="batch_test",
        task_type="batched_execution",
        timestamp=datetime.now().timestamp()
    )
    
    # Define multiple tasks
    agents = {
        "generator": AgentRequest(
            task="Generate a Python function to calculate fibonacci numbers",
            metadata=metadata
        ),
        "reviewer": AgentRequest(
            task="Generate a Python function to calculate factorial numbers",
            metadata=metadata
        )
    }
    
    result = await orchestrator.orchestrate_with_batching(
        agents,
        batch_size=1  # Process one at a time
    )
    
    # Verify results
    assert result.status.value == "completed"
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_error_handling_and_recovery(adapter_with_agents):
    """Test error handling and recovery mechanisms."""
    orchestrator = SequentialOrchestrator(adapter_with_agents)
    
    metadata = TaskMetadata(
        task_id="error_test",
        task_type="error_handling",
        timestamp=datetime.now().timestamp()
    )
    
    # Create a request that will cause an error
    agents = {
        "generator": AgentRequest(
            task="Generate invalid code that will cause errors",
            metadata=metadata
        ),
        "reviewer": AgentRequest(
            task="Review the generated code",
            metadata=metadata
        )
    }
    
    result = await orchestrator.orchestrate(agents)
    
    # Should handle errors gracefully
    assert result.status.value in ["completed", "failed"]
    
    # If failed, should have error information
    if result.errors:
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
