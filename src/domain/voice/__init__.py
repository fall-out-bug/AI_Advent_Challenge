"""Domain layer for voice agent functionality.

Purpose:
    Contains domain interfaces, value objects, and errors for voice-to-text
    processing, command confirmation, and Butler integration.
"""

from src.domain.voice.exceptions import (
    InvalidVoiceCommandError,
    SpeechToTextError,
)
from src.domain.voice.interfaces import SpeechToTextService
from src.domain.voice.value_objects import (
    TranscriptionResult,
    VoiceCommand,
    VoiceCommandState,
)

__all__ = [
    "SpeechToTextService",
    "TranscriptionResult",
    "VoiceCommand",
    "VoiceCommandState",
    "SpeechToTextError",
    "InvalidVoiceCommandError",
]


