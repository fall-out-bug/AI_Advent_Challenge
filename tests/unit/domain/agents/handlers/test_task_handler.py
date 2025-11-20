"""Unit tests for Task Handler.

Following TDD principles and testing best practices.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.presentation.bot.handlers.task import TaskHandler


class TestTaskHandler:
    """Test TaskHandler."""

    @pytest.fixture
    def mock_create_task_use_case(self) -> CreateTaskUseCase:
        """Create mocked CreateTaskUseCase."""
        use_case = Mock(spec=CreateTaskUseCase)
        use_case.execute = AsyncMock()
        return use_case

    @pytest.fixture
    def handler(self, mock_create_task_use_case: CreateTaskUseCase) -> TaskHandler:
        """Create handler instance."""
        return TaskHandler(create_task_use_case=mock_create_task_use_case)

    @pytest.mark.asyncio
    async def test_handle_creates_task_successfully(
        self, handler: TaskHandler, mock_create_task_use_case: CreateTaskUseCase
    ) -> None:
        """Task handler returns success message when use case succeeds."""
        context = DialogContext(state=DialogState.IDLE, user_id="123", session_id="456")
        mock_create_task_use_case.execute.return_value = TaskCreationResult(
            created=True,
            task_id="task123",
        )

        response = await handler.handle(context, "Create a task")

        assert "created successfully" in response.lower()
        mock_create_task_use_case.execute.assert_awaited_once()
        assert context.state == DialogState.IDLE

    @pytest.mark.asyncio
    async def test_handle_requests_clarification(
        self, handler: TaskHandler, mock_create_task_use_case: CreateTaskUseCase
    ) -> None:
        """Clarification responses are passed through and conversation state stored."""
        context = DialogContext(state=DialogState.IDLE, user_id="123", session_id="456")
        mock_create_task_use_case.execute.return_value = TaskCreationResult(
            created=False,
            clarification="What is the deadline?",
            intent_payload={"title": "Test"},
        )

        response = await handler.handle(context, "Create task")

        assert "deadline" in response.lower()
        assert context.data.get("pending_intent") == {"title": "Test"}

    @pytest.mark.asyncio
    async def test_handle_reports_error(
        self, handler: TaskHandler, mock_create_task_use_case: CreateTaskUseCase
    ) -> None:
        """User sees error message when use case fails."""
        context = DialogContext(state=DialogState.IDLE, user_id="123", session_id="456")
        mock_create_task_use_case.execute.return_value = TaskCreationResult(
            created=False,
            error="Task creation failed: Validation error",
        )

        response = await handler.handle(context, "Create task")

        assert "failed" in response.lower()
        mock_create_task_use_case.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_unexpected_exception(
        self, handler: TaskHandler, mock_create_task_use_case: CreateTaskUseCase
    ) -> None:
        """Handler falls back to generic error message on unexpected exceptions."""
        context = DialogContext(state=DialogState.IDLE, user_id="123", session_id="456")
        mock_create_task_use_case.execute.side_effect = Exception("boom")

        response = await handler.handle(context, "Create task")

        assert "sorry" in response.lower()
