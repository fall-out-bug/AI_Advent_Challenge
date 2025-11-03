"""Task handler for Butler Agent TASK mode.

Handles task creation and management using IntentOrchestrator and MCP tools.
Following Python Zen: Simple is better than complex.
"""

import logging
from typing import Any, Optional

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class TaskHandler(Handler):
    """Handler for TASK mode - task creation and management.

    Uses IntentOrchestrator to parse task intent, then saves via MCP.
    Following SOLID: Single Responsibility Principle.
    """

    def __init__(
        self,
        intent_orchestrator: IntentOrchestrator,
        tool_client: ToolClientProtocol,
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ):
        """Initialize task handler.

        Args:
            intent_orchestrator: Intent parsing orchestrator
            tool_client: MCP tool client for task creation
            hybrid_classifier: Optional hybrid intent classifier for intent detection and logging
        """
        self.intent_orchestrator = intent_orchestrator
        self.tool_client = tool_client
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
            intent_result = await self.intent_orchestrator.parse_task_intent(
                message, context.data
            )
            return await self._process_intent(context, intent_result)
        except Exception as e:
            logger.error(f"Task handling failed: {e}", exc_info=True)
            return "❌ Sorry, I couldn't process your task request. Please try again."

    async def _process_intent(
        self, context: DialogContext, intent_result: Any
    ) -> str:
        """Process parsed intent result.

        Args:
            context: Dialog context
            intent_result: Parsed intent result

        Returns:
            Response text
        """
        if intent_result.needs_clarification:
            question = intent_result.questions[0] if intent_result.questions else ""
            context.transition_to(context.state)
            context.update_data("pending_intent", intent_result)
            return f"❓ {question}"
        return await self._create_task(context, intent_result)

    async def _create_task(self, context: DialogContext, intent_result: Any) -> str:
        """Create task via MCP tool.

        Args:
            context: Dialog context
            intent_result: Parsed intent result

        Returns:
            Response text
        """
        task_params = {
            "user_id": context.user_id,
            "title": intent_result.title,
        }
        if intent_result.description:
            task_params["description"] = intent_result.description
        if intent_result.deadline_iso:
            task_params["deadline"] = intent_result.deadline_iso
        if intent_result.priority:
            task_params["priority"] = intent_result.priority

        result = await self.tool_client.call_tool("create_task", task_params)
        context.reset()
        task_id = result.get("id", "unknown")
        return f"✅ Task created successfully! (ID: {task_id})"

