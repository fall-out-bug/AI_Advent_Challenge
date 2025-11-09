"""Clarification question generation.

Extracted from IntentOrchestrator to follow Single Responsibility Principle.
Following the Zen of Python: Simple is better than complex.
"""

from typing import List

from src.domain.exceptions.intent_exceptions import ClarificationGenerationError


class IntentClarificationGenerator:
    """Generate clarifying questions for missing intent fields.

    Single responsibility: generate clarification questions.
    """

    def generate_questions(
        self, title: str, deadline_iso: str | None, priority: str
    ) -> List[str]:
        """Generate clarifying questions for missing fields.

        Args:
            title: Task title (may be empty)
            deadline_iso: ISO deadline or None
            priority: Priority level

        Returns:
            List of clarifying questions

        Raises:
            ClarificationGenerationError: If question generation fails
        """
        try:
            questions: List[str] = []
            if not deadline_iso:
                questions.append("What is the deadline (date and time)?")
            if priority not in {"low", "medium", "high"}:
                questions.append("What is the priority? [low, medium, high]")
            if not title:
                questions.append("What should I name the task?")
            return questions
        except Exception as e:
            raise ClarificationGenerationError(
                f"Failed to generate clarification questions: {e}", original_error=e
            ) from e
