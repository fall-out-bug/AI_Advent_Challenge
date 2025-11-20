"""Negative tests for ModularReviewService error handling and security."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from multipass_reviewer.domain.models.review_models import (
    MultiPassReport as PackageReport,
)
from multipass_reviewer.domain.models.review_models import (
    PassFindings as PackagePassFindings,
)

from src.application.services.modular_review_service import ModularReviewService
from src.domain.models.code_review_models import MultiPassReport
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import get_settings


class _ExplodingArchiveService:
    """Archive service stub that always raises to simulate malicious input."""

    def extract_submission(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ValueError("dangerous archive")


class _DummyLLMClient:
    async def make_request(self, *_args: Any, **_kwargs: Any) -> str:
        return "{}"


@pytest.mark.asyncio
async def test_review_submission_propagates_archive_errors() -> None:
    """Service must fail fast when archive extraction flags security issues."""

    service = ModularReviewService(
        archive_service=_ExplodingArchiveService(),
        diff_analyzer=DiffAnalyzer(),
        llm_client=_DummyLLMClient(),
        settings=get_settings(),
    )

    with pytest.raises(ValueError, match="dangerous archive"):
        await service.review_submission(
            new_archive_path="/tmp/suspicious.zip",
            previous_archive_path=None,
            assignment_id="HW_SECURITY",
            student_id="attacker",
        )


@pytest.mark.asyncio
async def test_review_submission_preserves_package_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Package-level errors must surface in the converted domain report."""

    service = ModularReviewService(
        archive_service=ZipArchiveService(get_settings()),
        diff_analyzer=DiffAnalyzer(),
        llm_client=_DummyLLMClient(),
        settings=get_settings(),
    )

    async def fake_review_from_archives(*_args: Any, **_kwargs: Any) -> PackageReport:
        return PackageReport(
            session_id="session-x",
            assignment_id="HW_FAIL",
            pass_1=PackagePassFindings(
                pass_name="architecture", status="failed", error="boom"
            ),
            errors=[{"pass": "architecture", "error": "boom"}],
        )

    observed_passes: list[Any] = []
    monkeypatch.setattr(
        "src.application.services.modular_review_service.observe_pass",
        lambda pf: observed_passes.append(pf),
    )

    service._reviewer.review_from_archives = fake_review_from_archives  # type: ignore[attr-defined]

    report = await service.review_submission(
        new_archive_path=str(tmp_path / "ignored.zip"),
        previous_archive_path=None,
        assignment_id="HW_FAIL",
        student_id="student",
    )

    assert isinstance(report, MultiPassReport)
    assert report.errors == [{"pass": "architecture", "error": "boom"}]
    assert report.pass_1 is not None and report.pass_1.status == "failed"
    assert observed_passes == []
