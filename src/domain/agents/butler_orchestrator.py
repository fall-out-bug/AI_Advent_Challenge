"""Butler Orchestrator for routing messages to mode handlers.

Main entry point for Butler Agent message processing.
Following Python Zen: Simple is better than complex.
"""

import logging
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.agents.handlers.chat_handler import ChatHandler
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.handlers.reminders_handler import RemindersHandler
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier
from src.domain.agents.state_machine import DialogContext, DialogState

logger = logging.getLogger(__name__)


class ButlerOrchestrator:
    """Main orchestrator for Butler Agent.

    Routes user messages to appropriate handlers based on mode classification.
    Following SOLID: Single Responsibility Principle - routing only.

    Attributes:
        mode_classifier: Service for classifying message modes
        task_handler: Handler for TASK mode
        data_handler: Handler for DATA mode
        reminders_handler: Handler for REMINDERS mode
        homework_handler: Handler for HOMEWORK_REVIEW mode
        chat_handler: Handler for IDLE mode
        mongodb: MongoDB database for context storage
        context_collection: MongoDB collection for dialog contexts
    """

    def __init__(
        self,
        mode_classifier: ModeClassifier,
        task_handler: TaskHandler,
        data_handler: DataHandler,
        reminders_handler: RemindersHandler,
        homework_handler: HomeworkHandler,
        chat_handler: ChatHandler,
        mongodb: AsyncIOMotorDatabase,
    ):
        """Initialize Butler orchestrator.

        Args:
            mode_classifier: Mode classification service
            task_handler: Task mode handler
            data_handler: Data mode handler
            reminders_handler: Reminders mode handler
            homework_handler: Homework review mode handler
            chat_handler: Chat/IDLE mode handler
            mongodb: MongoDB database instance
        """
        self.mode_classifier = mode_classifier
        self.task_handler = task_handler
        self.data_handler = data_handler
        self.reminders_handler = reminders_handler
        self.homework_handler = homework_handler
        self.chat_handler = chat_handler
        self.mongodb = mongodb
        self.context_collection = mongodb.dialog_contexts

    async def handle_user_message(
        self,
        user_id: str,
        message: str,
        session_id: str,
        force_mode: Optional[DialogMode] = None,
    ) -> str:
        """Handle user message - main entry point.

        Args:
            user_id: User identifier
            message: User message text
            session_id: Session identifier
            force_mode: Optional dialog mode to force (bypasses classification)

        Returns:
            Response text to send to user

        Example:
            >>> orchestrator = ButlerOrchestrator(...)
            >>> response = await orchestrator.handle_user_message(
            ...     user_id="123",
            ...     message="Create a task to buy milk",
            ...     session_id="456"
            ... )
            >>> response
            '✅ Task created successfully!'
        """
        try:
            context = await self._get_or_create_context(user_id, session_id)
            if force_mode:
                mode = force_mode
                logger.debug(f"Using forced mode: {force_mode.value}")
            else:
                mode = await self.mode_classifier.classify(message)
            handler = self._get_handler_for_mode(mode)
            response = await handler.handle(context, message)
            await self._save_context(context)
            return response
        except Exception as e:
            logger.error(f"Error handling user message: {e}", exc_info=True)
            return "❌ Sorry, I encountered an error. Please try again."

    async def _get_or_create_context(
        self, user_id: str, session_id: str
    ) -> DialogContext:
        """Get existing context or create new one.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            DialogContext instance
        """
        doc = await self.context_collection.find_one({"session_id": session_id})
        if doc:
            return self._deserialize_context(doc)
        return DialogContext(
            state=DialogState.IDLE,
            user_id=user_id,
            session_id=session_id,
        )

    async def _save_context(self, context: DialogContext) -> None:
        """Save context to MongoDB.

        Args:
            context: Dialog context to save
        """
        doc = self._serialize_context(context)
        await self.context_collection.update_one(
            {"session_id": context.session_id},
            {"$set": doc},
            upsert=True,
        )

    def _get_handler_for_mode(self, mode: DialogMode) -> Any:
        """Get handler for dialog mode.

        Args:
            mode: Dialog mode enum

        Returns:
            Handler instance

        Raises:
            ValueError: If mode is unknown
        """
        handlers = {
            DialogMode.TASK: self.task_handler,
            DialogMode.DATA: self.data_handler,
            DialogMode.REMINDERS: self.reminders_handler,
            DialogMode.HOMEWORK_REVIEW: self.homework_handler,
            DialogMode.IDLE: self.chat_handler,
        }
        if mode not in handlers:
            logger.warning(f"Unknown mode: {mode}, falling back to chat")
            return self.chat_handler
        return handlers[mode]

    def _serialize_context(self, context: DialogContext) -> dict:
        """Serialize context to dictionary.

        Args:
            context: Dialog context

        Returns:
            Dictionary representation
        """
        return {
            "user_id": context.user_id,
            "session_id": context.session_id,
            "state": context.state.value,
            "data": context.data,
            "step_count": context.step_count,
        }

    def _deserialize_context(self, doc: dict) -> DialogContext:
        """Deserialize context from dictionary.

        Args:
            doc: MongoDB document

        Returns:
            DialogContext instance
        """
        return DialogContext(
            state=DialogState(doc["state"]),
            user_id=doc["user_id"],
            session_id=doc["session_id"],
            data=doc.get("data", {}),
            step_count=doc.get("step_count", 0),
        )
