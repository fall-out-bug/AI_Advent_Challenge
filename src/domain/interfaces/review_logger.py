"""Protocol for review logging in the multi-pass reviewer domain.

Following Clean Architecture, the domain layer defines the behaviour that the
infrastructure must implement. Concrete implementations (JSON logger,
structured logger, etc.) live in the infrastructure layer and satisfy this
protocol via structural typing.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ReviewLoggerProtocol(Protocol):
    """Interface for structured review logging.

    Purpose:
        Provide a contract for logging the progress of the multi-pass review
        process without coupling domain logic to infrastructure details.
    """

    session_id: Optional[str]

    def log_work_step(
        self,
        step: str,
        data: Optional[Dict[str, object]] = None,
        status: str = "info",
    ) -> None:
        """Log an operational work step."""

    def log_review_pass(
        self,
        pass_name: str,
        event: str,
        data: Optional[Dict[str, object]] = None,
    ) -> None:
        """Log lifecycle events for a review pass."""

    def log_model_interaction(
        self,
        prompt: str,
        response: str,
        pass_name: str = "generic",
        model_name: str = "mistral",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tokens_used: Optional[Dict[str, int]] = None,
        execution_time_ms: Optional[float] = None,
        attempt: int = 1,
    ) -> None:
        """Log LLM interactions with contextual metadata."""

    def log_reasoning(
        self,
        reasoning: str,
        pass_name: str = "generic",
        context: Optional[str] = None,
    ) -> None:
        """Log model reasoning or analysis text."""

    def get_all_logs(self) -> Dict[str, object]:
        """Return all collected logs in structured form."""

    def get_model_responses(self) -> List[Dict[str, object]]:
        """Return recorded model interactions."""

    def get_reasoning_log(self) -> List[Dict[str, object]]:
        """Return recorded reasoning entries."""
