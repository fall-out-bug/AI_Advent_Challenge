from typing import cast

import pytest

from src.application.use_cases.create_task_use_case import CreateTaskUseCase


@pytest.mark.asyncio
async def test_task_handler_successful_creation():
    from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
    from src.application.dtos.butler_use_case_dtos import TaskCreationResult
    from src.presentation.bot.handlers.task import TaskHandler

    class StubCreateTaskUseCase:
        async def execute(self, user_id, message, context):
            return TaskCreationResult(created=True, task_id="123")

    handler = TaskHandler(
        create_task_use_case=cast("CreateTaskUseCase", StubCreateTaskUseCase())
    )
    context = DialogContext(
        state=DialogState.IDLE, user_id="42", session_id="session-test"
    )

    response = await handler.handle(context, "create task buy milk")

    assert "Task created successfully" in response
    assert context.state is DialogState.IDLE


@pytest.mark.asyncio
async def test_task_handler_error_response():
    from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
    from src.application.use_cases.create_task_use_case import CreateTaskUseCase
    from src.presentation.bot.handlers.task import TaskHandler

    class FailingUseCase:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("failure")

    handler = TaskHandler(
        create_task_use_case=cast("CreateTaskUseCase", FailingUseCase())
    )
    context = DialogContext(
        state=DialogState.IDLE, user_id="42", session_id="session-test"
    )

    response = await handler.handle(context, "create task")

    assert response.startswith("❌")
