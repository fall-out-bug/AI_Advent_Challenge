"""Task handler for Butler Agent TASK mode.

Handles task creation and management using IntentOrchestrator and MCP tools.
Following Python Zen: Simple is better than complex.
"""

import logging
from typing import Any, Dict, Optional

from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType

logger = logging.getLogger(__name__)


class TaskHandler(Handler):
    """Handler for TASK mode - task creation and management.

    Uses IntentOrchestrator to parse task intent, then saves via MCP.
    Following SOLID: Single Responsibility Principle.
    """

    def __init__(
        self,
        create_task_use_case: CreateTaskUseCase,
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ):
        """Initialize task handler."""
        self._create_task_use_case = create_task_use_case
        self.hybrid_classifier = hybrid_classifier

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle task creation request.

        Uses hybrid classifier for intent detection and logging if available.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text to send to user
        """
        # Use hybrid classifier for intent detection and logging (if available)
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                logger.debug(
                    f"TaskHandler: intent={intent_result.intent.value}, "
                    f"confidence={intent_result.confidence:.2f}, entities={intent_result.entities}"
                )
                # Log intent for observability
                if intent_result.intent not in [
                    IntentType.TASK,
                    IntentType.TASK_CREATE,
                    IntentType.TASK_LIST,
                    IntentType.TASK_UPDATE,
                    IntentType.TASK_DELETE,
                ]:
                    logger.warning(
                        f"TaskHandler received non-task intent: {intent_result.intent.value}"
                    )
            except Exception as e:
                logger.debug(f"Hybrid classifier failed in TaskHandler: {e}")

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
        except Exception as e:  # noqa: BLE001
            logger.error(f"Task handling failed: {e}", exc_info=True)
            return "❌ Sorry, I couldn't process your task request. Please try again."

    def _build_response(
        self, context: DialogContext, result: TaskCreationResult
    ) -> str:
        """Convert TaskCreationResult into a user-facing message."""

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
