"""Butler gateway implementation.

Purpose:
    Implements ButlerGateway protocol by wrapping ButlerOrchestrator
    for routing confirmed voice commands to Butler pipeline.
"""

from __future__ import annotations

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.interfaces.voice import ButlerGateway
from src.infrastructure.logging import get_logger

logger = get_logger("voice.butler_gateway_impl")


class ButlerGatewayImpl:
    """Butler gateway implementation wrapping ButlerOrchestrator.

    Purpose:
        Adapts ButlerOrchestrator.handle_user_message() to ButlerGateway protocol
        for voice command routing. Enables Clean Architecture by decoupling
        voice use cases from concrete orchestrator implementation.

    Args:
        orchestrator: ButlerOrchestrator instance (injected via DI).
    """

    def __init__(self, orchestrator: ButlerOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def handle_user_message(
        self,
        user_id: str,
        text: str,
        session_id: str,
    ) -> str:
        """Delegate confirmed voice command text into Butler pipeline.

        Purpose:
            Routes transcribed and confirmed voice command text to the
            Butler orchestrator, which handles intent classification,
            mode selection, and execution.

        Args:
            user_id: User identifier (Telegram user ID).
            text: Confirmed transcription text from voice command.
            session_id: Session identifier (generated as
                `f"voice_{user_id}_{command_id}"`).

        Returns:
            Response text from Butler orchestrator to send to user.

        Raises:
            RuntimeError: If routing fails.

        Example:
            >>> gateway = ButlerGatewayImpl(orchestrator)
            >>> response = await gateway.handle_user_message(
            ...     user_id="123456789",
            ...     text="Сделай дайджест по каналу onaboka за последние 24 часа",
            ...     session_id="voice_123456789_12345678-1234-5678-1234-567812345678"
            ... )
            >>> response
            "Дайджест по каналу onaboka за последние 24 часа..."
        """
        logger.info(
            "Routing voice command to Butler",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "text_length": len(text),
            },
        )

        try:
            response = await self.orchestrator.handle_user_message(
                user_id=user_id,
                message=text,
                session_id=session_id,
                force_mode=None,  # Let Butler classify intent
            )

            logger.info(
                "Butler response received",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "response_length": len(response),
                },
            )

            return response

        except Exception as e:
            logger.error(
                "Butler gateway error",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise RuntimeError(f"Butler gateway error: {str(e)}") from e

