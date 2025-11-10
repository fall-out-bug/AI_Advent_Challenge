"""Butler orchestrator for routing messages between dialog modes."""

from __future__ import annotations

import logging
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dtos.butler_dialog_dtos import DialogContext, DialogMode, DialogState
from src.application.services.mode_classifier import ModeClassifier
from src.presentation.bot.handlers.base import Handler

logger = logging.getLogger(__name__)


class ButlerOrchestrator:
    """Coordinate dialog mode selection and handler execution."""

    def __init__(
        self,
        mode_classifier: ModeClassifier,
        task_handler: Handler,
        data_handler: Handler,
        homework_handler: Handler,
        chat_handler: Handler,
        mongodb: AsyncIOMotorDatabase,
    ) -> None:
        """Store dependencies required to process user messages."""
        self._mode_classifier = mode_classifier
        self._handlers = {
            DialogMode.TASK: task_handler,
            DialogMode.DATA: data_handler,
            DialogMode.HOMEWORK_REVIEW: homework_handler,
            DialogMode.IDLE: chat_handler,
        }
        self._chat_handler = chat_handler
        self._mongodb = mongodb
        self._contexts = mongodb.dialog_contexts

    @property
    def mongodb(self) -> AsyncIOMotorDatabase:
        """Return underlying MongoDB instance for compatibility with tests."""
        return self._mongodb

    async def handle_user_message(
        self,
        user_id: str,
        message: str,
        session_id: str,
        force_mode: Optional[DialogMode] = None,
    ) -> str:
        """Classify message, delegate to handler, and persist context."""
        try:
            context = await self._get_or_create_context(user_id, session_id)
            mode = force_mode or await self._mode_classifier.classify(message)
            handler = self._handlers.get(mode, self._chat_handler)
            if handler is self._chat_handler and mode not in self._handlers:
                logger.warning("Unknown mode %s, falling back to chat", mode)
            response = await handler.handle(context, message)
            await self._save_context(context)
            return response
        except Exception as exc:  # noqa: BLE001
            logger.error("Error handling user message: %s", exc, exc_info=True)
            return "❌ Sorry, I encountered an error. Please try again."

    async def _get_or_create_context(
        self, user_id: str, session_id: str
    ) -> DialogContext:
        """Fetch stored dialog context or create a new one."""
        document = await self._contexts.find_one({"session_id": session_id})
        if document:
            return self._deserialize_context(document)
        return DialogContext(
            state=DialogState.IDLE,
            user_id=user_id,
            session_id=session_id,
        )

    async def _save_context(self, context: DialogContext) -> None:
        """Persist dialog context to MongoDB."""
        payload = self._serialize_context(context)
        await self._contexts.update_one(
            {"session_id": context.session_id},
            {"$set": payload},
            upsert=True,
        )

    def _serialize_context(self, context: DialogContext) -> dict[str, Any]:
        """Convert context dataclass into Mongo-friendly dict."""
        return {
            "user_id": context.user_id,
            "session_id": context.session_id,
            "state": context.state.value,
            "data": context.data,
            "step_count": context.step_count,
        }

    def _deserialize_context(self, document: dict[str, Any]) -> DialogContext:
        """Deserialize Mongo document into dialog context dataclass."""
        return DialogContext(
            state=DialogState(document["state"]),
            user_id=document["user_id"],
            session_id=document["session_id"],
            data=document.get("data", {}),
            step_count=document.get("step_count", 0),
        )
