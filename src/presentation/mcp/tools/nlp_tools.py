"""MCP NLP tools for intent parsing."""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.presentation.mcp.server import mcp
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.infrastructure.clients.llm_client import get_llm_client, ResilientLLMClient

logger = logging.getLogger(__name__)


@mcp.tool()
async def parse_task_intent(text: str, user_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Parse free-form text into a structured task intent.

    Args:
        text: User-provided natural language request
        user_context: Optional additional context (timezone, locale, user prefs)

    Returns:
        Parsed intent as a dictionary
    """
    try:
        # Use resilient client that falls back on errors
        llm = ResilientLLMClient()
        orchestrator = IntentOrchestrator(llm=llm)
        result = await orchestrator.parse_task_intent(text, context=user_context or {})
        return result.model_dump()
    except Exception as e:
        logger.error(f"Failed to parse intent: {e}", exc_info=True)
        # Return minimal valid intent on failure
        return {
            "title": text[:100] if text else "Task",
            "description": "",
            "deadline": None,
            "priority": "medium",
            "tags": [],
            "needs_clarification": False,
            "questions": [],
        }


