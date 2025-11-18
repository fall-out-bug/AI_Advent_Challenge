"""Voice message handler for Telegram bot.

Purpose:
    Handles voice and audio messages: downloads audio, transcribes via STT,
<<<<<<< HEAD
    processes through use case, and executes command immediately.
=======
    processes through use case, and sends confirmation to user.
>>>>>>> origin/master
"""

from __future__ import annotations

import asyncio
<<<<<<< HEAD
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

if TYPE_CHECKING:
    from typing import Any
else:
    Any = object

=======
from uuid import uuid4

>>>>>>> origin/master
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
<<<<<<< HEAD
_personalized_reply_use_case: Optional[Any] = None
=======
>>>>>>> origin/master


def setup_voice_handler(
    process_use_case: ProcessVoiceCommandUseCase,
    confirmation_use_case: HandleVoiceConfirmationUseCase,
<<<<<<< HEAD
    personalized_reply_use_case: Optional[Any] = None,
=======
>>>>>>> origin/master
) -> Router:
    """Setup voice handler with use case dependencies.

    Purpose:
        Configure router with use case dependencies for voice message
        and callback handlers.

    Args:
        process_use_case: ProcessVoiceCommandUseCase instance.
        confirmation_use_case: HandleVoiceConfirmationUseCase instance.
<<<<<<< HEAD
        personalized_reply_use_case: Optional PersonalizedReplyUseCase for personalization.
=======
>>>>>>> origin/master

    Returns:
        Configured aiogram Router with voice and callback handlers.

    Example:
        >>> process_use_case = ProcessVoiceCommandUseCase(...)
        >>> confirmation_use_case = HandleVoiceConfirmationUseCase(...)
<<<<<<< HEAD
        >>> router = setup_voice_handler(process_use_case, confirmation_use_case, personalized_reply_use_case)
        >>> dp.include_router(router)
    """
    global _process_use_case, _confirmation_use_case, _personalized_reply_use_case
    _process_use_case = process_use_case
    _confirmation_use_case = confirmation_use_case
    _personalized_reply_use_case = personalized_reply_use_case
=======
        >>> router = setup_voice_handler(process_use_case, confirmation_use_case)
        >>> dp.include_router(router)
    """
    global _process_use_case, _confirmation_use_case
    _process_use_case = process_use_case
    _confirmation_use_case = confirmation_use_case
>>>>>>> origin/master

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
<<<<<<< HEAD
    """Handle voice/audio message from user.

    Purpose:
        Downloads audio file, transcribes via STT, processes through use case,
        and executes command immediately without confirmation.

    Args:
        message: Telegram message with voice/audio content.

    Example:
        >>> # Handler is registered automatically via setup_voice_handler
        >>> # No direct call needed
=======
    """Handle voice or audio message.

    Purpose:
        Downloads audio file from Telegram, creates ProcessVoiceCommandInput,
        invokes ProcessVoiceCommandUseCase, and handles errors.

    Args:
        message: Telegram message with voice or audio attachment.

    Example:
        >>> await handle_voice_message(message)
>>>>>>> origin/master
    """
    if not message.from_user:
        logger.warning("Received voice message without user")
        return

<<<<<<< HEAD
    user_id = str(message.from_user.id)
    command_id = uuid4()

    global _process_use_case
    if _process_use_case is None:
        logger.error("ProcessVoiceCommandUseCase not initialized")
        await message.answer("❌ Ошибка: сервис обработки голосовых команд недоступен.")
=======
    global _process_use_case
    if _process_use_case is None:
        logger.error("ProcessVoiceCommandUseCase not initialized")
        try:
            await message.answer(
                "❌ Ошибка: сервис обработки голосовых сообщений недоступен."
            )
        except Exception:
            pass
>>>>>>> origin/master
        return

    process_use_case = _process_use_case

<<<<<<< HEAD
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
=======
    user_id = str(message.from_user.id)
    command_id = uuid4()

    logger.info(
        "Processing voice message",
        extra={
            "user_id": user_id,
            "command_id": str(command_id),
            "message_id": message.message_id,
            "content_type": message.content_type,
        },
    )

    try:
        # Download audio file
        if message.voice:
            file_id = message.voice.file_id
            duration = message.voice.duration
        elif message.audio:
            file_id = message.audio.file_id
            duration = message.audio.duration or 0
        else:
            logger.warning("Message has no voice or audio attachment")
            await message.answer(
                "❌ Не удалось распознать голосовое сообщение. "
>>>>>>> origin/master
                "Попробуйте отправить сообщение заново."
            )
            return

<<<<<<< HEAD
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
=======
        # Get file from Telegram
        file = await message.bot.get_file(file_id)

        # Download file content
        # aiogram returns BytesIO object (synchronous file-like object)
        audio_file = await message.bot.download_file(file.file_path)

        # Read audio bytes from BytesIO (synchronous read)
        try:
            if hasattr(audio_file, "read"):
                # BytesIO.read() is synchronous, NOT async - don't use await!
                audio_data = audio_file.read()
                # Close file if needed
                if hasattr(audio_file, "close"):
                    audio_file.close()
            elif isinstance(audio_file, bytes):
                # Already bytes
                audio_data = audio_file
            else:
                # Try to convert to bytes
                audio_data = bytes(audio_file) if hasattr(audio_file, "__iter__") else b""
        except Exception as e:
            logger.error(
                f"Failed to read audio file: {e}",
                extra={"user_id": user_id, "command_id": str(command_id)},
            )
            raise

        logger.debug(
            f"Downloaded audio: {len(audio_data)} bytes",
            extra={
                "voice_command_id": str(command_id),
                "user_id": user_id,
                "file_size": len(audio_data),
            },
        )

        if not audio_data:
>>>>>>> origin/master
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
<<<<<<< HEAD
            audio_bytes=audio_bytes,
=======
            audio_bytes=audio_data,
>>>>>>> origin/master
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

<<<<<<< HEAD
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

=======
>>>>>>> origin/master
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
<<<<<<< HEAD
=======
                from src.application.voice.dtos import HandleVoiceConfirmationInput

>>>>>>> origin/master
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
<<<<<<< HEAD
            exc_info=True,
=======
>>>>>>> origin/master
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
<<<<<<< HEAD
        >>> # Handler is registered automatically via setup_voice_handler
        >>> # No direct call needed
=======
        >>> await handle_voice_callback(callback)
>>>>>>> origin/master
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
<<<<<<< HEAD
        confirmation_input = HandleVoiceConfirmationInput(
=======
        # Create input for use case
        input_data = HandleVoiceConfirmationInput(
>>>>>>> origin/master
            command_id=command_id,
            user_id=user_id,
            action=action,
        )

<<<<<<< HEAD
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
=======
        # Answer callback query IMMEDIATELY (Telegram requires response within timeout)
        # Process command asynchronously after answering callback
        if action == "confirm":
            # Answer callback immediately to avoid timeout
            try:
                await callback.answer("✅ Команда подтверждена, выполняется...")
            except Exception as e:
                logger.warning(
                    "Failed to answer callback query (may be too old)",
                    extra={
                        "user_id": user_id,
                        "command_id": str(command_id),
                        "error": str(e),
                    },
                )
                # Continue anyway - we'll send response as new message

        # Handle confirmation (process in background after answering callback)
        response = await confirmation_use_case.execute(input_data)

        logger.info(
            "Confirmation use case executed",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "action": action,
                "response_type": type(response).__name__,
                "response_length": len(response) if response else 0,
                "response_empty": not response,
            },
        )

        # Send response to user
        if action == "confirm":
            # Send Butler response to user
            logger.debug(
                "Checking response before sending",
                extra={
                    "user_id": user_id,
                    "command_id": str(command_id),
                    "response": response[:100] if response else None,
                    "response_bool": bool(response),
                },
            )
            if response:
                logger.info(
                    "Sending Butler response to user",
                    extra={
                        "user_id": user_id,
                        "command_id": str(command_id),
                        "response_length": len(response),
                    },
                )
                try:
                    # Use callback.message if available, otherwise send directly
                    if callback.message:
                        await callback.message.answer(response)
                    else:
                        # Fallback: send message directly
                        await callback.bot.send_message(
                            chat_id=int(user_id),
                            text=response,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to send Butler response to user",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                            "error": str(e),
                        },
                    )
                    # Try to notify user about error
                    try:
                        await callback.message.answer(
                            "✅ Команда выполнена, но произошла ошибка при отправке ответа."
                        )
                    except Exception:
                        pass
            else:
                logger.warning(
                    "Empty Butler response",
                    extra={
                        "user_id": user_id,
                        "command_id": str(command_id),
                    },
                )
                # Send message directly since callback may be expired
                try:
                    if callback.message:
                        await callback.message.answer(
                            "✅ Команда обработана, но ответ пуст."
                        )
                    else:
                        await callback.bot.send_message(
                            chat_id=int(user_id),
                            text="✅ Команда обработана, но ответ пуст.",
                        )
                except Exception as e:
                    logger.error(
                        "Failed to send empty response message",
                        extra={
                            "user_id": user_id,
                            "command_id": str(command_id),
                            "error": str(e),
                        },
                    )
        else:
            # Reject action - callback already answered if needed
            try:
                await callback.answer("🔄 Команда отклонена", show_alert=False)
            except Exception:
                # Callback may be expired, continue anyway
                pass
            # Send rejection message if available
            if response:
                if callback.message:
                    await callback.message.answer(response)
                else:
                    await callback.bot.send_message(
                        chat_id=int(user_id),
                        text=response,
                    )

        logger.info(
            "Voice confirmation processed successfully",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
                "action": action,
            },
        )
>>>>>>> origin/master

    except Exception as e:
        logger.error(
            "Failed to process voice confirmation",
            extra={
                "user_id": user_id,
                "command_id": str(command_id),
<<<<<<< HEAD
                "error": str(e),
            },
            exc_info=True,
        )
        await callback.answer("❌ Ошибка при обработке команды.")
=======
                "action": action,
                "error": str(e),
            },
        )
        await callback.answer("❌ Ошибка при обработке команды.")

>>>>>>> origin/master
