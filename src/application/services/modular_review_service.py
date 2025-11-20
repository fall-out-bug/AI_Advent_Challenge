"""Service layer integration with the reusable multipass reviewer package."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, cast

from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.application.orchestrator import (
    MultiPassReviewerAgent as ModularReviewer,
)
from multipass_reviewer.domain.interfaces.archive_reader import ArchiveReader
from multipass_reviewer.domain.interfaces.llm_client import LLMClientProtocol
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import (
    MultiPassReport as PackageReview,
)
from multipass_reviewer.domain.models.review_models import (
    PassFindings as PackagePassFindings,
)

from src.domain.models.code_review_models import Finding as LegacyFinding
from src.domain.models.code_review_models import (
    MultiPassReport,
    PassFindings,
    SeverityLevel,
)
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging.review_logger import ReviewLogger
from src.infrastructure.monitoring.checker_metrics import observe_pass
from src.infrastructure.monitoring.review_metrics import review_pipeline_duration


class _ZipArchiveReaderAdapter(ArchiveReader):
    """Adapter exposing `ZipArchiveService` as a package ArchiveReader."""

    def __init__(self, archive_service: ZipArchiveService) -> None:
        self._archive_service = archive_service

    async def read_latest(
        self, archive_path: str, *_args: object, **_kwargs: object
    ) -> Mapping[str, str]:
        submission_id = Path(archive_path).stem
        archive = self._archive_service.extract_submission(
            archive_path,
            submission_id,
        )
        return archive.code_files


class _LLMClientAliasAdapter(LLMClientProtocol):
    """Rewrite package-specific model aliases to real model names."""

    def __init__(
        self,
        delegate: LLMClientProtocol,
        default_model: str,
    ) -> None:
        self._delegate = delegate
        self._default_model = self._normalize(default_model)

    async def make_request(
        self,
        model_name: str,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        actual_model = self._default_model if model_name == "summary" else model_name
        response = await self._delegate.make_request(
            actual_model,
            prompt,
            **kwargs,
        )
        return cast(str, response)

    @staticmethod
    def _normalize(model_name: str) -> str:
        candidate = model_name.lower()
        slug = re.sub(r"[^a-z0-9]+", " ", candidate)
        tokens = slug.split()
        aliases = (
            "mistral",
            "qwen",
            "tinyllama",
            "starcoder",
            "perplexity",
            "chadgpt",
        )
        for alias in aliases:
            if alias in tokens or alias in candidate:
                return alias
        return candidate.replace(" ", "")


class ModularReviewService:
    """Bridge infrastructure services with the reusable reviewer package."""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        archive_service: ZipArchiveService,
        diff_analyzer: DiffAnalyzer,
        llm_client: LLMClientProtocol,
        review_config: Optional[ReviewConfig] = None,
        review_logger: Optional[ReviewLoggerProtocol] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._archive_service = archive_service
        self._diff_analyzer = diff_analyzer
        self._settings = settings or get_settings()
        self._llm_client = _LLMClientAliasAdapter(
            llm_client,
            default_model=self._settings.llm_model,
        )
        self._review_logger = review_logger or ReviewLogger()
        self._config = review_config or ReviewConfig()

        archive_adapter = _ZipArchiveReaderAdapter(self._archive_service)
        self._reviewer = ModularReviewer(
            archive_reader=archive_adapter,
            llm_client=self._llm_client,
            logger=self._review_logger,
            config=self._config,
        )

    async def review_submission(
        self,
        new_archive_path: str,
        previous_archive_path: Optional[str],
        assignment_id: str,
        student_id: str,
    ) -> MultiPassReport:
        """Run modular multipass review for archives stored on disk."""

        start_time = time.perf_counter()
        try:
            package_report = await self._reviewer.review_from_archives(
                new_archive_path=new_archive_path,
                previous_archive_path=previous_archive_path,
                assignment_id=assignment_id,
                student_id=student_id,
            )
        finally:
            review_pipeline_duration.observe(time.perf_counter() - start_time)
        return self._convert_report(package_report)

    @staticmethod
    def _convert_report(package_report: PackageReview) -> MultiPassReport:
        def _convert_pass(
            pass_result: Optional[PackagePassFindings], name: str
        ) -> Optional[PassFindings]:
            if pass_result is None:
                return None
            metadata = dict(pass_result.metadata)
            metadata.setdefault("status", pass_result.status)
            if pass_result.error:
                metadata.setdefault("error_message", pass_result.error)

            findings: list[LegacyFinding] = []
            for entry in pass_result.findings:
                findings.append(
                    LegacyFinding(
                        severity=_parse_severity(entry.get("severity")),
                        title=(entry.get("title") or entry.get("message") or name),
                        description=entry.get("description")
                        or entry.get("message")
                        or "",
                        location=entry.get("location"),
                        recommendation=entry.get("recommendation"),
                    )
                )

            return PassFindings(
                pass_name=pass_result.pass_name,
                status=pass_result.status,
                error=pass_result.error,
                findings=findings,
                recommendations=list(pass_result.recommendations),
                summary=pass_result.summary,
                metadata=metadata,
            )

        def _parse_severity(value: Optional[str]) -> SeverityLevel:
            if not value:
                return SeverityLevel.MAJOR
            try:
                return SeverityLevel[value.upper()]
            except KeyError:
                try:
                    normalized = value.lower()
                    return SeverityLevel(normalized)  # type: ignore[arg-type]
                except Exception:
                    return SeverityLevel.MAJOR

        pass_1 = _convert_pass(package_report.pass_1, "pass_1")
        pass_2 = _convert_pass(package_report.pass_2, "pass_2")
        pass_3 = _convert_pass(package_report.pass_3, "pass_3")

        for converted_pass in (pass_1, pass_2, pass_3):
            if converted_pass is None:
                continue
            if converted_pass.status != "completed":
                ModularReviewService.logger.warning(
                    "modular_pass_failure",
                    extra={
                        "pass_name": converted_pass.pass_name,
                        "metadata": converted_pass.metadata,
                        "error": converted_pass.error,
                    },
                )
                continue
            observe_pass(converted_pass)
            ModularReviewService.logger.info(
                "modular_pass_summary",
                extra={
                    "pass_name": converted_pass.pass_name,
                    "finding_count": len(converted_pass.findings),
                    "metadata": converted_pass.metadata,
                },
            )

        pass_2_results: Dict[str, PassFindings] = {}
        if pass_2:
            pass_2_results[pass_2.pass_name or "pass_2"] = pass_2

        total_findings = sum(
            len(p.findings) for p in [p for p in [pass_1, pass_2, pass_3] if p]
        )

        haiku = None
        if pass_3 and "haiku" in pass_3.metadata:
            haiku = str(pass_3.metadata["haiku"])

        return MultiPassReport(
            session_id=package_report.session_id,
            repo_name=package_report.assignment_id,
            assignment_id=package_report.assignment_id,
            pass_1=pass_1,
            pass_2_results=pass_2_results,
            pass_3=pass_3,
            total_findings=total_findings,
            haiku=haiku,
            errors=list(package_report.errors),
        )
