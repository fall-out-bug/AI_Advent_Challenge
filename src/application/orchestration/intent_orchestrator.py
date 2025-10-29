"""Intent parsing orchestrator built on an LLM client."""

from __future__ import annotations

import json
from typing import List

from src.domain.entities.intent import ClarificationQuestion, IntentParseResult
from src.infrastructure.clients.llm_client import LLMClient, FallbackLLMClient


INTENT_SCHEMA_HINT = (
    "Return JSON with keys: title, description, deadline (ISO or null), priority (low|medium|high), "
    "tags (list[str]), needs_clarification (bool), questions (list[{text,key}])."
)


class IntentOrchestrator:
    """High-level interface for intent parsing and refinement.

    Args:
        llm: LLM client to call for parsing
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or FallbackLLMClient()

    async def parse_task_intent(self, text: str, context: dict) -> IntentParseResult:
        """Parse free-form text into an IntentParseResult."""

        prompt = (
            "You parse a task request. "
            + INTENT_SCHEMA_HINT
            + "\nInput: "
            + json.dumps({"text": text, "context": context})
        )
        raw = await self._llm.generate(prompt)
        data = self._safe_json(raw)
        return IntentParseResult(**data)

    async def refine_with_answers(self, original: IntentParseResult, answers: List[str]) -> IntentParseResult:
        """Apply user answers to the pending clarification questions in order."""

        updated = original.model_copy(deep=True)
        for idx, q in enumerate(original.questions):
            if idx >= len(answers):
                break
            answer = answers[idx]
            if q.key == "deadline":
                updated.deadline = answer
            elif q.key == "priority":
                updated.priority = answer
            elif q.key == "title":
                updated.title = answer
            elif q.key == "description":
                updated.description = answer
        # After applying provided answers, clear questions
        updated.needs_clarification = False
        updated.questions = []
        return updated

    @staticmethod
    def _safe_json(text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Minimal fallback
            return {
                "title": "Task",
                "description": "",
                "deadline": None,
                "priority": "medium",
                "tags": [],
                "needs_clarification": False,
                "questions": [],
            }


