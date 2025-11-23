"""Unit tests for GodAgentTelegramHandler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.application.god_agent.services.intent_router_service import IntentRouterService
from src.application.god_agent.services.plan_compiler_service import PlanCompilerService
from src.presentation.bot.handlers.god_agent_handler import (
    GodAgentTelegramHandler,
    setup_god_agent_handler,
)


@pytest.fixture
def mock_orchestrator():
    """Mock GodAgentOrchestrator."""
    orchestrator = AsyncMock()
    orchestrator.execute_plan = AsyncMock(
        return_value={
            "plan_id": "plan_1",
            "status": "completed",
            "step_results": [{"step_id": "step_1", "status": "success"}],
        }
    )
    return orchestrator


@pytest.fixture
def mock_intent_router():
    """Mock IntentRouterService."""
    router = AsyncMock()
    return router


@pytest.fixture
def mock_plan_compiler():
    """Mock PlanCompilerService."""
    compiler = AsyncMock()
    return compiler


@pytest.fixture
def god_agent_handler(mock_orchestrator, mock_intent_router, mock_plan_compiler):
    """Create GodAgentTelegramHandler instance."""
    return GodAgentTelegramHandler(
        orchestrator=mock_orchestrator,
        intent_router=mock_intent_router,
        plan_compiler=mock_plan_compiler,
    )


@pytest.fixture
def mock_message():
    """Create mock Telegram message."""
    message = MagicMock()
    message.from_user.id = 123
    message.text = "Hello, how can you help me?"
    message.voice = None
    message.audio = None
    message.answer = AsyncMock()  # Make answer async
    return message


@pytest.mark.asyncio
async def test_handle_text_message_routes_through_orchestrator(
    god_agent_handler,
    mock_orchestrator,
    mock_intent_router,
    mock_plan_compiler,
    mock_message,
):
    """Test handle_text_message routes through orchestrator."""
    # Setup global variables
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = mock_orchestrator
    handler_module._intent_router = mock_intent_router
    handler_module._plan_compiler = mock_plan_compiler

    # Mock intent router and plan compiler
    from src.domain.god_agent.value_objects.intent import Intent, IntentType

    mock_intent_router.route_intent = AsyncMock(
        return_value=Intent(
            intent_type=IntentType.CONCIERGE,
            confidence=0.9,
        )
    )

    from src.domain.god_agent.entities.task_plan import TaskPlan
    from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
    from src.domain.god_agent.value_objects.skill import SkillType

    mock_plan_compiler.compile_plan = AsyncMock(
        return_value=TaskPlan(
            plan_id="plan_1",
            steps=[
                TaskStep(
                    step_id="step_1",
                    skill_type=SkillType.CONCIERGE,
                    status=TaskStepStatus.PENDING,
                )
            ],
        )
    )

    await god_agent_handler.handle_text_message(mock_message)

    # Verify orchestrator was called
    mock_orchestrator.execute_plan.assert_called_once()


@pytest.mark.asyncio
async def test_handle_voice_message_transcribes_and_routes(
    god_agent_handler,
    mock_orchestrator,
    mock_intent_router,
    mock_plan_compiler,
    mock_message,
):
    """Test handle_voice_message transcribes and routes through orchestrator."""
    # Setup global variables
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = mock_orchestrator
    handler_module._intent_router = mock_intent_router
    handler_module._plan_compiler = mock_plan_compiler

    # Mock voice message
    mock_message.voice = MagicMock()
    mock_message.text = None

    # Mock transcription function
    with patch(
        "src.presentation.bot.handlers.god_agent_handler._transcribe_voice",
        return_value="Hello, how can you help me?",
    ):
        # Mock intent router and plan compiler
        from src.domain.god_agent.value_objects.intent import Intent, IntentType

        mock_intent_router.route_intent = AsyncMock(
            return_value=Intent(
                intent_type=IntentType.CONCIERGE,
                confidence=0.9,
            )
        )

        from src.domain.god_agent.entities.task_plan import TaskPlan
        from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
        from src.domain.god_agent.value_objects.skill import SkillType

        mock_plan_compiler.compile_plan = AsyncMock(
            return_value=TaskPlan(
                plan_id="plan_1",
                steps=[
                    TaskStep(
                        step_id="step_1",
                        skill_type=SkillType.CONCIERGE,
                        status=TaskStepStatus.PENDING,
                    )
                ],
            )
        )

        await god_agent_handler.handle_voice_message(mock_message)

        # Verify orchestrator was called
        mock_orchestrator.execute_plan.assert_called_once()


@pytest.mark.asyncio
async def test_setup_god_agent_handler_returns_router(
    mock_orchestrator, mock_intent_router, mock_plan_compiler
):
    """Test setup_god_agent_handler returns configured router."""
    router = setup_god_agent_handler(
        orchestrator=mock_orchestrator,
        intent_router=mock_intent_router,
        plan_compiler=mock_plan_compiler,
    )

    assert router is not None
    # Verify router is configured
    assert hasattr(router, "message")


@pytest.mark.asyncio
async def test_handle_text_message_handles_orchestrator_error(
    god_agent_handler,
    mock_orchestrator,
    mock_intent_router,
    mock_plan_compiler,
    mock_message,
):
    """Test handle_text_message handles orchestrator errors gracefully."""
    # Setup global variables
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = mock_orchestrator
    handler_module._intent_router = mock_intent_router
    handler_module._plan_compiler = mock_plan_compiler

    # Mock intent router and plan compiler
    from src.domain.god_agent.value_objects.intent import Intent, IntentType

    mock_intent_router.route_intent = AsyncMock(
        return_value=Intent(
            intent_type=IntentType.CONCIERGE,
            confidence=0.9,
        )
    )

    from src.domain.god_agent.entities.task_plan import TaskPlan
    from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
    from src.domain.god_agent.value_objects.skill import SkillType

    mock_plan_compiler.compile_plan = AsyncMock(
        return_value=TaskPlan(
            plan_id="plan_1",
            steps=[
                TaskStep(
                    step_id="step_1",
                    skill_type=SkillType.CONCIERGE,
                    status=TaskStepStatus.PENDING,
                )
            ],
        )
    )

    # Mock orchestrator to raise error
    mock_orchestrator.execute_plan.side_effect = Exception("Orchestrator error")

    # Should not raise exception
    await god_agent_handler.handle_text_message(mock_message)

    # Verify error was handled (no exception raised)
    assert True
