"""Use case for creating tasks via Butler Agent.

Following Clean Architecture: Business logic is separated from domain handlers.
Following TDD: Implementation after tests.
"""

import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.application.usecases.result_types import TaskCreationResult
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class CreateTaskUseCase:
    """Use case for creating tasks.

    Purpose:
        Encapsulates business logic for task creation: parsing intent,
        validating completeness, and saving via MCP tools.

    Example:
        >>> usecase = CreateTaskUseCase(intent_orch, tool_client, mongodb)
        >>> result = await usecase.execute(user_id=123, message="Buy milk")
        >>> if result.created:
        ...     print(f"Task created: {result.task_id}")
        >>> elif result.clarification:
        ...     print(f"Need clarification: {result.clarification}")
    """

    def __init__(
        self,
        intent_orch: IntentOrchestrator,
        tool_client: ToolClientProtocol,
        mongodb: AsyncIOMotorDatabase,
    ):
        """Initialize use case."""
        self.intent_orch = intent_orch
        self.tool_client = tool_client
        self.mongodb = mongodb

    async def execute(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskCreationResult:
        """Execute task creation use case."""
        try:
            intent_result = await self._parse_intent(message, context)
            if intent_result.needs_clarification:
                return self._build_clarification_result(intent_result)
            return await self._create_task_via_mcp(user_id, intent_result)
        except Exception as e:
            logger.error(f"Task creation failed: {e}", exc_info=True)
            return self._build_error_result(str(e))

    async def _parse_intent(
        self, message: str, context: Optional[Dict[str, Any]]
    ) -> Any:
        """Parse task intent from message.

        Args:
            message: User message text
            context: Optional conversation context

        Returns:
            IntentParseResult from orchestrator
        """
        return await self.intent_orch.parse_task_intent(message, context)

    def _build_clarification_result(self, intent_result: Any) -> TaskCreationResult:
        """Build clarification result."""
        question = (
            intent_result.questions[0] if intent_result.questions else "Need more info"
        )
        return TaskCreationResult(created=False, clarification=question)

    async def _create_task_via_mcp(
        self, user_id: int, intent_result: Any
    ) -> TaskCreationResult:
        """Create task via MCP tool.

        Args:
            user_id: Telegram user ID
            intent_result: Parsed intent result

        Returns:
            TaskCreationResult with creation status
        """
        params = self._build_mcp_params(user_id, intent_result)
        result = await self.tool_client.call_tool("add_task", params)
        return self._process_mcp_result(result)

    def _build_mcp_params(self, user_id: int, intent_result: Any) -> Dict[str, Any]:
        """Build MCP tool parameters from intent result."""
        return {
            "user_id": user_id,
            "title": intent_result.title,
            "description": intent_result.description or "",
            "deadline": intent_result.deadline_iso,
            "priority": intent_result.priority,
            "tags": intent_result.tags or [],
        }

    def _process_mcp_result(self, result: Dict[str, Any]) -> TaskCreationResult:
        """Process MCP tool response."""
        if result.get("status") == "error":
            return TaskCreationResult(
                created=False, error=result.get("error", "Unknown error")
            )
        task_id = result.get("task_id")
        if task_id:
            return TaskCreationResult(created=True, task_id=str(task_id))
        return TaskCreationResult(created=False, error="No task_id in response")

    def _build_error_result(self, error_msg: str) -> TaskCreationResult:
        """Build error result."""
        return TaskCreationResult(
            created=False, error=f"Task creation failed: {error_msg}"
        )
