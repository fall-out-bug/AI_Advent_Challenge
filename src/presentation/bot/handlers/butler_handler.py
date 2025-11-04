"""Butler handler for Telegram bot using ButlerOrchestrator.

Following Clean Architecture: Presentation layer delegates to domain layer.
Following Python Zen: Simple is better than complex.
"""

import base64
import logging
import re
from typing import Optional

from aiogram import Router, F
from aiogram.types import BufferedInputFile, Message

from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.services.mode_classifier import DialogMode
from src.infrastructure.logging import get_logger

logger = get_logger("butler_handler")

# Global orchestrator instance (set by setup_butler_handler)
_orchestrator: Optional[ButlerOrchestrator] = None


def setup_butler_handler(orchestrator: ButlerOrchestrator) -> Router:
    """Setup butler handler with orchestrator dependency.

    Purpose:
        Configure router with orchestrator dependency for handler functions.

    Args:
        orchestrator: ButlerOrchestrator instance for message processing

    Returns:
        Configured aiogram Router

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> router = setup_butler_handler(orchestrator)
        >>> dp.include_router(router)
    """
    global _orchestrator
    _orchestrator = orchestrator
    
    router = Router()
    router.message.register(handle_any_message, F.text)
    return router


async def handle_any_message(message: Message) -> None:
    """Handle any text message using ButlerOrchestrator.

    Purpose:
        Main entry point for processing user messages through ButlerOrchestrator.
        Extracts user_id and message text, delegates to orchestrator,
        and sends formatted response.

    Args:
        message: Telegram message object

    Example:
        >>> await handle_any_message(message)
    """
    if not message.text or not message.from_user:
        logger.warning("Received message without text or user")
        return

    if _orchestrator is None:
        logger.error("ButlerOrchestrator not initialized")
        await _handle_error(message, RuntimeError("Orchestrator not initialized"))
        return

    user_id = str(message.from_user.id)
    session_id = f"telegram_{user_id}_{message.message_id}"
    text = message.text

    logger.info(
        f"Processing message: user_id={user_id}, message_id={message.message_id}, text_preview={text[:50]}"
    )

    try:
        # Check if message contains commit hash - force HOMEWORK_REVIEW mode
        commit_hash = _extract_commit_hash(text)
        force_mode = None
        if commit_hash:
            force_mode = DialogMode.HOMEWORK_REVIEW
            await message.answer("⏳ Начал ревью коммита...")
        elif _is_review_command(text):
            # Also check for review keywords without hash (might be partial)
            force_mode = DialogMode.HOMEWORK_REVIEW
            await message.answer("⏳ Начал ревью коммита...")

        response = await _orchestrator.handle_user_message(
            user_id=user_id, message=text, session_id=session_id, force_mode=force_mode
        )
        # Check if response is a file format: "FILE:<filename>:<content>"
        if response.startswith("FILE:"):
            await _handle_file_response(message, response)
        else:
            await _safe_answer(message, response)
    except Exception as e:
        logger.error(
            f"Failed to handle message: user_id={user_id}, error={str(e)}",
            exc_info=True,
        )
        await _handle_error(message, e)


async def _safe_answer(message: Message, text: str) -> None:
    """Send response message with error handling.

    Purpose:
        Safely send Telegram message with retry logic and error handling.
        Handles message length limits and formatting.

    Args:
        message: Telegram message object
        text: Response text to send
    """
    MAX_MESSAGE_LENGTH = 4096  # Telegram limit

    try:
        if len(text) > MAX_MESSAGE_LENGTH:
            # Try to truncate at sentence boundary
            truncated = text[:MAX_MESSAGE_LENGTH - 50]  # Reserve space for truncation marker
            # Look for last sentence boundary
            last_period = truncated.rfind(".")
            last_exclamation = truncated.rfind("!")
            last_question = truncated.rfind("?")
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            if last_sentence_end > MAX_MESSAGE_LENGTH * 0.8:  # If found within last 20%
                text = truncated[:last_sentence_end + 1] + "\n\n_(сообщение обрезано)_"
            else:
                # Try paragraph boundary
                last_paragraph = truncated.rfind("\n\n")
                if last_paragraph > MAX_MESSAGE_LENGTH * 0.7:
                    text = truncated[:last_paragraph].strip() + "\n\n_(сообщение обрезано)_"
                else:
                    text = truncated + "\n\n_(сообщение обрезано)_"
        
        await message.answer(text, parse_mode="Markdown")
        logger.debug(f"Response sent successfully: user_id={message.from_user.id}")
    except Exception as e:
        logger.error(
            f"Failed to send response: user_id={message.from_user.id}, error={str(e)}"
        )
        try:
            await message.answer(
                "❌ Sorry, I encountered an error sending the response. "
                "Please try again."
            )
        except Exception:
            logger.error("Failed to send error message", user_id=message.from_user.id)


def _extract_commit_hash(message: str) -> Optional[str]:
    """Extract commit hash from message.

    Args:
        message: User message text

    Returns:
        Commit hash if found, None otherwise
    """
    # Patterns for commit hash (7-64 hex characters)
    patterns = [
        r"(?:сделай|do|make)\s+ревью\s+([a-f0-9]{7,64})",
        r"ревью\s+([a-f0-9]{7,64})",
        r"review\s+([a-f0-9]{7,64})",
        r"проверь\s+коммит\s+([a-f0-9]{7,64})",
        r"check\s+commit\s+([a-f0-9]{7,64})",
        # Also match standalone hash if it's very long (likely commit hash)
        r"\b([a-f0-9]{40,64})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _is_review_command(message: str) -> bool:
    """Check if message is a review command.

    Args:
        message: User message text

    Returns:
        True if message is a review command
    """
    message_lower = message.lower()
    review_keywords = [
        "сделай ревью",
        "do review",
        "review",
        "ревью",
        "проверь коммит",
        "check commit",
    ]
    return any(keyword in message_lower for keyword in review_keywords)


async def _handle_file_response(message: Message, file_response: str) -> None:
    """Handle file response from handler.

    Purpose:
        Parse FILE: format and send as document.

    Args:
        message: Telegram message object
        file_response: Response in format "FILE:<filename>:<content>"
    """
    try:
        # Parse format: FILE:<filename>:<content>
        if not file_response.startswith("FILE:"):
            logger.error(f"Invalid file response format: {file_response[:100]}")
            await message.answer("❌ Ошибка обработки файла.")
            return

        parts = file_response[5:].split(":", 1)  # Remove "FILE:" prefix
        if len(parts) != 2:
            logger.error(f"Invalid file response format: {file_response[:100]}")
            await message.answer("❌ Ошибка обработки файла.")
            return

        filename = parts[0]
        content_b64 = parts[1]

        # Decode base64 content
        try:
            content_bytes = base64.b64decode(content_b64)
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            await message.answer("❌ Ошибка декодирования файла.")
            return

        # Send as document
        document = BufferedInputFile(content_bytes, filename=filename)
        await message.answer_document(document=document)
        logger.debug(f"File sent successfully: {filename}, size: {len(content_bytes)} bytes")

    except Exception as e:
        logger.error(
            f"Failed to send file: user_id={message.from_user.id}, error={str(e)}",
            exc_info=True,
        )
        try:
            await message.answer(
                "❌ Ошибка при отправке файла. Попробуйте позже."
            )
        except Exception:
            logger.error("Failed to send error message", user_id=message.from_user.id)


async def _handle_error(message: Message, error: Exception) -> None:
    """Handle errors gracefully with user-friendly message.

    Purpose:
        Send error message to user when processing fails.

    Args:
        message: Telegram message object
        error: Exception that occurred
    """
    try:
        await message.answer(
            "❌ Sorry, I encountered an error processing your message. "
            "Please try again or use /menu for available commands."
        )
    except Exception as e:
        user_id = message.from_user.id if message.from_user else None
        logger.error(
            f"Failed to send error message: user_id={user_id}, error={str(e)}"
        )

