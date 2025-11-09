"""Synthesis pass for aggregating review insights."""

from __future__ import annotations

from typing import Mapping

from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import PassFindings
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass


class SynthesisPass(BaseReviewPass):
    """Create final summary and optional haiku."""

    def __init__(
        self, config: ReviewConfig, review_logger: ReviewLoggerProtocol | None = None
    ) -> None:
        super().__init__("synthesis", review_logger)
        self._config = config

    async def run(self, archive: Mapping[str, str]) -> PassFindings:
        """Generate synthesis summary and creative extras."""
        self._start_timer_if_needed()
        summary = f"Synthesis summary: reviewed {len(archive)} files."
        metadata: dict[str, object] = {"token_budget": self._config.token_budget}
        if self._config.enable_haiku:
            metadata["haiku"] = (
                "Code flows like rivers / Reviewers weave clear guidance / "
                "Quality takes root"
            )
        return self._build_result(summary=summary, metadata=metadata)
