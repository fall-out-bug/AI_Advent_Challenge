"""Task handler for Butler bot TASK mode."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.application.dtos.butler_dialog_dtos import DialogContext
from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.domain.intent import HybridIntentClassifier, IntentType
from src.presentation.bot.handlers.base import Handler

logger = logging.getLogger(__name__)


class TaskHandler(Handler):
    """Handle task creation and management requests."""

    def __init__(
        self,
        create_task_use_case: CreateTaskUseCase,
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ) -> None:
        """Initialize handler with dependencies."""
        self._create_task_use_case = create_task_use_case
        self.hybrid_classifier = hybrid_classifier

    async def handle(self, context: DialogContext, message: str) -> str:
        """Process task-related user message."""
        if self.hybrid_classifier:
            await self._log_hybrid_intent(message)

        try:
            execution_context: Optional[Dict[str, Any]] = (
                context.data if context.data else None
            )
            result = await self._create_task_use_case.execute(
                user_id=int(context.user_id),
                message=message,
                context=execution_context,
            )
            return self._build_response(context, result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Task handling failed: %s", exc, exc_info=True)
            return "❌ Sorry, I couldn't process your task request. Please try again."

    async def _log_hybrid_intent(self, message: str) -> None:
        """Invoke hybrid classifier for observability."""
        if not self.hybrid_classifier:
            return
        try:
            intent_result = await self.hybrid_classifier.classify(message)
            logger.debug(
                "TaskHandler intent=%s confidence=%.2f entities=%s",
                intent_result.intent.value,
                intent_result.confidence,
                intent_result.entities,
            )
            if intent_result.intent not in [
                IntentType.TASK,
                IntentType.TASK_CREATE,
                IntentType.TASK_LIST,
                IntentType.TASK_UPDATE,
                IntentType.TASK_DELETE,
            ]:
                logger.warning(
                    "TaskHandler received non-task intent: %s",
                    intent_result.intent.value,
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Hybrid classifier failed in TaskHandler: %s", exc)

    def _build_response(
        self, context: DialogContext, result: TaskCreationResult
    ) -> str:
        """Convert TaskCreationResult into user-facing message."""
        if result.clarification:
            context.transition_to(context.state)
            if result.intent_payload:
                context.update_data("pending_intent", result.intent_payload)
            return f"❓ {result.clarification}"

        if result.created:
            context.reset()
            task_id = result.task_id or "unknown"
            return f"✅ Task created successfully! (ID: {task_id})"

        if result.error:
            return f"❌ {result.error}"

        logger.warning("TaskCreationResult returned without status or error.")
        return "⚠️ Unable to process the task request. Please try again."
