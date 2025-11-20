"""Factory for creating voice agent use cases and dependencies.

Purpose:
    Centralized creation of voice agent components with dependency injection.
"""

from __future__ import annotations

from typing import Optional

from aiogram import Bot
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.voice.use_cases.handle_voice_confirmation import (
    HandleVoiceConfirmationUseCase,
)
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.interfaces import ButlerGateway
from src.domain.voice.interfaces import SpeechToTextService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.stt.fallback_stt_adapter import FallbackSTTAdapter
from src.infrastructure.stt.ollama_adapter import WhisperSpeechToTextAdapter
from src.infrastructure.stt.vosk_adapter import VoskSpeechToTextAdapter
from src.infrastructure.voice.butler_gateway_impl import ButlerGatewayImpl
from src.infrastructure.voice.command_store import VoiceCommandStore
from src.infrastructure.voice.confirmation_gateway_impl import (
    ConfirmationGatewayImpl,
)
from src.infrastructure.voice.redis_command_store import RedisVoiceCommandStore

logger = get_logger("voice_factory")


async def create_voice_use_cases(
    orchestrator: ButlerOrchestrator,
    bot: Bot,
    mongodb: Optional[AsyncIOMotorDatabase] = None,
    stt_service: Optional[SpeechToTextService] = None,
    command_store: Optional[VoiceCommandStore] = None,
) -> tuple[ProcessVoiceCommandUseCase, HandleVoiceConfirmationUseCase]:
    """Create voice agent use cases with all dependencies.

    Purpose:
        Initialize all infrastructure components required for voice agent:
        STT service, command store, gateways, and use cases.

    Args:
        orchestrator: ButlerOrchestrator instance for ButlerGateway.
        bot: Telegram Bot instance for ConfirmationGateway.
        mongodb: Optional MongoDB database instance for Redis connection (if None, will be created).
        stt_service: Optional STT service (if None, will create Ollama adapter).
        command_store: Optional command store (if None, will create Redis store).

    Returns:
        Tuple of (ProcessVoiceCommandUseCase, HandleVoiceConfirmationUseCase).

    Raises:
        RuntimeError: If critical dependencies cannot be initialized.

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> bot = Bot(token="...")
        >>> process_uc, confirmation_uc = await create_voice_use_cases(orchestrator, bot)
    """
    try:
        settings = get_settings()

        # 1. Initialize STT Service
        # Note: Whisper STT is separate from LLM service (Mistral/Ollama for LLM)
        if stt_service is None:
            try:
                stt_service = WhisperSpeechToTextAdapter(settings=settings)
                logger.info(
                    f"WhisperSpeechToTextAdapter initialized: "
                    f"{settings.whisper_host}:{settings.whisper_port}, "
                    f"model={settings.stt_model}"
                )
                # Note: Model availability is checked during first transcription call
                # If model not found, will fall back to Vosk during actual use
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Whisper STT adapter: {e}. "
                    "Falling back to Vosk adapter."
                )
                try:
                    stt_service = VoskSpeechToTextAdapter()
                    logger.info("VoskSpeechToTextAdapter initialized (fallback)")
                except ImportError as e2:
                    logger.error(
                        f"Vosk not installed: {e2}. "
                        "Install with: pip install vosk pydub. "
                        "Or start whisper-stt service"
                    )
                    raise RuntimeError(
                        "Failed to initialize STT service: "
                        "Neither Whisper STT server nor Vosk are available. "
                        "Please start whisper-stt service or install Vosk: pip install vosk pydub"
                    ) from e2
                except Exception as e2:
                    logger.error(f"Failed to initialize Vosk STT adapter: {e2}")
                    raise RuntimeError(
                        "Failed to initialize STT service (both Whisper and Vosk failed)"
                    ) from e2

        # 2. Initialize Voice Command Store
        if command_store is None:
            try:
                # Try Redis first
                command_store = RedisVoiceCommandStore(settings=settings)
                logger.info(
                    f"RedisVoiceCommandStore initialized: "
                    f"{settings.redis_host}:{settings.redis_port}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Redis command store: {e}. "
                    "Falling back to in-memory store."
                )
                from src.infrastructure.voice.command_store import (
                    InMemoryVoiceCommandStore,
                )

                command_store = InMemoryVoiceCommandStore()
                logger.info("InMemoryVoiceCommandStore initialized (fallback)")

        # 3. Initialize Gateways
        butler_gateway: ButlerGateway = ButlerGatewayImpl(orchestrator=orchestrator)
        confirmation_gateway = ConfirmationGatewayImpl(bot=bot)

        logger.info("Gateways initialized")

        # 4. Create Use Cases
        process_use_case = ProcessVoiceCommandUseCase(
            stt_service=stt_service,
            command_store=command_store,
            confirmation_gateway=confirmation_gateway,
            settings=settings,
        )

        confirmation_use_case = HandleVoiceConfirmationUseCase(
            command_store=command_store,
            butler_gateway=butler_gateway,
            confirmation_gateway=confirmation_gateway,
            settings=settings,
        )

        logger.info("Voice agent use cases created successfully")

        return process_use_case, confirmation_use_case

    except Exception as e:
        logger.error(f"Failed to create voice use cases: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize voice agent: {e}") from e
