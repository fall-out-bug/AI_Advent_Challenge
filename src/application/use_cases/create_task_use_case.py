"""Task creation use case for Butler flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class CreateTaskUseCase:
    """Create tasks via the MCP tooling layer.

    Purpose:
        Parse user intent, request clarifications when necessary, and invoke
        the MCP `add_task` tool with normalized parameters. Provides a typed
        result describing success, clarification needs, or failure.

    Args:
        intent_orchestrator: Service responsible for parsing task intents.
        tool_client: MCP tool client used to call task-related tools.
        mongodb: Mongo database instance (kept for compatibility with legacy flows).

    Example:
        >>> use_case = CreateTaskUseCase(intent_orchestrator, tool_client, mongodb)
        >>> result = await use_case.execute(user_id=123, message="Buy milk tomorrow")
        >>> result.created
        True
    """

    def __init__(
        self,
        intent_orchestrator: IntentOrchestrator,
        tool_client: ToolClientProtocol,
        mongodb: AsyncIOMotorDatabase,
    ) -> None:
        self._intent_orchestrator = intent_orchestrator
        self._tool_client = tool_client
        self._mongodb = mongodb

    async def execute(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskCreationResult:
        """Execute task creation workflow.

        Purpose:
            Parse the user's intent, request clarifications when the payload is
            incomplete, and create the task via MCP.

        Args:
            user_id: Telegram user identifier.
            message: User message containing task information.
            context: Optional dialog context.

        Returns:
            TaskCreationResult describing the outcome.
        """

        try:
            intent_result = await self._parse_intent(message, context)
            if intent_result.needs_clarification:
                return self._build_clarification_result(intent_result)
            return await self._create_task(user_id, intent_result)
        except Exception as error:  # noqa: BLE001
            logger.error("Task creation failed", exc_info=True, extra={"error": str(error)})
            return TaskCreationResult(
                created=False,
                error=f"Task creation failed: {error}",
            )

    async def _parse_intent(
        self, message: str, context: Optional[Dict[str, Any]]
    ) -> Any:
        """Parse task intent via orchestrator."""

        return await self._intent_orchestrator.parse_task_intent(message, context)

    @staticmethod
    def _build_clarification_result(intent_result: Any) -> TaskCreationResult:
        """Build result requesting user clarification."""

        question = (
            intent_result.questions[0]
            if intent_result.questions
            else "Please clarify the task details."
        )
        payload: Optional[Dict[str, Any]] = None
        if hasattr(intent_result, "dict"):
            try:
                payload = intent_result.dict()
            except Exception:  # pragma: no cover - defensive
                payload = None

        return TaskCreationResult(
            created=False,
            clarification=question,
            intent_payload=payload,
        )

    async def _create_task(self, user_id: int, intent_result: Any) -> TaskCreationResult:
        """Call MCP tool to create a task."""

        params = self._build_params(user_id, intent_result)
        mcp_result = await self._tool_client.call_tool("add_task", params)
        if mcp_result.get("status") == "error":
            return TaskCreationResult(created=False, error=mcp_result.get("error"))

        task_id = mcp_result.get("task_id")
        if not task_id:
            return TaskCreationResult(created=False, error="Task id missing in response")

        return TaskCreationResult(created=True, task_id=str(task_id))

    @staticmethod
    def _build_params(user_id: int, intent_result: Any) -> Dict[str, Any]:
        """Transform intent result into MCP parameters."""

        return {
            "user_id": user_id,
            "title": intent_result.title,
            "description": intent_result.description or "",
            "deadline": intent_result.deadline_iso,
            "priority": intent_result.priority,
            "tags": intent_result.tags or [],
        }
