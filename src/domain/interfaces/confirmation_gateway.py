"""Confirmation gateway protocol for voice commands.

Purpose:
    Defines interface for sending confirmation messages to users
    with inline buttons for voice command confirmation.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class ConfirmationGateway(Protocol):
    """Protocol for sending voice command confirmation messages.

    Purpose:
        Defines a canonical interface for sending confirmation prompts
        to users, decoupling domain logic from specific messaging
        implementations (Telegram, etc.). Enables testability by
        allowing mocking in use case tests.

    Methods:
        send_confirmation: Send confirmation message with inline buttons.
    """

    async def send_confirmation(
        self,
        user_id: str,
        text: str,
        command_id: UUID,
    ) -> None:
        """Send confirmation message to user with inline buttons.

        Purpose:
            Sends a message to the user showing the transcribed text
            and inline buttons for confirmation ("Подтвердить", "Повторить").

        Args:
            user_id: Telegram user identifier.
            text: Recognized transcription text to display.
            command_id: Voice command UUID for callback payload.

        Example:
            >>> gateway = TelegramConfirmationGateway(bot)
            >>> await gateway.send_confirmation(
            ...     user_id="123456789",
            ...     text="Сделай дайджест по каналу X",
            ...     command_id=UUID("12345678-1234-5678-1234-567812345678")
            ... )
        """
        ...


