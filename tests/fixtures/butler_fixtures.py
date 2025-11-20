"""Butler-specific fixtures for testing.

Following TDD principles and Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dtos.butler_dialog_dtos import (
    DialogContext,
    DialogMode,
    DialogState,
)
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.application.services.mode_classifier import ModeClassifier
from src.application.use_cases.collect_data_use_case import CollectDataUseCase
from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.domain.interfaces.llm_client import LLMClientProtocol
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.presentation.bot.handlers.chat import ChatHandler
from src.presentation.bot.handlers.data import DataHandler
from src.presentation.bot.handlers.task import TaskHandler
from src.presentation.bot.orchestrator import ButlerOrchestrator


@pytest.fixture
async def mock_llm_client_protocol() -> LLMClientProtocol:
    """Create mock LLMClientProtocol for testing.

    Returns:
        Mock LLMClientProtocol with all required methods.
    """
    mock_client = AsyncMock(spec=LLMClientProtocol)
    mock_client.make_request = AsyncMock(return_value="TASK")
    mock_client.check_availability = AsyncMock(return_value=True)
    mock_client.close = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture
async def mock_tool_client_protocol() -> ToolClientProtocol:
    """Create mock ToolClientProtocol for testing.

    Returns:
        Mock ToolClientProtocol with discover_tools and call_tool methods.
    """
    mock_client = AsyncMock(spec=ToolClientProtocol)

    # Default tool discovery response
    mock_client.discover_tools = AsyncMock(
        return_value=[
            {
                "name": "create_task",
                "description": "Create a new task",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["title"],
                },
            },
            {
                "name": "get_channels_digest",
                "description": "Get channel digests",
                "input_schema": {
                    "type": "object",
                    "properties": {"user_id": {"type": "string"}},
                    "required": ["user_id"],
                },
            },
            {
                "name": "get_student_stats",
                "description": "Get student statistics",
                "input_schema": {
                    "type": "object",
                    "properties": {"teacher_id": {"type": "string"}},
                    "required": ["teacher_id"],
                },
            },
        ]
    )

    # Default tool call response
    mock_client.call_tool = AsyncMock(
        return_value={"success": True, "data": {"id": "task_123", "title": "Test Task"}}
    )

    return mock_client


@pytest.fixture
async def mock_mongodb() -> AsyncIOMotorDatabase:
    """Create mock MongoDB database for testing.

    Returns:
        Mock AsyncIOMotorDatabase with dialog_contexts collection.
    """
    db = MagicMock(spec=AsyncIOMotorDatabase)

    # Mock dialog_contexts collection
    dialog_contexts = MagicMock()

    # Mock find_one (returns None by default - no existing context)
    async def find_one_mock(filter: Dict[str, Any]) -> Dict[str, Any] | None:
        return None

    # Mock insert_one (creates new context)
    async def insert_one_mock(doc: Dict[str, Any]) -> MagicMock:
        result = MagicMock()
        result.inserted_id = "test_context_id"
        return result

    # Mock update_one (updates existing context)
    async def update_one_mock(
        filter: Dict[str, Any], update: Dict[str, Any], **kwargs
    ) -> MagicMock:
        result = MagicMock()
        result.modified_count = 1
        return result

    dialog_contexts.find_one = AsyncMock(side_effect=find_one_mock)
    dialog_contexts.insert_one = AsyncMock(side_effect=insert_one_mock)
    dialog_contexts.update_one = AsyncMock(side_effect=update_one_mock)

    db.dialog_contexts = dialog_contexts

    return db


@pytest.fixture
async def mock_mode_classifier(
    mock_llm_client_protocol: LLMClientProtocol,
) -> ModeClassifier:
    """Create ModeClassifier with mocked LLM client.

    Args:
        mock_llm_client_protocol: Mocked LLM client.

    Returns:
        ModeClassifier instance.
    """
    return ModeClassifier(llm_client=mock_llm_client_protocol, default_model="mistral")


@pytest.fixture
def mock_intent_orchestrator() -> IntentOrchestrator:
    """Create mock IntentOrchestrator for testing.

    Returns:
        Mock IntentOrchestrator.
    """
    mock_orch = MagicMock(spec=IntentOrchestrator)
    mock_orch.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Test Task",
            description="Test Description",
            to_mcp_params=lambda: {
                "title": "Test Task",
                "description": "Test Description",
            },
        )
    )
    return mock_orch


@pytest.fixture
def mock_task_handler(
    mock_intent_orchestrator: IntentOrchestrator,
    mock_tool_client_protocol: ToolClientProtocol,
    mock_mongodb: AsyncIOMotorDatabase,
) -> TaskHandler:
    """Create TaskHandler with mocked dependencies.

    Args:
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
        mock_mongodb: Mocked MongoDB database.

    Returns:
        TaskHandler instance.
    """
    create_task_uc = CreateTaskUseCase(
        intent_orchestrator=mock_intent_orchestrator,
        tool_client=mock_tool_client_protocol,
        mongodb=mock_mongodb,
    )
    return TaskHandler(
        create_task_use_case=create_task_uc,
    )


@pytest.fixture
def mock_data_handler(mock_tool_client_protocol: ToolClientProtocol) -> DataHandler:
    """Create DataHandler with mocked dependencies.

    Args:
        mock_tool_client_protocol: Mocked ToolClientProtocol.

    Returns:
        DataHandler instance.
    """
    return DataHandler(tool_client=mock_tool_client_protocol)


@pytest.fixture
def mock_chat_handler(mock_llm_client_protocol: LLMClientProtocol) -> ChatHandler:
    """Create ChatHandler with mocked dependencies.

    Args:
        mock_llm_client_protocol: Mocked LLMClientProtocol.

    Returns:
        ChatHandler instance.
    """
    return ChatHandler(llm_client=mock_llm_client_protocol, default_model="mistral")


@pytest.fixture
async def butler_orchestrator(
    mock_mode_classifier: ModeClassifier,
    mock_task_handler: TaskHandler,
    mock_data_handler: DataHandler,
    mock_chat_handler: ChatHandler,
    mock_mongodb: AsyncIOMotorDatabase,
) -> ButlerOrchestrator:
    """Create ButlerOrchestrator with all mocked dependencies.

    This is the main fixture for testing ButlerOrchestrator.
    All dependencies are mocked for isolation.

    Args:
        mock_mode_classifier: Mocked ModeClassifier.
        mock_task_handler: Mocked TaskHandler.
        mock_data_handler: Mocked DataHandler.
        mock_chat_handler: Mocked ChatHandler.
        mock_mongodb: Mocked MongoDB database.

    Returns:
        Fully configured ButlerOrchestrator instance.
    """
    return ButlerOrchestrator(
        mode_classifier=mock_mode_classifier,
        task_handler=mock_task_handler,
        data_handler=mock_data_handler,
        homework_handler=MagicMock(),
        chat_handler=mock_chat_handler,
        mongodb=mock_mongodb,
    )


@pytest.fixture
def sample_dialog_context() -> DialogContext:
    """Create sample dialog context for testing.

    Returns:
        DialogContext instance.
    """
    return DialogContext(
        user_id="test_user_123",
        session_id="test_session_456",
        state=DialogState.IDLE,
        data={},
        step_count=0,
    )


@pytest.fixture
def sample_task_message() -> str:
    """Sample task creation message.

    Returns:
        Task creation message string.
    """
    return "Create a task: Buy milk tomorrow"


@pytest.fixture
def sample_data_message() -> str:
    """Sample data collection message.

    Returns:
        Data collection message string.
    """
    return "Get channel digests"


@pytest.fixture
def sample_idle_message() -> str:
    """Sample idle/chat message.

    Returns:
        Chat message string.
    """
    return "Hello, how are you?"


@pytest.fixture
def mock_telegram_bot():
    """Create mock aiogram Bot for E2E testing.

    Returns:
        Mock Bot instance.
    """
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=12345, username="test_bot"))
    return bot


@pytest.fixture
def mock_telegram_dispatcher():
    """Create mock aiogram Dispatcher for E2E testing.

    Returns:
        Mock Dispatcher instance.
    """
    dispatcher = MagicMock()
    dispatcher.include_router = MagicMock()
    dispatcher.start_polling = AsyncMock()
    dispatcher.stop_polling = AsyncMock()
    return dispatcher


@pytest.fixture
def mock_telegram_message():
    """Create mock aiogram Message for E2E testing.

    Returns:
        Mock Message instance.
    """
    message = MagicMock()
    message.from_user = MagicMock(id=12345, username="test_user")
    message.text = "Test message"
    message.message_id = 123
    message.answer = AsyncMock()
    return message


@pytest.fixture
def sample_user_id() -> str:
    """Sample user ID for testing.

    Returns:
        User ID string.
    """
    return "12345"


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing.

    Returns:
        Session ID string.
    """
    return "session_12345"
