"""Review logger protocol for multipass reviewer package."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class ReviewLoggerProtocol(Protocol):
    session_id: Optional[str]
    trace_id: Optional[str]

    def log_work_step(
        self, step: str, data: Dict[str, Any] | None = None, status: str = "info"
    ) -> None:
        ...

    def log_review_pass(
        self, pass_name: str, event: str, data: Dict[str, Any] | None = None
    ) -> None:
        ...

    def log_model_interaction(self, *args: Any, **kwargs: Any) -> None:
        ...

    def log_reasoning(
        self,
        reasoning: str,
        pass_name: str = "generic",
        context: str | None = None,
    ) -> None:
        ...

    def get_all_logs(self) -> Dict[str, Any]:
        ...

    def get_model_responses(self) -> List[Dict[str, Any]]:
        ...

    def get_reasoning_log(self) -> List[Dict[str, Any]]:
        ...
