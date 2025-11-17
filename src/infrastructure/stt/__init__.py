"""Speech-to-text infrastructure adapters.

Purpose:
    Contains STT adapter implementations (Whisper, Vosk) for voice agent.
    Note: Whisper STT is separate from LLM service (Mistral/Ollama for LLM).
"""

from src.infrastructure.stt.ollama_adapter import WhisperSpeechToTextAdapter
from src.infrastructure.stt.vosk_adapter import VoskSpeechToTextAdapter

__all__ = [
    "WhisperSpeechToTextAdapter",
    "VoskSpeechToTextAdapter",
]

