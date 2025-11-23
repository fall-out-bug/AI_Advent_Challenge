"""Unit tests for VoicePipelineAdapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message, Voice

from src.application.voice.dtos import ProcessVoiceCommandInput
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.domain.voice.value_objects import TranscriptionResult
from src.infrastructure.god_agent.adapters.voice_pipeline_adapter import (
    VoicePipelineAdapter,
)


@pytest.fixture
def mock_process_voice_use_case():
    """Mock ProcessVoiceCommandUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def mock_bot():
    """Mock Telegram bot."""
    bot = AsyncMock()
    bot.get_file = AsyncMock()
    bot.download_file = AsyncMock()
    file = MagicMock()
    file.file_path = "voice_file_path"
    bot.get_file.return_value = file
    file_stream = MagicMock()
    file_stream.read.return_value = b"fake_audio_bytes"
    bot.download_file.return_value = file_stream
    return bot


@pytest.fixture
def voice_adapter(mock_process_voice_use_case, mock_bot):
    """Create VoicePipelineAdapter instance."""
    return VoicePipelineAdapter(
        process_voice_command_use_case=mock_process_voice_use_case,
        bot=mock_bot,
    )


@pytest.fixture
def mock_voice_message():
    """Create mock Telegram voice message."""
    message = MagicMock()
    message.from_user.id = 123
    message.voice = MagicMock()
    message.voice.file_id = "voice_file_123"
    message.voice.duration = 5
    message.text = None
    return message


@pytest.mark.asyncio
async def test_transcribe_voice_calls_use_case(
    voice_adapter, mock_process_voice_use_case, mock_voice_message
):
    """Test transcribe_voice calls ProcessVoiceCommandUseCase."""
    # Setup mock
    transcription_result = TranscriptionResult(
        text="Hello, how can you help me?",
        confidence=0.95,
        language="en",
        duration_ms=5000,
    )
    mock_process_voice_use_case.execute.return_value = transcription_result

    # Execute
    result = await voice_adapter.transcribe_voice(mock_voice_message)

    # Verify
    assert result == "Hello, how can you help me?"
    mock_process_voice_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_transcribe_voice_handles_use_case_error(
    voice_adapter, mock_process_voice_use_case, mock_voice_message
):
    """Test transcribe_voice handles ProcessVoiceCommandUseCase errors."""
    # Setup mock to raise error
    mock_process_voice_use_case.execute.side_effect = Exception("Transcription error")

    # Execute
    result = await voice_adapter.transcribe_voice(mock_voice_message)

    # Should return empty string on error
    assert result == ""


@pytest.mark.asyncio
async def test_is_voice_message_returns_true_for_voice(
    voice_adapter, mock_voice_message
):
    """Test is_voice_message returns True for voice message."""
    is_voice = voice_adapter.is_voice_message(mock_voice_message)

    assert is_voice is True


@pytest.mark.asyncio
async def test_is_voice_message_returns_false_for_text(voice_adapter):
    """Test is_voice_message returns False for text message."""
    message = MagicMock()
    message.voice = None
    message.audio = None
    message.text = "Hello"

    is_voice = voice_adapter.is_voice_message(message)

    assert is_voice is False
