<<<<<<< HEAD
"""Handle voice confirmation use case.

Purpose:
    Handles voice command confirmation: retrieves stored command text,
    routes to Butler for execution, and returns response.
"""

from src.application.voice.dtos import HandleVoiceConfirmationInput
from src.domain.interfaces.voice import ButlerGateway, VoiceCommandStore
from src.infrastructure.logging import get_logger

logger = get_logger("voice.handle_voice_confirmation")


class HandleVoiceConfirmationUseCase:
    """Use case for handling voice command confirmation.

    Purpose:
        Retrieves stored command text, routes to Butler for execution,
        and returns Butler response. Used for immediate execution
        (action="confirm") after transcription.

    Args:
        command_store: Voice command store for retrieving transcripts.
        butler_gateway: Butler gateway for routing commands.
=======
"""Handle voice command confirmation use case.

Purpose:
    Handles user confirmation or rejection of transcribed voice commands,
    routes confirmed commands to Butler pipeline, or deletes rejected commands.
"""

from __future__ import annotations

from typing import Optional

from src.application.voice.dtos import HandleVoiceConfirmationInput
from src.domain.interfaces import ButlerGateway, ConfirmationGateway
from src.domain.voice.exceptions import InvalidVoiceCommandError
from src.domain.voice.value_objects import VoiceCommandState
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.voice.command_store import VoiceCommandStore

logger = get_logger("use_cases.handle_voice_confirmation")


class HandleVoiceConfirmationUseCase:
    """Use case for handling voice command confirmations.

    Purpose:
        Processes user confirmation or rejection of transcribed voice commands.
        On confirm: retrieves command, generates session_id, calls ButlerGateway.
        On reject: deletes command and prompts user to resend.

    Args:
        command_store: Voice command storage (Redis or in-memory).
        butler_gateway: Gateway for routing commands to Butler orchestrator.
        confirmation_gateway: Gateway for sending messages to user.
        settings: Optional settings instance (defaults to get_settings()).
>>>>>>> origin/master
    """

    def __init__(
        self,
        command_store: VoiceCommandStore,
        butler_gateway: ButlerGateway,
<<<<<<< HEAD
    ) -> None:
        self.command_store = command_store
        self.butler_gateway = butler_gateway
=======
        confirmation_gateway: ConfirmationGateway,
        settings: Optional[Settings] = None,
    ) -> None:
        self.command_store = command_store
        self.butler_gateway = butler_gateway
        self.confirmation_gateway = confirmation_gateway
        self.settings = settings or get_settings()
>>>>>>> origin/master

    async def execute(
        self,
        input_data: HandleVoiceConfirmationInput,
    ) -> str:
<<<<<<< HEAD
        """Handle voice command confirmation.

        Purpose:
            Retrieves stored command text, routes to Butler if confirmed,
            and returns Butler response.

        Args:
            input_data: Input DTO with command ID, user ID, action.

        Returns:
            Response text from Butler orchestrator.

        Raises:
            ValueError: If command not found or action invalid.
            RuntimeError: If routing fails.

        Example:
            >>> use_case = HandleVoiceConfirmationUseCase(command_store, butler_gateway)
            >>> input_data = HandleVoiceConfirmationInput(
            ...     command_id=UUID(...),
            ...     user_id="123456789",
            ...     action="confirm",
            ... )
            >>> response = await use_case.execute(input_data)
            >>> response
            'Команда выполнена успешно.'
        """
        logger.info(
            "Handling voice confirmation",
            extra={
                "command_id": str(input_data.command_id),
=======
        """Execute voice command confirmation handling.

        Purpose:
            Processes confirmation or rejection action, retrieves stored command,
            routes to Butler on confirm, or deletes on reject.

        Args:
            input_data: Confirmation input with command_id, user_id, and action.

        Returns:
            Response text from Butler (on confirm) or empty string (on reject).

        Raises:
            InvalidVoiceCommandError: If command not found or invalid state.
            RuntimeError: If Butler gateway or confirmation gateway fails.

        Example:
            >>> use_case = HandleVoiceConfirmationUseCase(...)
            >>> input_data = HandleVoiceConfirmationInput(
            ...     command_id=uuid4(),
            ...     user_id="123456789",
            ...     action="confirm"
            ... )
            >>> response = await use_case.execute(input_data)
            >>> response
            "Дайджест по каналу onaboka за последние 24 часа..."
        """
        logger.info(
            "Handling voice command confirmation",
            extra={
                "voice_command_id": str(input_data.command_id),
>>>>>>> origin/master
                "user_id": input_data.user_id,
                "action": input_data.action,
            },
        )

<<<<<<< HEAD
        # Retrieve stored command text
        command_text = await self.command_store.get(
            command_id=str(input_data.command_id),
            user_id=input_data.user_id,
        )

        if command_text is None:
            logger.warning(
                "Command not found in store",
                extra={
                    "command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                },
            )
            raise ValueError(f"Command {input_data.command_id} not found or expired")

        # Handle action
        if input_data.action == "confirm":
            # Route to Butler for execution
            session_id = f"voice_{input_data.user_id}_{input_data.command_id}"

            try:
                response = await self.butler_gateway.handle_user_message(
                    user_id=input_data.user_id,
                    text=command_text,
                    session_id=session_id,
                )

                # Delete stored command after execution
                await self.command_store.delete(
                    command_id=str(input_data.command_id),
                    user_id=input_data.user_id,
                )

                logger.info(
                    "Voice command executed successfully",
                    extra={
                        "command_id": str(input_data.command_id),
                        "user_id": input_data.user_id,
                        "response_length": len(response),
                    },
                )

                return response

            except Exception as e:
                logger.error(
                    "Failed to execute voice command via Butler",
                    extra={
                        "command_id": str(input_data.command_id),
                        "user_id": input_data.user_id,
                        "error": str(e),
                    },
                )
                raise RuntimeError(f"Failed to execute command: {str(e)}") from e

        elif input_data.action == "reject":
            # Delete stored command
            await self.command_store.delete(
                command_id=str(input_data.command_id),
                user_id=input_data.user_id,
            )

            logger.info(
                "Voice command rejected",
                extra={
                    "command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                },
            )

            return "Команда отменена."

        else:
            raise ValueError(f"Invalid action: {input_data.action}")
=======
        # Retrieve stored command
        command = await self.command_store.get(input_data.command_id)

        if command is None:
            error_msg = f"Voice command {input_data.command_id} not found or expired"
            logger.warning(
                error_msg,
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                },
            )
            raise InvalidVoiceCommandError(
                error_msg,
                command_id=str(input_data.command_id),
            )

        # Validate user_id matches
        if command.user_id != input_data.user_id:
            error_msg = (
                f"User ID mismatch: expected {command.user_id}, "
                f"got {input_data.user_id}"
            )
            logger.warning(
                error_msg,
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "command_user_id": command.user_id,
                },
            )
            raise InvalidVoiceCommandError(
                error_msg,
                command_id=str(input_data.command_id),
            )

        # Handle action
        if input_data.action == "confirm":
            return await self._handle_confirm(command, input_data.user_id)

        if input_data.action == "reject":
            return await self._handle_reject(command, input_data.user_id)

        # Should not reach here (action validated in DTO)
        raise ValueError(f"Invalid action: {input_data.action}")

    async def _handle_confirm(
        self,
        command: VoiceCommand,
        user_id: str,
    ) -> str:
        """Handle confirmation action.

        Args:
            command: Voice command to confirm.
            user_id: User identifier.

        Returns:
            Response text from Butler.
        """
        # Confirm command state
        try:
            command.confirm()
        except InvalidVoiceCommandError as e:
            logger.warning(
                "Cannot confirm command in current state",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                    "state": command.state.value,
                    "error": str(e),
                },
            )
            raise

        # Generate session_id as f"voice_{user_id}_{command_id}"
        session_id = f"voice_{user_id}_{command.id}"

        logger.info(
            "Confirming voice command and routing to Butler",
            extra={
                "voice_command_id": str(command.id),
                "user_id": user_id,
                "session_id": session_id,
                "transcription_text": command.transcription.text,
            },
        )

        # Route to Butler gateway
        try:
            response = await self.butler_gateway.handle_user_message(
                user_id=user_id,
                text=command.transcription.text,
                session_id=session_id,
            )

            logger.info(
                "Butler response received",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                    "response_length": len(response),
                },
            )

            # Delete command after successful execution
            try:
                await self.command_store.delete(command.id)
                logger.debug(
                    "Voice command deleted after confirmation",
                    extra={
                        "voice_command_id": str(command.id),
                        "user_id": user_id,
                    },
                )
            except Exception as e:
                logger.warning(
                    "Failed to delete command after confirmation",
                    extra={
                        "voice_command_id": str(command.id),
                        "user_id": user_id,
                        "error": str(e),
                    },
                )
                # Continue even if deletion fails

            return response

        except Exception as e:
            logger.error(
                "Failed to route command to Butler",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                    "error": str(e),
                },
            )
            raise RuntimeError("Failed to process voice command") from e

    async def _handle_reject(
        self,
        command: VoiceCommand,
        user_id: str,
    ) -> str:
        """Handle rejection action.

        Args:
            command: Voice command to reject.
            user_id: User identifier.

        Returns:
            Empty string (rejection message sent via gateway).
        """
        # Reject command state
        try:
            command.reject()
        except InvalidVoiceCommandError as e:
            logger.warning(
                "Cannot reject command in current state",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                    "state": command.state.value,
                    "error": str(e),
                },
            )
            raise

        logger.info(
            "Rejecting voice command",
            extra={
                "voice_command_id": str(command.id),
                "user_id": user_id,
            },
        )

        # Delete command
        try:
            await self.command_store.delete(command.id)
            logger.debug(
                "Voice command deleted after rejection",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                },
            )
        except Exception as e:
            logger.warning(
                "Failed to delete command after rejection",
                extra={
                    "voice_command_id": str(command.id),
                    "user_id": user_id,
                    "error": str(e),
                },
            )
            # Continue even if deletion fails

        # Send rejection message to user
        # Note: We reuse confirmation_gateway to send message, even though
        # it's called "confirmation" - it's just a messaging gateway
        # For MVP, we can send a simple text message or use a different method
        # For now, we'll just log and return empty string
        # The actual message sending can be handled in presentation layer

        rejection_message = "Команда отклонена. Запишите голос заново."
        logger.info(
            "Rejection message prepared",
            extra={
                "voice_command_id": str(command.id),
                "user_id": user_id,
                "message": rejection_message,
            },
        )

        # Return empty string (message will be sent by presentation layer)
        return rejection_message

>>>>>>> origin/master
