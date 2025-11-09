"""Base class for review passes within the modular package."""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional

from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import PassFindings
from multipass_reviewer.infrastructure.monitoring import metrics


class BaseReviewPass:
    """Common helpers shared across reviewer passes."""

    def __init__(
        self, name: str, review_logger: ReviewLoggerProtocol | None = None
    ) -> None:
        """Store pass name and optional logger."""
        self.name = name
        self.review_logger = review_logger
        self._timer_start: float | None = None

    async def run(self, archive: Mapping[str, str]) -> PassFindings:
        """Execute the pass and return structured findings."""
        raise NotImplementedError

    def _build_result(
        self,
        findings: Optional[list[dict[str, Any]]] = None,
        recommendations: Optional[list[str]] = None,
        summary: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        status: str = "completed",
        error: Optional[str] = None,
    ) -> PassFindings:
        """Create PassFindings and emit logger event when configured."""
        self._start_timer_if_needed()
        metadata_dict: dict[str, Any] = dict(metadata or {})
        metadata_dict.setdefault("status", status)
        if error:
            metadata_dict.setdefault("error_message", error)
        result = PassFindings(
            pass_name=self.name,
            status=status,
            error=error,
            findings=findings or [],
            recommendations=recommendations or [],
            summary=summary,
            metadata=metadata_dict,
        )
        if self.review_logger:
            self.review_logger.log_review_pass(self.name, "completed", result.metadata)
        duration = self._observe_runtime()
        if duration is not None:
            result.metadata.setdefault("duration_seconds", duration)
        metrics.observe_checker_findings(self.name, result.findings)
        return result

    def build_failure_result(self, error: Exception) -> PassFindings:
        """Create pass result describing failure."""
        message = str(error)
        self._start_timer_if_needed()
        metadata: dict[str, object] = {"status": "error", "error_message": message}
        if self.review_logger:
            self.review_logger.log_review_pass(self.name, "error", metadata)
        duration = self._observe_runtime()
        if duration is not None:
            metadata["duration_seconds"] = duration
        return PassFindings(
            pass_name=self.name,
            status="failed",
            error=message,
            findings=[],
            recommendations=[],
            summary=None,
            metadata=metadata,
        )

    def _start_timer_if_needed(self) -> None:
        """Start timer for pass execution if not already started."""
        if self._timer_start is None:
            self._timer_start = time.perf_counter()

    def _observe_runtime(self) -> float | None:
        """Record runtime metric and reset timer."""
        if self._timer_start is None:
            return None
        duration = time.perf_counter() - self._timer_start
        metrics.observe_pass_runtime(self.name, duration)
        self._timer_start = None
        return duration
