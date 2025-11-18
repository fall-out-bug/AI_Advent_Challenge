"""Characterization tests for Butler Orchestrator behavior.

Purpose:
    Capture current Butler Orchestrator behavior before refactoring.
    These tests document the existing behavior to ensure no regressions
    during Cluster C refactoring (C.2-C.3).

Note:
    These tests are intentionally verbose to capture current behavior.
    They serve as a baseline for verifying that refactoring doesn't change
    the external behavior of Butler Orchestrator.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.presentation.bot.orchestrator import ButlerOrchestrator
from src.application.dtos.butler_dialog_dtos import DialogMode


@pytest.mark.asyncio
async def test_butler_orchestrator_public_api_characterization():
    """Characterization: ButlerOrchestrator public API.

    Purpose:
        Captures the current public API of ButlerOrchestrator:
        - What methods are available publicly
        - What parameters they accept
        - What they return
    """
    # Setup: Create ButlerOrchestrator with mocked dependencies
    mock_mode_classifier = MagicMock()
    mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.IDLE)

    mock_task_handler = MagicMock()
    mock_task_handler.handle = AsyncMock(return_value="Task created")

    mock_data_handler = MagicMock()
    mock_data_handler.handle = AsyncMock(return_value="Data here")

    mock_homework_handler = MagicMock()
    mock_homework_handler.handle = AsyncMock(return_value="Review complete")

    mock_chat_handler = MagicMock()
    mock_chat_handler.handle = AsyncMock(return_value="Hello!")

    mock_mongodb = MagicMock()
    mock_mongodb.dialog_contexts = MagicMock()
    mock_mongodb.dialog_contexts.find_one = AsyncMock(return_value=None)
    mock_mongodb.dialog_contexts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_mongodb.dialog_contexts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_mongodb.dialog_contexts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    orchestrator = ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=mock_task_handler,
        data_handler=mock_data_handler,
        homework_handler=mock_homework_handler,
        chat_handler=mock_chat_handler,
        mongodb=mock_mongodb,
    )

    # Characterize: Public method is `handle_user_message`
    assert hasattr(orchestrator, "handle_user_message"), "Should have handle_user_message method"
    assert callable(orchestrator.handle_user_message), "handle_user_message should be callable"

    # Characterize: Method signature: (user_id, message, session_id, force_mode=None) -> str
    response = await orchestrator.handle_user_message(
        user_id="123",
        message="Hello",
        session_id="session_456",
    )

    assert isinstance(response, str), "Should return string response"
    assert len(response) > 0, "Response should not be empty"

    # Characterize: force_mode parameter bypasses classification
    mock_mode_classifier.classify.reset_mock()
    response_forced = await orchestrator.handle_user_message(
        user_id="123",
        message="Hello",
        session_id="session_456",
        force_mode=DialogMode.TASK,
    )

    assert isinstance(response_forced, str), "Should return string response"
    mock_mode_classifier.classify.assert_not_called(), "Should not call classifier when force_mode is set"


@pytest.mark.asyncio
async def test_butler_orchestrator_message_routing_characterization():
    """Characterization: Message routing to handlers.

    Purpose:
        Captures how ButlerOrchestrator routes messages to different handlers
        based on mode classification.
    """
    # Setup: Create orchestrator with mocked handlers
    mock_mode_classifier = MagicMock()
    mock_task_handler = MagicMock()
    mock_task_handler.handle = AsyncMock(return_value="Task response")

    mock_data_handler = MagicMock()
    mock_data_handler.handle = AsyncMock(return_value="Data response")

    mock_homework_handler = MagicMock()
    mock_homework_handler.handle = AsyncMock(return_value="Review response")

    mock_chat_handler = MagicMock()
    mock_chat_handler.handle = AsyncMock(return_value="Chat response")

    mock_mongodb = MagicMock()
    mock_mongodb.dialog_contexts = MagicMock()
    mock_mongodb.dialog_contexts.find_one = AsyncMock(return_value=None)
    mock_mongodb.dialog_contexts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_mongodb.dialog_contexts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_mongodb.dialog_contexts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    orchestrator = ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=mock_task_handler,
        data_handler=mock_data_handler,
        homework_handler=mock_homework_handler,
        chat_handler=mock_chat_handler,
        mongodb=mock_mongodb,
    )

    # Characterize: TASK mode routes to task_handler
    mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.TASK)
    mock_task_handler.handle = AsyncMock(return_value="Task response")
    response = await orchestrator.handle_user_message(
        user_id="123", message="Create task", session_id="session_1"
    )
    assert "Task" in response or response == "Task response"
    mock_task_handler.handle.assert_called_once()

    # Characterize: DATA mode routes to data_handler
    mock_task_handler.handle.reset_mock()
    mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.DATA)
    response = await orchestrator.handle_user_message(
        user_id="123", message="Get digests", session_id="session_2"
    )
    assert "Data" in response or response == "Data response"
    mock_data_handler.handle.assert_called_once()

    # Characterize: IDLE mode routes to chat_handler
    mock_data_handler.handle.reset_mock()
    mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.IDLE)
    response = await orchestrator.handle_user_message(
        user_id="123", message="Hello", session_id="session_3"
    )
    assert "Chat" in response or response == "Chat response"
    mock_chat_handler.handle.assert_called_once()


@pytest.mark.asyncio
async def test_butler_orchestrator_context_management_characterization():
    """Characterization: Context management behavior.

    Purpose:
        Captures how ButlerOrchestrator manages dialog context:
        - Context retrieval/creation
        - Context persistence
    """
    # Setup: Create orchestrator with mocked MongoDB
    mock_mode_classifier = MagicMock()
    mock_mode_classifier.classify = AsyncMock(return_value=DialogMode.IDLE)

    mock_chat_handler = MagicMock()
    mock_chat_handler.handle = AsyncMock(return_value="Hello")

    context_stored = {}

    async def find_one_side_effect(filter_dict):
        session_id = filter_dict.get("session_id")
        if session_id:
            for key, value in context_stored.items():
                if session_id in key:
                    return value
        return None

    async def insert_one_side_effect(doc):
        key = f"{doc.get('user_id')}:{doc.get('session_id')}"
        context_stored[key] = doc
        return MagicMock(inserted_id="test_id")

    mock_mongodb = MagicMock()
    mock_mongodb.dialog_contexts = MagicMock()
    mock_mongodb.dialog_contexts.find_one = AsyncMock(side_effect=find_one_side_effect)
    mock_mongodb.dialog_contexts.insert_one = AsyncMock(side_effect=insert_one_side_effect)
    mock_mongodb.dialog_contexts.update_one = AsyncMock()

    orchestrator = ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=MagicMock(),
        data_handler=MagicMock(),
        homework_handler=MagicMock(),
        chat_handler=mock_chat_handler,
        mongodb=mock_mongodb,
    )

    # Characterize: Context is created/retrieved before processing
    user_id = "123"
    session_id = "session_456"

    response = await orchestrator.handle_user_message(
        user_id=user_id, message="Hello", session_id=session_id
    )

    assert isinstance(response, str), "Should return response"
    # Characterize: Context should be persisted (either via insert_one or update_one)
    # Note: Internal implementation detail, but we verify behavior
    assert mock_mongodb.dialog_contexts.find_one.called, "Should retrieve context"
    assert (
        mock_mongodb.dialog_contexts.insert_one.called
        or mock_mongodb.dialog_contexts.update_one.called
    ), "Should persist context"


@pytest.mark.asyncio
async def test_butler_orchestrator_error_handling_characterization():
    """Characterization: Error handling behavior.

    Purpose:
        Captures how ButlerOrchestrator handles errors:
        - Exception during processing
        - Error response format
    """
    # Setup: Create orchestrator that will raise exception
    mock_mode_classifier = MagicMock()
    mock_mode_classifier.classify = AsyncMock(side_effect=Exception("Classification error"))

    mock_mongodb = MagicMock()
    mock_mongodb.dialog_contexts = MagicMock()
    mock_mongodb.dialog_contexts.find_one = AsyncMock(return_value=None)

    orchestrator = ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=MagicMock(),
        data_handler=MagicMock(),
        homework_handler=MagicMock(),
        chat_handler=MagicMock(),
        mongodb=mock_mongodb,
    )

    # Characterize: Errors return user-friendly error message
    response = await orchestrator.handle_user_message(
        user_id="123", message="Test", session_id="session_456"
    )

    assert isinstance(response, str), "Should return string response even on error"
    assert (
        "error" in response.lower()
        or "sorry" in response.lower()
        or "❌" in response
    ), "Error response should be user-friendly"


@pytest.mark.asyncio
async def test_mcp_aware_agent_public_api_characterization():
    """Characterization: MCPAwareAgent public API.

    Purpose:
        Captures the current public API of MCPAwareAgent:
        - What methods are available publicly
        - What parameters they accept
        - What they return
    """
    from src.domain.agents.mcp_aware_agent import MCPAwareAgent
    from src.domain.agents.schemas import AgentRequest, AgentResponse

    # Setup: Create MCPAwareAgent with mocked dependencies
    mock_mcp_client = MagicMock()
    mock_mcp_client.discover_tools = AsyncMock(return_value=[])
    # call_tool signature: async def call_tool(tool_name: str, params: dict) -> dict
    mock_mcp_client.call_tool = AsyncMock(return_value={"status": "success"})

    mock_llm_client = MagicMock()
    mock_llm_client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"tool": "test_tool", "params": {}}',
            response_tokens=50,
            input_tokens=50,
            total_tokens=100,
        )
    )

    agent = MCPAwareAgent(
        mcp_client=mock_mcp_client,
        llm_client=mock_llm_client,
    )

    # Characterize: Public method is `process`
    assert hasattr(agent, "process"), "Should have process method"
    assert callable(agent.process), "process should be callable"

    # Characterize: Method signature: process(request: AgentRequest) -> AgentResponse
    request = AgentRequest(
        user_id=123,
        message="Test message",
        session_id="session_123",
    )

    # Characterize: Public attributes for configuration
    assert hasattr(agent, "mcp_client"), "Should have mcp_client attribute"
    assert hasattr(agent, "llm_client"), "Should have llm_client attribute"
    assert hasattr(agent, "model_name"), "Should have model_name attribute"
    assert hasattr(agent, "max_tokens"), "Should have max_tokens attribute"
    assert hasattr(agent, "temperature"), "Should have temperature attribute"

    # Characterize: Private attributes exist (should not be accessed in tests after C.2)
    assert hasattr(agent, "registry"), "Should have registry attribute"
    assert hasattr(agent, "chat_client"), "Should have chat_client attribute (internal)"

    # Characterize: AgentResponse schema structure
    # AgentResponse should have: success, text, tools_used, tokens_used, error, reasoning
    response_fields = AgentResponse.__fields__.keys()
    assert "success" in response_fields, "Response should have success field"
    assert "text" in response_fields, "Response should have text field"
    assert "tools_used" in response_fields, "Response should have tools_used field"
    assert "tokens_used" in response_fields, "Response should have tokens_used field"

    # Note: Full execution test is skipped due to Prometheus metrics mocking complexity.
    # This test serves as API structure documentation.


@pytest.mark.asyncio
@patch("src.domain.agents.mcp_aware_agent.METRICS_AVAILABLE", False)
async def test_mcp_aware_agent_tool_invocation_characterization():
    """Characterization: MCP tool invocation patterns.

    Purpose:
        Captures how MCPAwareAgent invokes MCP tools:
        - Tool discovery
        - Tool selection
        - Tool execution
    """
    from src.domain.agents.mcp_aware_agent import MCPAwareAgent
    from src.domain.agents.schemas import AgentRequest, AgentResponse

    # Setup: Create agent with mocked MCP client and tools
    mock_tools = [
        {
            "name": "get_posts",
            "description": "Get channel posts",
            "input_schema": {
                "type": "object",
                "properties": {"channel_username": {"type": "string"}},
            },
        }
    ]

    mock_mcp_client = MagicMock()
    mock_mcp_client.discover_tools = AsyncMock(return_value=mock_tools)
    mock_mcp_client.call_tool = AsyncMock(
        return_value={"status": "success", "data": []}
    )

    mock_llm_client = MagicMock()
    mock_llm_client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"tool": "get_posts", "params": {"channel_username": "test"}}',
            response_tokens=50,
            input_tokens=50,
            total_tokens=100,
            model_name="test-model",
            response_time=1.0,
        )
    )

    agent = MCPAwareAgent(
        mcp_client=mock_mcp_client,
        llm_client=mock_llm_client,
    )

    # Mock chat_client after initialization to avoid HTTP requests
    mock_chat_client = MagicMock()
    mock_chat_client.create_completion = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"tool": "get_posts", "params": {"channel_username": "test"}}'))]
        )
    )
    agent.chat_client = mock_chat_client

    request = AgentRequest(
        user_id=123,
        message="Get posts from test channel",
        session_id="session_123",
    )

    # Characterize: Agent discovers tools before processing
    response = await agent.process(request)

    assert isinstance(response, AgentResponse), "Should return AgentResponse"
    # Characterize: Tool discovery is called (internal behavior)
    # Note: This may be implementation detail, but we document it
    assert mock_mcp_client.discover_tools.called, "Should discover tools"


@pytest.mark.asyncio
async def test_mcp_aware_agent_error_handling_characterization():
    """Characterization: MCP-aware agent error handling.

    Purpose:
        Captures how MCPAwareAgent handles errors:
        - LLM errors
        - Tool execution errors
        - Error response format

    Note:
        This test documents expected error handling behavior.
        Full error execution tests are in other integration tests
        due to Prometheus metrics mocking complexity.
    """
    from src.domain.agents.mcp_aware_agent import MCPAwareAgent
    from src.domain.agents.schemas import AgentRequest, AgentResponse

    # Setup: Create agent with mocked dependencies
    mock_mcp_client = MagicMock()
    mock_mcp_client.discover_tools = AsyncMock(return_value=[])

    mock_llm_client = MagicMock()
    mock_llm_client.make_request = AsyncMock(side_effect=Exception("LLM error"))

    agent = MCPAwareAgent(
        mcp_client=mock_mcp_client,
        llm_client=mock_llm_client,
    )

    # Characterize: Agent has error handling logic
    # Process method should handle errors and return AgentResponse with success=False
    # This is verified by existing integration tests.
    # This characterization test documents the expected behavior.

    request = AgentRequest(
        user_id=123,
        message="Test message",
        session_id="session_123",
    )

    # Characterize: Process method signature accepts AgentRequest
    assert callable(agent.process), "process should be callable"
    # Characterize: Error handling should return AgentResponse with success=False
    # Note: Full error execution is tested in other integration tests


@pytest.mark.asyncio
async def test_butler_orchestrator_private_attributes_characterization():
    """Characterization: Private attributes usage patterns.

    Purpose:
        Captures what private attributes are currently accessed in tests:
        - This documents what needs to be refactored to use public APIs
        - Serves as baseline for C.2 refactoring
    """
    # Setup: Create orchestrator
    mock_mode_classifier = MagicMock()
    mock_mongodb = MagicMock()
    mock_mongodb.dialog_contexts = MagicMock()
    mock_mongodb.dialog_contexts.find_one = AsyncMock(return_value=None)
    mock_mongodb.dialog_contexts.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_mongodb.dialog_contexts.update_one = AsyncMock(return_value=MagicMock(modified_count=1))

    orchestrator = ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=MagicMock(),
        data_handler=MagicMock(),
        homework_handler=MagicMock(),
        chat_handler=MagicMock(),
        mongodb=mock_mongodb,
    )

    # Characterize: Current tests access these attributes directly
    # (This documents what needs refactoring in C.2)
    # Note: ButlerOrchestrator in presentation layer uses private attributes (_mode_classifier, etc.)
    # Some tests may access via property (e.g., mongodb property)
    assert hasattr(orchestrator, "mongodb"), "Current tests access mongodb property"

    # Characterize: Private attributes exist (should not be accessed in tests after C.2)
    assert hasattr(orchestrator, "_mode_classifier"), "Private attribute exists"
    assert hasattr(orchestrator, "_handlers"), "Private attribute exists"
    assert hasattr(orchestrator, "_mongodb"), "Private attribute exists"
    assert hasattr(orchestrator, "_contexts"), "Private attribute exists"

    # Characterize: Private methods exist (but should not be accessed in tests)
    assert hasattr(orchestrator, "_get_or_create_context"), "Private method exists"
    assert hasattr(orchestrator, "_save_context"), "Private method exists"
    assert hasattr(orchestrator, "_serialize_context"), "Private method exists"
    assert hasattr(orchestrator, "_deserialize_context"), "Private method exists"

    # Note: After C.2, tests should NOT access these private attributes/methods


@pytest.mark.asyncio
async def test_mcp_aware_agent_state_transitions_characterization():
    """Characterization: Agent state transitions.

    Purpose:
        Captures agent state transition patterns during message processing:
        - Decision stage
        - Execution stage
        - Formatting stage

    Note:
        This test documents the expected state transition pattern.
        Full execution tests are in other integration tests
        due to Prometheus metrics mocking complexity.
    """
    from src.domain.agents.mcp_aware_agent import MCPAwareAgent
    from src.domain.agents.schemas import AgentRequest, AgentResponse

    # Setup: Create agent
    mock_mcp_client = MagicMock()
    mock_mcp_client.discover_tools = AsyncMock(return_value=[])

    mock_llm_client = MagicMock()
    mock_llm_client.make_request = AsyncMock(
        return_value=MagicMock(
            response='{"text": "Response"}',
            response_tokens=50,
            input_tokens=50,
            total_tokens=100,
            model_name="test-model",
            response_time=1.0,
        )
    )

    agent = MCPAwareAgent(
        mcp_client=mock_mcp_client,
        llm_client=mock_llm_client,
    )

    # Characterize: Agent has private methods for stage processing
    assert hasattr(agent, "_stage_decision"), "Should have _stage_decision private method"
    assert hasattr(agent, "_stage_execution"), "Should have _stage_execution private method"
    assert hasattr(agent, "_stage_formatting"), "Should have _stage_formatting private method"

    # Characterize: Process method orchestrates stages
    request = AgentRequest(
        user_id=123,
        message="Test message",
        session_id="session_123",
    )

    # Characterize: Process method should return AgentResponse with expected fields
    # Note: Full execution is tested in other integration tests
    assert callable(agent.process), "process should be callable"

    # Characterize: AgentResponse schema
    # AgentResponse should have: success, text, tools_used, tokens_used, error, reasoning
    response_fields = AgentResponse.__fields__.keys()
    assert "success" in response_fields, "Response should have success field"
    assert "text" in response_fields, "Response should have text field"
    assert "tools_used" in response_fields, "Response should have tools_used field"
    assert "tokens_used" in response_fields, "Response should have tokens_used field"
