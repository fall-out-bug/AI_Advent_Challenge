"""Voice message handler for Telegram bot.

Purpose:
    Handles voice and audio messages: downloads audio, transcribes via STT,
    processes through use case, and executes command immediately.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

if TYPE_CHECKING:
    from typing import Any
else:
    Any = object

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.application.voice.dtos import (
    HandleVoiceConfirmationInput,
    ProcessVoiceCommandInput,
)
from src.application.voice.use_cases.handle_voice_confirmation import (
    HandleVoiceConfirmationUseCase,
)
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.infrastructure.logging import get_logger

logger = get_logger("voice_handler")

# Global use case instances (set by setup_voice_handler)
_process_use_case: ProcessVoiceCommandUseCase | None = None
_confirmation_use_case: HandleVoiceConfirmationUseCase | None = None
_personalized_reply_use_case: Optional[Any] = None


def setup_voice_handler(
    process_use_case: ProcessVoiceCommandUseCase,
    confirmation_use_case: HandleVoiceConfirmationUseCase,
    personalized_reply_use_case: Optional[Any] = None,
) -> Router:
    """Setup voice handler with use case dependencies.

    Purpose:
        Configure router with use case dependencies for voice message
        and callback handlers.

    Args:
        process_use_case: ProcessVoiceCommandUseCase instance.
        confirmation_use_case: HandleVoiceConfirmationUseCase instance.
        personalized_reply_use_case: Optional PersonalizedReplyUseCase for personalization.

    Returns:
        Configured aiogram Router with voice and callback handlers.

    Example:
        >>> process_use_case = ProcessVoiceCommandUseCase(...)
        >>> confirmation_use_case = HandleVoiceConfirmationUseCase(...)
        >>> router = setup_voice_handler(process_use_case, confirmation_use_case, personalized_reply_use_case)
        >>> dp.include_router(router)
    """
    global _process_use_case, _confirmation_use_case, _personalized_reply_use_case
    _process_use_case = process_use_case
    _confirmation_use_case = confirmation_use_case
    _personalized_reply_use_case = personalized_reply_use_case

    router = Router()

    # Register voice/audio message handler
    router.message.register(
        handle_voice_message,
        F.content_type.in_(["voice", "audio"]),
    )

    # Register callback handler for confirmation buttons
    router.callback_query.register(
        handle_voice_callback,
        F.data.startswith("voice_"),
    )

    return router


async def handle_voice_message(message: Message) -> None:
    """Handle voice/audio message from user.

    Purpose:
        Downloads audio file, transcribes via STT, processes through use case,
        and executes command immediately without confirmation.

    Args:
        message: Telegram message with voice/audio content.

    Example:
        >>> # Handler is registered automatically via setup_voice_handler
        >>> # No direct call needed
    """
    if not message.from_user:
        logger.warning("Received voice message without user")
        return

    user_id = str(message.from_user.id)
    command_id = uuid4()

    global _process_use_case
    if _process_use_case is None:
        logger.error("ProcessVoiceCommandUseCase not initialized")
        await message.answer("❌ Ошибка: сервис обработки голосовых команд недоступен.")
        return

    process_use_case = _process_use_case

    try:
        # Get audio file
        if message.voice:
            audio_file = message.voice
            duration = message.voice.duration or 0
        elif message.audio:
            audio_file = message.audio
            duration = message.audio.duration or 0
        else:
            logger.warning("Message has no voice or audio content")
            await message.answer(
                "❌ Ошибка: не удалось получить аудио. Попробуйте отправить сообщение заново."
            )
            return

        # Download audio file
        file = await message.bot.get_file(audio_file.file_id)
        audio_data = await message.bot.download_file(file.file_path)

        if audio_data is None:
            logger.warning("Downloaded audio file is None")
            await message.answer(
                "❌ Не удалось загрузить голосовое сообщение. "
                "Попробуйте отправить сообщение заново."
            )
            return

        # Read audio bytes
        # In aiogram 3.x, download_file returns bytes directly or a file-like object
        if isinstance(audio_data, bytes):
            audio_bytes = audio_data
        elif hasattr(audio_data, 'read'):
            # If it's a file-like object with read method, check if it's async
            read_method = getattr(audio_data, 'read', None)
            if read_method and callable(read_method):
                # Check if read() is a coroutine (async method)
                import inspect
                if inspect.iscoroutinefunction(read_method):
                    audio_bytes = await read_method()
                else:
                    audio_bytes = read_method()
            else:
                audio_bytes = bytes(audio_data) if audio_data else b''
        else:
            # Try to convert to bytes
            try:
                audio_bytes = bytes(audio_data)
            except (TypeError, ValueError):
                audio_bytes = b''

        logger.info(
            "Voice message received",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "file_size": len(audio_bytes),
            },
        )

        if not audio_bytes:
            logger.warning("Downloaded audio file is empty")
            await message.answer(
                "❌ Не удалось загрузить голосовое сообщение. "
                "Попробуйте отправить сообщение заново."
            )
            return

        # Create input for use case
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id=user_id,
            audio_bytes=audio_bytes,
            duration_seconds=float(duration),
        )

        # Process voice command
        transcription = await process_use_case.execute(input_data)

        logger.info(
            "Voice command processed successfully",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "transcription_length": len(transcription.text),
                "confidence": transcription.confidence,
            },
        )

        # Check if personalization is enabled
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        if (
            settings.personalization_enabled
            and _personalized_reply_use_case is not None
        ):
            logger.info(
                "Routing voice transcription through personalized reply",
                extra={
                    "user_id": user_id,
                    "transcription": transcription.text[:50],
                },
            )

            try:
                from src.application.personalization.dtos import (
                    PersonalizedReplyInput,
                )

                input_data = PersonalizedReplyInput(
                    user_id=user_id,
                    text=transcription.text,
                    source="voice",
                )

                output = await _personalized_reply_use_case.execute(input_data)

                # Send transcription + personalized reply
                await message.answer(
                    f"🎤 Распознала: «{transcription.text[:500]}{'...' if len(transcription.text) > 500 else ''}»\n\n"
                    f"{output.reply}"
                )

                logger.info(
                    "Voice command processed with personalization",
                    extra={
                        "user_id": user_id,
                        "used_persona": output.used_persona,
                    },
                )
                return

            except Exception as e:
                logger.error(
                    "Personalized voice reply failed",
                    extra={"user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                # Fall through to fallback

        # Execute command immediately without confirmation
        # Send transcription result to user and execute via Butler
        try:
            await message.answer(
                f"🎤 Распознала: «{transcription.text[:500]}{'...' if len(transcription.text) > 500 else ''}»\n\n"
                "⏳ Выполняю команду..."
            )

            # Execute command immediately via confirmation use case
            global _confirmation_use_case
            if _confirmation_use_case is not None:
                confirmation_input = HandleVoiceConfirmationInput(
                    command_id=command_id,
                    user_id=user_id,
                    action="confirm",  # Auto-confirm and execute
                )

                response = await _confirmation_use_case.execute(confirmation_input)

                # Send Butler's response to user
                if response:
                    logger.info(
                        "Voice command executed successfully",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                            "response_length": len(response),
                        },
                    )
                    await message.answer(response)
                else:
                    logger.warning(
                        "Empty Butler response",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                        },
                    )
                    await message.answer(
                        "✅ Команда обработана, но ответ пуст."
                    )
            else:
                logger.error("HandleVoiceConfirmationUseCase not initialized")
                await message.answer(
                    "❌ Ошибка: сервис выполнения команд недоступен."
                )

        except Exception as e:
            logger.error(
                "Failed to execute voice command",
                extra={
                    "user_id": user_id,
                    "command_id": str(command_id),
                    "error": str(e),
                },
                exc_info=True,
            )
            await message.answer(
                "❌ Ошибка при выполнении команды. Попробуйте отправить текст команды вручную."
            )

    except ValueError as e:
        logger.warning(
            "Voice command validation failed",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "error": str(e),
            },
        )
        await message.answer(
            f"❌ Ошибка валидации: {str(e)}. "
            "Попробуйте отправить голосовое сообщение заново."
        )

    except Exception as e:
        logger.error(
            "Failed to process voice message",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "error": str(e),
            },
            exc_info=True,
        )
        await message.answer(
            "❌ Не удалось распознать голос. Попробуйте записать заново."
        )


async def handle_voice_callback(callback: CallbackQuery) -> None:
    """Handle voice confirmation callback.

    Purpose:
        Processes user confirmation or rejection of transcribed voice command.
        Parses callback_data, creates HandleVoiceConfirmationInput,
        invokes HandleVoiceConfirmationUseCase, and sends response.

    Args:
        callback: Telegram callback query with voice confirmation action.

    Example:
        >>> # Handler is registered automatically via setup_voice_handler
        >>> # No direct call needed
    """
    if not callback.data or not callback.from_user:
        logger.warning("Received callback without data or user")
        return

    # Parse callback data: "voice_confirm:{command_id}" or "voice_reject:{command_id}"
    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        logger.warning(f"Invalid callback data format: {callback.data}")
        await callback.answer("❌ Ошибка: неверный формат данных.")
        return

    action_type = parts[0]  # "voice_confirm" or "voice_reject"
    command_id_str = parts[1]

    global _confirmation_use_case
    if _confirmation_use_case is None:
        logger.error("HandleVoiceConfirmationUseCase not initialized")
        await callback.answer("❌ Ошибка: сервис недоступен.")
        return

    confirmation_use_case = _confirmation_use_case

    try:
        from uuid import UUID

        command_id = UUID(command_id_str)
    except ValueError:
        logger.warning(f"Invalid command_id in callback: {command_id_str}")
        await callback.answer("❌ Ошибка: неверный ID команды.")
        return

    user_id = str(callback.from_user.id)

    # Map action type
    if action_type == "voice_confirm":
        action = "confirm"
    elif action_type == "voice_reject":
        action = "reject"
    else:
        logger.warning(f"Unknown action type: {action_type}")
        await callback.answer("❌ Ошибка: неизвестное действие.")
        return

    logger.info(
        "Processing voice confirmation callback",
        extra={
            "user_id": user_id,
            "command_id": str(command_id),
            "action": action,
        },
    )

    try:
        confirmation_input = HandleVoiceConfirmationInput(
            command_id=command_id,
            user_id=user_id,
            action=action,
        )

        response = await confirmation_use_case.execute(confirmation_input)

        await callback.answer("✅ Обработано")

        if callback.message:
            await callback.message.answer(response)

    except ValueError as e:
        logger.warning(
            "Voice confirmation validation failed",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "error": str(e),
            },
        )
        await callback.answer(f"❌ Ошибка: {str(e)}")

    except Exception as e:
        logger.error(
            "Failed to process voice confirmation",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "error": str(e),
            },
            exc_info=True,
        )
        await callback.answer("❌ Ошибка при обработке команды.")
