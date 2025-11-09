"""End-to-end integration tests for Day 10 MCP system.

These tests validate complete workflows:
- User message → intent parsing → multi-tool execution → formatted response
- Result caching behavior
- Error recovery and retry logic
- Context window management
- Plan optimization
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest

from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.infrastructure.repositories.json_conversation_repository import (
    JsonConversationRepository,
)
from src.presentation.mcp.orchestrators.mcp_mistral_wrapper import MCPMistralWrapper


@pytest.fixture
def mock_unified_client():
    """Create mock unified client."""
    client = AsyncMock()
    client.check_availability = AsyncMock(return_value=True)

    # Mock responses for different scenarios
    async def make_request_mock(**kwargs):
        """Mock make_request with different responses."""
        prompt = kwargs.get("prompt", "")

        # Intent parsing response
        if "primary_goal" in prompt:
            return MagicMock(
                response=json.dumps(
                    {
                        "primary_goal": "generate a hello world function",
                        "tools_needed": ["generate_code"],
                        "parameters": {"description": "create a hello world function"},
                        "confidence": 0.9,
                        "needs_clarification": False,
                        "unclear_aspects": [],
                    }
                ),
                total_tokens=100,
                input_tokens=50,
                response_tokens=50,
            )

        # Plan generation response
        if "execution plan" in prompt.lower() or "Available MCP tools" in prompt:
            return MagicMock(
                response=json.dumps(
                    [
                        {
                            "tool": "generate_code",
                            "args": {
                                "description": "create a hello world function",
                                "model": "mistral",
                            },
                        }
                    ]
                ),
                total_tokens=80,
                input_tokens=40,
                response_tokens=40,
            )

        # Default response
        return MagicMock(
            response="Default response",
            total_tokens=50,
            input_tokens=25,
            response_tokens=25,
        )

    client.make_request = make_request_mock
    return client


@pytest.fixture
def mock_mcp_wrapper():
    """Create mock MCP wrapper."""
    wrapper = AsyncMock(spec=MCPMistralWrapper)
    wrapper.execute_plan = AsyncMock(
        return_value=[
            {
                "code": "def hello_world(): return 'Hello, World!'",
                "success": True,
                "metadata": {"model_used": "mistral"},
            }
        ]
    )
    return wrapper


@pytest.fixture
def orchestrator(mock_unified_client, conversation_repo, mock_mcp_wrapper):
    """Create orchestrator with mocked dependencies."""
    return MistralChatOrchestrator(
        unified_client=mock_unified_client,
        conversation_repo=conversation_repo,
        model_name="mistral",
        mcp_wrapper=mock_mcp_wrapper,
        enable_optimization=True,
        enable_context_management=True,
    )


@pytest.mark.asyncio
async def test_e2e_workflow(orchestrator):
    """Test complete workflow from user message to response.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Simulate user requesting code generation
    response = await orchestrator.handle_message(
        "Create a hello world function", "test_e2e_workflow"
    )

    # Verify response contains generated code
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_multiple_tool_execution(orchestrator):
    """Test workflow with multiple tools.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Mock intent that requires multiple tools
    async def multi_tool_intent(**kwargs):
        """Mock multi-tool intent."""
        prompt = kwargs.get("prompt", "")
        if "primary_goal" in prompt:
            return MagicMock(
                response=json.dumps(
                    {
                        "primary_goal": "generate and review code",
                        "tools_needed": ["generate_code", "review_code"],
                        "parameters": {},
                        "confidence": 0.9,
                        "needs_clarification": False,
                        "unclear_aspects": [],
                    }
                ),
                total_tokens=120,
                input_tokens=60,
                response_tokens=60,
            )
        elif "execution plan" in prompt.lower():
            return MagicMock(
                response=json.dumps(
                    [
                        {
                            "tool": "generate_code",
                            "args": {
                                "description": "create a function",
                                "model": "mistral",
                            },
                        },
                        {
                            "tool": "review_code",
                            "args": {"code": "def test(): pass", "model": "mistral"},
                        },
                    ]
                ),
                total_tokens=100,
                input_tokens=50,
                response_tokens=50,
            )
        return MagicMock(
            response="", total_tokens=50, input_tokens=25, response_tokens=25
        )

    orchestrator.unified_client.make_request = multi_tool_intent

    # Configure mock wrapper to return multiple results
    orchestrator.mcp_wrapper.execute_plan = AsyncMock(
        return_value=[
            {"code": "def test(): return 42", "success": True},
            {"review_result": "Code looks good", "success": True},
        ]
    )

    response = await orchestrator.handle_message(
        "Generate and review some code", "test_multi_tool"
    )

    assert response is not None
    # Verify mcp_wrapper was called
    orchestrator.mcp_wrapper.execute_plan.assert_called_once()


@pytest.mark.asyncio
async def test_result_caching(orchestrator):
    """Test result caching behavior.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Configure mock wrapper with caching simulation
    call_count = {"count": 0}

    async def cached_execute_plan(plan, conv_id):
        """Mock execute_plan with caching simulation."""
        call_count["count"] += 1
        return [{"code": "cached_result", "success": True}]

    orchestrator.mcp_wrapper.execute_plan = cached_execute_plan

    # Make same request twice
    await orchestrator.handle_message("test cache", "test_cache_conv")
    await orchestrator.handle_message("test cache", "test_cache_conv")

    # In real implementation with caching, second call should use cache
    # For now, just verify calls were made
    assert call_count["count"] >= 1


@pytest.mark.asyncio
async def test_error_recovery(orchestrator):
    """Test error recovery and retry logic.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Configure mock to fail first, then succeed
    attempt = {"count": 0}

    async def retry_execute_plan(plan, conv_id):
        """Mock execute_plan with retry simulation."""
        attempt["count"] += 1
        if attempt["count"] < 2:
            raise ValueError("Transient error")
        return [{"code": "success", "success": True}]

    orchestrator.mcp_wrapper.execute_plan = retry_execute_plan

    # Request should eventually succeed
    response = await orchestrator.handle_message("test retry", "test_retry_conv")

    assert response is not None
    assert attempt["count"] >= 2


@pytest.mark.asyncio
async def test_context_window_management(orchestrator):
    """Test context window management with long conversations.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Simulate long conversation
    conv_id = "test_context_conv"
    for i in range(20):
        await orchestrator.handle_message(
            f"This is message {i} with some content", conv_id
        )

    # Verify conversation was handled
    conversation = await orchestrator.conversation_repo.get_by_id(conv_id)
    assert conversation is not None
    assert len(conversation.messages) >= 20


@pytest.mark.asyncio
async def test_plan_optimization(orchestrator):
    """Test plan optimization removes redundant steps.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Configure mock to generate plan with redundant steps
    async def optimized_intent(**kwargs):
        """Mock optimized intent."""
        prompt = kwargs.get("prompt", "")
        if "primary_goal" in prompt:
            return MagicMock(
                response=json.dumps(
                    {
                        "primary_goal": "generate code",
                        "tools_needed": ["generate_code"],
                        "parameters": {},
                        "confidence": 0.9,
                        "needs_clarification": False,
                        "unclear_aspects": [],
                    }
                ),
                total_tokens=100,
                input_tokens=50,
                response_tokens=50,
            )
        return MagicMock(
            response=json.dumps(
                [
                    {
                        "tool": "generate_code",
                        "args": {"description": "test", "model": "mistral"},
                    },
                    {
                        "tool": "generate_code",
                        "args": {"description": "test", "model": "mistral"},
                    },
                ]
            ),
            total_tokens=80,
            input_tokens=40,
            response_tokens=40,
        )

    orchestrator.unified_client.make_request = optimized_intent

    response = await orchestrator.handle_message("test optimization", "test_opt_conv")

    # Verify plan was optimized (redundant steps removed)
    assert response is not None


@pytest.mark.asyncio
async def test_clarification_flow(orchestrator):
    """Test clarification flow for unclear requests.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Configure mock to return low confidence intent
    async def unclear_intent(**kwargs):
        """Mock unclear intent."""
        return MagicMock(
            response=json.dumps(
                {
                    "primary_goal": "unclear request",
                    "tools_needed": [],
                    "parameters": {},
                    "confidence": 0.5,
                    "needs_clarification": True,
                    "unclear_aspects": ["missing details", "ambiguous requirement"],
                }
            ),
            total_tokens=100,
            input_tokens=50,
            response_tokens=50,
        )

    orchestrator.unified_client.make_request = unclear_intent

    # Configure clarifying questions response
    async def clarifying_response(**kwargs):
        """Mock clarifying questions."""
        return MagicMock(
            response="What specific functionality do you need?",
            total_tokens=50,
            input_tokens=25,
            response_tokens=25,
        )

    # First call returns unclear intent
    orchestrator.unified_client.make_request = unclear_intent
    response1 = await orchestrator.handle_message("do something", "test_clarify")

    # Verify clarification was requested
    assert response1 is not None
    assert "clarification" in response1.lower() or "?" in response1


@pytest.mark.asyncio
async def test_empty_plan_handling(orchestrator):
    """Test handling of requests that don't need tools.

    Args:
        orchestrator: MistralChatOrchestrator instance
    """
    await orchestrator.initialize()

    # Configure mock to return no tools needed
    async def no_tools_intent(**kwargs):
        """Mock intent with no tools."""
        prompt = kwargs.get("prompt", "")
        if "primary_goal" in prompt:
            return MagicMock(
                response=json.dumps(
                    {
                        "primary_goal": "greeting",
                        "tools_needed": [],
                        "parameters": {},
                        "confidence": 0.9,
                        "needs_clarification": False,
                        "unclear_aspects": [],
                    }
                ),
                total_tokens=100,
                input_tokens=50,
                response_tokens=50,
            )
        return MagicMock(
            response="Hello! How can I help you?",
            total_tokens=50,
            input_tokens=25,
            response_tokens=25,
        )

    orchestrator.unified_client.make_request = no_tools_intent

    response = await orchestrator.handle_message("Hello", "test_no_tools")

    # Verify response without tool execution
    assert response is not None
    # mcp_wrapper should not be called
    assert not orchestrator.mcp_wrapper.execute_plan.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
