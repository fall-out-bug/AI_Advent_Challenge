"""Component deep dive pass implementation."""

from __future__ import annotations

from typing import List, Mapping

from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import PassFindings
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass


class ComponentDeepDivePass(BaseReviewPass):
    """Inspect individual modules for potential issues."""

    def __init__(
        self, config: ReviewConfig, review_logger: ReviewLoggerProtocol | None = None
    ) -> None:
        super().__init__("component", review_logger)
        self._config = config

    async def run(self, archive: Mapping[str, str]) -> PassFindings:
        """Collect component level metrics across files."""
        self._start_timer_if_needed()
        findings: List[dict[str, object]] = []
        for path, content in archive.items():
            complexity = content.count("def ") + content.count("class ")
            findings.append(
                {
                    "component": path,
                    "complexity": complexity,
                    "languages": list(self._config.language_checkers),
                }
            )
        metadata: dict[str, object] = {"files_scanned": len(archive)}
        summary = f"Component summary: analysed {len(archive)} modules."
        return self._build_result(findings=findings, summary=summary, metadata=metadata)
