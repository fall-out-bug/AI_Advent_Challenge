"""Multi-pass reviewer orchestrator for the reusable package."""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple

from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.domain.interfaces.archive_reader import ArchiveReader
from multipass_reviewer.domain.interfaces.llm_client import LLMClientProtocol
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import MultiPassReport, PassFindings
from multipass_reviewer.domain.passes.architecture_pass import ArchitectureReviewPass
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass
from multipass_reviewer.domain.passes.component_pass import ComponentDeepDivePass
from multipass_reviewer.domain.passes.synthesis_pass import SynthesisPass
from multipass_reviewer.infrastructure.monitoring import metrics

logger = logging.getLogger(__name__)


def create_passes(
    config: ReviewConfig,
    logger: Optional[ReviewLoggerProtocol],
) -> Tuple[ArchitectureReviewPass, ComponentDeepDivePass, SynthesisPass]:
    """Factory for default pass implementations."""
    architecture = ArchitectureReviewPass(config=config, review_logger=logger)
    component = ComponentDeepDivePass(config=config, review_logger=logger)
    synthesis = SynthesisPass(config=config, review_logger=logger)
    return architecture, component, synthesis


class MultiPassReviewerAgent:
    """Application-layer orchestrator coordinating review passes."""

    def __init__(
        self,
        archive_reader: ArchiveReader,
        llm_client: LLMClientProtocol,
        logger: Optional[ReviewLoggerProtocol] = None,
        config: Optional[ReviewConfig] = None,
    ) -> None:
        self._archive_reader = archive_reader
        self._llm_client = llm_client
        self._logger = logger
        self._config = config or ReviewConfig()
        (
            self._architecture_pass,
            self._component_pass,
            self._synthesis_pass,
        ) = create_passes(self._config, logger)

    async def review_from_archives(
        self,
        new_archive_path: str,
        previous_archive_path: Optional[str],
        assignment_id: str,
        student_id: str,
    ) -> MultiPassReport:
        if self._logger:
            self._logger.log_work_step(
                "start_review",
                {
                    "new_archive": new_archive_path,
                    "previous_archive": previous_archive_path,
                },
            )

        errors: list[dict[str, str]] = []

        archive = await self._archive_reader.read_latest(new_archive_path)
        pass_1 = await self._run_pass_with_recovery(
            self._architecture_pass, archive, errors
        )
        pass_2 = await self._run_pass_with_recovery(
            self._component_pass, archive, errors
        )
        pass_3 = await self._run_pass_with_recovery(
            self._synthesis_pass, archive, errors
        )

        prompt = (
            "Generate review summary for assignment '{assignment}' "
            "with token budget {budget}."
        ).format(assignment=assignment_id, budget=self._config.token_budget)
        llm_start = time.perf_counter()
        try:
            response = await self._llm_client.make_request(
                model_name="summary", prompt=prompt
            )
            duration = time.perf_counter() - llm_start
            metrics.record_llm_usage(
                model="summary",
                prompt_tokens=getattr(response, "input_tokens", 0),
                response_tokens=getattr(response, "response_tokens", 0),
                latency=duration,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            errors.append({"stage": "summary_llm", "error": str(exc)})
            logger.warning("Failed to generate summary: %s", exc, exc_info=True)
            if self._logger:
                self._logger.log_work_step(
                    "summary_generation",
                    {"error": str(exc)},
                    status="error",
                )

        report = MultiPassReport(
            session_id=f"session_{student_id}",
            assignment_id=assignment_id,
            pass_1=pass_1,
            pass_2=pass_2,
            pass_3=pass_3,
            errors=errors,
        )

        if self._logger:
            self._logger.log_work_step(
                "complete_review", {"session_id": report.session_id}
            )

        return report

    async def _run_pass_with_recovery(
        self,
        review_pass: BaseReviewPass,
        archive: dict[str, str],
        errors: list[dict[str, str]],
    ) -> PassFindings:
        """Execute pass and capture exceptions as partial results."""
        review_pass._start_timer_if_needed()
        if self._logger:
            self._logger.log_review_pass(review_pass.name, "started", {})
        try:
            return await review_pass.run(archive)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Review pass %s failed: %s", review_pass.name, exc, exc_info=True
            )
            failure = review_pass.build_failure_result(exc)
            errors.append(
                {
                    "pass": review_pass.name,
                    "error": failure.error or str(exc),
                }
            )
            return failure
