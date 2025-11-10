"""Intent validation logic.

Extracted from IntentOrchestrator to follow Single Responsibility Principle.
Following the Zen of Python: Explicit is better than implicit.
"""

from typing import List, Tuple

from src.domain.entities.intent import IntentParseResult
from src.domain.exceptions.intent_exceptions import IntentValidationError


class IntentValidator:
    """Validates intent completeness and correctness.

    Single responsibility: validate intent parse results.
    """

    def validate_completeness(
        self, result: IntentParseResult
    ) -> Tuple[bool, List[str]]:
        """Validate intent completeness.

        Args:
            result: Intent parse result

        Returns:
            Tuple of (is_complete, missing_fields)

        Raises:
            IntentValidationError: If validation fails unexpectedly
        """
        try:
            missing: List[str] = []
            if not result.title:
                missing.append("title")
            if result.deadline_iso is None:
                missing.append("deadline")
            if result.priority not in {"low", "medium", "high"}:
                missing.append("priority")
            return (len(missing) == 0, missing)
        except Exception as e:
            raise IntentValidationError(
                f"Validation failed: {e}", original_error=e
            ) from e

    def is_valid_priority(self, priority: str) -> bool:
        """Check if priority is valid.

        Args:
            priority: Priority level string

        Returns:
            True if valid, False otherwise
        """
        return priority in {"low", "medium", "high"}

    def has_required_fields(self, result: IntentParseResult) -> bool:
        """Check if result has all required fields.

        Args:
            result: Intent parse result

        Returns:
            True if all required fields present
        """
        return (
            bool(result.title)
            and result.deadline_iso is not None
            and self.is_valid_priority(result.priority)
        )
