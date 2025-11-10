"""Architecture review pass implementation."""

from __future__ import annotations

from typing import Mapping

from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import PassFindings
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass


class ArchitectureReviewPass(BaseReviewPass):
    """Evaluate project architecture composition and layout."""

    def __init__(
        self, config: ReviewConfig, review_logger: ReviewLoggerProtocol | None = None
    ) -> None:
        super().__init__("architecture", review_logger)
        self._config = config

    async def run(self, archive: Mapping[str, str]) -> PassFindings:
        """Analyse module distribution and emit architectural hints."""
        self._start_timer_if_needed()
        total_files = len(archive)
        findings = [
            {
                "type": "architecture_overview",
                "message": f"Detected {total_files} files for review.",
                "languages": list(self._config.language_checkers),
            }
        ]
        summary = f"Architecture summary: {total_files} files detected."
        metadata: dict[str, object] = {"files_scanned": total_files}
        return self._build_result(findings=findings, summary=summary, metadata=metadata)
