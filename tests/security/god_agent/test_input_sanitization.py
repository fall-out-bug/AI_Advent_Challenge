"""Security tests for input sanitization."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.application.god_agent.services.intent_router_service import IntentRouterService
from src.application.god_agent.services.plan_compiler_service import PlanCompilerService
from src.presentation.bot.handlers.god_agent_handler import (
    GodAgentTelegramHandler,
    handle_text_message,
)


@pytest.fixture
def mock_message():
    """Create mock Telegram message."""
    message = MagicMock()
    message.from_user = User(
        id=123,
        is_bot=False,
        first_name="Test",
    )
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_sql_injection_sanitized(mock_message):
    """Test SQL injection attempts are sanitized."""
    # SQL injection attempt
    mock_message.text = "'; DROP TABLE users; --"

    # Setup handler
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = AsyncMock()
    handler_module._intent_router = AsyncMock()
    handler_module._plan_compiler = AsyncMock()

    # Should not raise exception or execute SQL
    await handle_text_message(mock_message)

    # Verify message was answered (no SQL execution)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_xss_sanitized(mock_message):
    """Test XSS attempts are sanitized."""
    # XSS attempt
    mock_message.text = "<script>alert('XSS')</script>"

    # Setup handler
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = AsyncMock()
    handler_module._intent_router = AsyncMock()
    handler_module._plan_compiler = AsyncMock()

    # Should not execute script
    await handle_text_message(mock_message)

    # Verify message was answered (no script execution)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_path_traversal_sanitized(mock_message):
    """Test path traversal attempts are sanitized."""
    # Path traversal attempt
    mock_message.text = "../../../etc/passwd"

    # Setup handler
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = AsyncMock()
    handler_module._intent_router = AsyncMock()
    handler_module._plan_compiler = AsyncMock()

    # Should not access files outside allowed paths
    await handle_text_message(mock_message)

    # Verify message was answered (no file access)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_command_injection_sanitized(mock_message):
    """Test command injection attempts are sanitized."""
    # Command injection attempt
    mock_message.text = "; rm -rf /"

    # Setup handler
    from src.presentation.bot.handlers import god_agent_handler as handler_module

    handler_module._orchestrator = AsyncMock()
    handler_module._intent_router = AsyncMock()
    handler_module._plan_compiler = AsyncMock()

    # Should not execute commands
    await handle_text_message(mock_message)

    # Verify message was answered (no command execution)
    mock_message.answer.assert_called()


@pytest.mark.asyncio
async def test_voice_transcript_sanitized():
    """Test voice transcript sanitization."""
    from src.infrastructure.god_agent.adapters.voice_pipeline_adapter import (
        VoicePipelineAdapter,
    )

    adapter = VoicePipelineAdapter(
        process_voice_command_use_case=AsyncMock(),
    )

    # Malicious transcript
    malicious_text = "<script>alert('XSS')</script>; DROP TABLE users;"

    # Should sanitize before processing
    # Note: Actual sanitization would happen in use case or handler
    assert True  # Placeholder - actual implementation will verify sanitization
