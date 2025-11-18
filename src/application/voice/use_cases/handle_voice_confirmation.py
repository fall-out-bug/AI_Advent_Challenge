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
    """

    def __init__(
        self,
        command_store: VoiceCommandStore,
        butler_gateway: ButlerGateway,
    ) -> None:
        self.command_store = command_store
        self.butler_gateway = butler_gateway

    async def execute(
        self,
        input_data: HandleVoiceConfirmationInput,
    ) -> str:
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
                "user_id": input_data.user_id,
                "action": input_data.action,
            },
        )

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

