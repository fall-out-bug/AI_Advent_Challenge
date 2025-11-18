"""Voice use case factory.

Purpose:
    Creates voice use cases with their dependencies (adapters, gateways, stores).
"""

from __future__ import annotations

from aiogram import Bot

from src.application.voice.use_cases.handle_voice_confirmation import (
    HandleVoiceConfirmationUseCase,
)
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.interfaces.voice import ButlerGateway
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.voice.butler_gateway_impl import ButlerGatewayImpl
from src.infrastructure.voice.confirmation_gateway_impl import (
    ConfirmationGatewayImpl,
)
from src.infrastructure.voice.redis_store import RedisVoiceCommandStore
from src.infrastructure.voice.whisper_adapter import WhisperSpeechToTextAdapter

logger = get_logger("voice_factory")


async def create_voice_use_cases(
    orchestrator: ButlerOrchestrator,
    bot: Bot,
) -> tuple[ProcessVoiceCommandUseCase, HandleVoiceConfirmationUseCase]:
    """Create voice use cases with dependencies.

    Purpose:
        Creates ProcessVoiceCommandUseCase and HandleVoiceConfirmationUseCase
        with their infrastructure dependencies (STT adapter, Redis store,
        Butler gateway, confirmation gateway).

    Args:
        orchestrator: ButlerOrchestrator instance for routing commands.
        bot: Aiogram Bot instance for sending confirmations.

    Returns:
        Tuple of (ProcessVoiceCommandUseCase, HandleVoiceConfirmationUseCase).

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> bot = Bot(token="...")
        >>> process_uc, confirmation_uc = await create_voice_use_cases(
        ...     orchestrator=orchestrator,
        ...     bot=bot,
        ... )
    """
    logger.info("Creating voice use cases...")

    settings = get_settings()

    # Create STT adapter
    stt_adapter = WhisperSpeechToTextAdapter(
        host=settings.whisper_host,
        port=settings.whisper_port,
        model=settings.stt_model,
    )

    logger.info(
        "WhisperSpeechToTextAdapter initialized",
        extra={
            "host": settings.whisper_host,
            "port": settings.whisper_port,
            "model": settings.stt_model,
        },
    )

    # Create Redis store
    command_store = RedisVoiceCommandStore(
        host=settings.voice_redis_host,
        port=settings.voice_redis_port,
        password=settings.voice_redis_password,
    )

    logger.info(
        "RedisVoiceCommandStore initialized",
        extra={
            "host": settings.voice_redis_host,
            "port": settings.voice_redis_port,
        },
    )

    # Create Butler gateway
    butler_gateway: ButlerGateway = ButlerGatewayImpl(orchestrator)

    logger.info("ButlerGateway initialized")

    # Create confirmation gateway (deprecated, but needed for compatibility)
    confirmation_gateway = ConfirmationGatewayImpl(bot)

    logger.info("ConfirmationGateway initialized (deprecated)")

    # Create use cases
    process_use_case = ProcessVoiceCommandUseCase(
        stt_adapter=stt_adapter,
        command_store=command_store,
    )

    confirmation_use_case = HandleVoiceConfirmationUseCase(
        command_store=command_store,
        butler_gateway=butler_gateway,
    )

    logger.info("Voice agent use cases created successfully")

    return process_use_case, confirmation_use_case

