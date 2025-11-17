"""Butler gateway protocol for voice command execution.

Purpose:
    Defines interface for delegating confirmed voice command text
    to the Butler orchestrator pipeline.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ButlerGateway(Protocol):
    """Protocol for delegating voice commands to Butler orchestrator.

    Purpose:
        Defines a canonical interface for routing confirmed voice command
        text into the existing Butler/LLM pipeline, decoupling domain logic
        from specific orchestrator implementations. Enables testability by
        allowing mocking in use case tests.

        Implementation wraps ButlerOrchestrator.handle_user_message() in
        application layer adapter.

    Methods:
        handle_user_message: Delegate confirmed voice command text to Butler.
    """

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
            mode selection, and execution (e.g., digest generation).

        Args:
            user_id: User identifier (Telegram user ID).
            text: Confirmed transcription text from voice command.
            session_id: Session identifier (generated as
                `f"voice_{user_id}_{command_id}"` or from Butler session manager).

        Returns:
            Response text from Butler orchestrator to send to user.

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
        ...


