"""Integration tests for use case integration.

Following TDD principles: test use cases integrated with real orchestrator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.application.use_cases.collect_data_use_case import CollectDataUseCase
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from tests.fixtures.butler_fixtures import (
    mock_tool_client_protocol,
    mock_llm_client_protocol,
    mock_mongodb,
)


@pytest.mark.asyncio
async def test_create_task_usecase_with_real_intent_orchestrator(
    mock_llm_client_protocol, mock_tool_client_protocol, mock_mongodb
):
    """Test CreateTaskUseCase with real IntentOrchestrator (mocked LLM).

    Args:
        mock_llm_client_protocol: Mocked LLM client.
        mock_tool_client_protocol: Mocked tool client.
        mock_mongodb: Mocked MongoDB.
    """
    # Setup: Real IntentOrchestrator with mocked LLM
    intent_orch = IntentOrchestrator(model_name="mistral")
    intent_orch._llm_client = mock_llm_client_protocol

    # Setup: Mock parse_task_intent to return complete intent
    from src.domain.entities.intent import IntentParseResult

    async def mock_parse_success(*args, **kwargs):
        return IntentParseResult(
            title="Buy milk",
            description="Tomorrow",
            needs_clarification=False,
            questions=[],
        )

    intent_orch.parse_task_intent = AsyncMock(side_effect=mock_parse_success)

    # Configure tool client
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"status": "success", "task_id": "task_123"}
    )

    # Create use case
    use_case = CreateTaskUseCase(
        intent_orchestrator=intent_orch,
        tool_client=mock_tool_client_protocol,
        mongodb=mock_mongodb,
    )

    # Execute
    result = await use_case.execute(
        user_id=12345, message="Create a task: Buy milk tomorrow", context={}
    )

    # Verify: Task created successfully
    assert result.created is True
    assert result.task_id == "task_123"
    assert result.error is None
    mock_tool_client_protocol.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_create_task_usecase_clarification_flow(
    mock_llm_client_protocol, mock_tool_client_protocol, mock_mongodb
):
    """Test CreateTaskUseCase clarification flow.

    Args:
        mock_llm_client_protocol: Mocked LLM client.
        mock_tool_client_protocol: Mocked tool client.
        mock_mongodb: Mocked MongoDB.
    """
    # Setup: Intent needs clarification
    intent_orch = IntentOrchestrator(model_name="mistral")
    intent_orch._llm_client = mock_llm_client_protocol

    # Setup: Intent needs clarification - return proper IntentParseResult structure
    from src.domain.entities.intent import IntentParseResult

    # Mock parse_task_intent to return clarification result
    async def mock_parse_clarification(*args, **kwargs):
        return IntentParseResult(
            title="",  # Required field
            needs_clarification=True,
            questions=["What is the task title?"],
            description=None,
        )

    intent_orch.parse_task_intent = AsyncMock(side_effect=mock_parse_clarification)

    use_case = CreateTaskUseCase(
        intent_orchestrator=intent_orch,
        tool_client=mock_tool_client_protocol,
        mongodb=mock_mongodb,
    )

    # Execute
    result = await use_case.execute(user_id=12345, message="Create a task", context={})

    # Verify: Clarification requested
    assert result.created is False
    assert result.clarification is not None
    assert "title" in result.clarification.lower() or "?" in result.clarification
    assert mock_tool_client_protocol.call_tool.call_count == 0


@pytest.mark.asyncio
async def test_collect_data_usecase_channels_digest(mock_tool_client_protocol):
    """Test CollectDataUseCase for channel digests.

    Args:
        mock_tool_client_protocol: Mocked tool client.
    """
    # Setup: Configure tool client response
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={
            "success": True,
            "digests": [
                {"channel": "channel1", "posts": 10},
                {"channel": "channel2", "posts": 5},
            ],
        }
    )

    use_case = CollectDataUseCase(tool_client=mock_tool_client_protocol)

    # Execute
    result = await use_case.get_channels_digest(user_id=12345)

    # Verify: Digests returned
    assert result.error is None
    assert len(result.digests) == 2
    mock_tool_client_protocol.call_tool.assert_called_once()
    call_args = mock_tool_client_protocol.call_tool.call_args
    assert call_args[0][0] == "get_channel_digest"
    assert call_args[0][1]["user_id"] == 12345


@pytest.mark.asyncio
async def test_collect_data_usecase_student_stats(mock_tool_client_protocol):
    """Test CollectDataUseCase for student stats.

    Args:
        mock_tool_client_protocol: Mocked tool client.
    """
    # Setup: Configure tool client response
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={
            "success": True,
            "stats": {"total_students": 50, "active_students": 45},
        }
    )

    use_case = CollectDataUseCase(tool_client=mock_tool_client_protocol)

    # Execute
    result = await use_case.get_student_stats(teacher_id="teacher_123")

    # Verify: Stats returned
    assert result.error is None
    assert result.stats["total_students"] == 50
    mock_tool_client_protocol.call_tool.assert_called_once_with(
        "get_student_stats", {"teacher_id": "teacher_123"}
    )


@pytest.mark.asyncio
async def test_create_task_usecase_error_propagation(
    mock_llm_client_protocol, mock_tool_client_protocol, mock_mongodb
):
    """Test error propagation from use case to handler.

    Args:
        mock_llm_client_protocol: Mocked LLM client.
        mock_tool_client_protocol: Mocked tool client.
        mock_mongodb: Mocked MongoDB.
    """
    # Setup: Tool call fails
    intent_orch = IntentOrchestrator(model_name="mistral")
    intent_orch._llm_client = mock_llm_client_protocol

    mock_llm_client_protocol.make_request = AsyncMock(
        return_value='{"primary_goal": "create_task", "title": "Test", "confidence": 0.9}'
    )
    mock_tool_client_protocol.call_tool = AsyncMock(
        side_effect=Exception("Tool execution failed")
    )

    use_case = CreateTaskUseCase(
        intent_orchestrator=intent_orch,
        tool_client=mock_tool_client_protocol,
        mongodb=mock_mongodb,
    )

    # Execute
    result = await use_case.execute(
        user_id=12345, message="Create task: Test", context={}
    )

    # Verify: Error captured in result
    assert result.created is False
    assert result.error is not None
    assert "failed" in result.error.lower() or "error" in result.error.lower()
