"""Unit tests for `ModularReviewService` helpers and orchestration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from multipass_reviewer.domain.models.review_models import (
    MultiPassReport as PackageReport,
    PassFindings as PackagePassFindings,
)
from src.application.services.modular_review_service import (
    ModularReviewService,
    _LLMClientAliasAdapter,
    _ZipArchiveReaderAdapter,
)
from src.infrastructure.config.settings import Settings
from src.infrastructure.monitoring import checker_metrics, review_metrics
from src.infrastructure.archive.archive_service import ZipArchiveService


class _DummyZipArchiveService(ZipArchiveService):
    """Test double for `ZipArchiveService` that avoids filesystem access."""

    def __init__(self) -> None:
        super().__init__(Settings())
        self.extract_calls: list[tuple[str, str]] = []

    def extract_submission(self, archive_path: str, submission_id: str) -> Any:
        self.extract_calls.append((archive_path, submission_id))
        return SimpleNamespace(code_files={"main.py": "print('hi')"})

    def extract_logs(self, archive_path: str) -> Dict[str, str]:
        return {"logs/app.log": "INFO run"}


@pytest.mark.asyncio
async def test_review_submission_converts_package_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Review submission converts package report and records metrics."""

    archive_service = _DummyZipArchiveService()
    diff_analyzer = SimpleNamespace()

    class _StubLLMClient:
        async def make_request(self, model_name: str, prompt: str, **kwargs: Any) -> str:
            return "ok"

    service = ModularReviewService(
        archive_service=archive_service,
        diff_analyzer=diff_analyzer,  # type: ignore[arg-type]
        llm_client=_StubLLMClient(),  # type: ignore[arg-type]
    )

    recorded_passes: list[Any] = []
    recorded_durations: list[float] = []

    review_calls: list[dict[str, Any]] = []

    async def _fake_review_from_archives(**kwargs: Any) -> PackageReport:
        review_calls.append(kwargs)
        pass_payload = PackagePassFindings(
            pass_name="pass_1",
            status="completed",
            findings=[{"severity": "minor", "title": "Title", "description": "Desc"}],
            recommendations=["Read docs"],
            summary="summary",
            metadata={"overall_score": 88},
        )
        pass_three = PackagePassFindings(
            pass_name="pass_3",
            status="completed",
            findings=[],
            metadata={"haiku": "haiku text"},
        )
        return PackageReport(
            session_id="session-1",
            assignment_id="assignment-1",
            pass_1=pass_payload,
            pass_2=None,
            pass_3=pass_three,
            errors=[],
        )

    monkeypatch.setattr(
        service,
        "_reviewer",
        SimpleNamespace(review_from_archives=_fake_review_from_archives),
    )
    monkeypatch.setattr(
        "src.application.services.modular_review_service.observe_pass",
        lambda pass_result: recorded_passes.append(pass_result),
    )
    monkeypatch.setattr(
        "src.application.services.modular_review_service.review_pipeline_duration",
        SimpleNamespace(observe=recorded_durations.append),
    )

    result = await service.review_submission(
        new_archive_path="/tmp/new.zip",
        previous_archive_path=None,
        assignment_id="assignment-1",
        student_id="student-1",
    )

    assert result.session_id == "session-1"
    assert result.total_findings == 1
    assert recorded_passes and recorded_passes[0].pass_name == "pass_1"
    assert review_calls[0]["new_archive_path"] == "/tmp/new.zip"
    assert review_calls[0]["student_id"] == "student-1"
    assert recorded_durations  # metric observed
    assert result.haiku == "haiku text"


@pytest.mark.asyncio
async def test_zip_archive_adapter_reads_submission() -> None:
    """Adapter delegates to archive service."""
    archive_service = _DummyZipArchiveService()
    adapter = _ZipArchiveReaderAdapter(archive_service)
    files = await adapter.read_latest("/tmp/review.zip")
    assert "main.py" in files
    assert archive_service.extract_calls == [("/tmp/review.zip", "review")]


@dataclass
class _FakeDelegate:
    responses: list[tuple[str, str]]

    def __init__(self) -> None:
        self.responses = []

    async def make_request(self, model_name: str, prompt: str, **kwargs: Any) -> str:
        self.responses.append((model_name, prompt))
        return prompt


@pytest.mark.asyncio
async def test_llm_client_alias_adapter_rewrites_summary_model() -> None:
    """Alias adapter normalizes summary model and preserves custom names."""
    delegate = _FakeDelegate()
    adapter = _LLMClientAliasAdapter(delegate, default_model="Qwen-Turbo")
    await adapter.make_request("summary", "prompt")
    await adapter.make_request("custom-model", "prompt")
    assert delegate.responses[0][0] == "qwen"
    assert delegate.responses[1][0] == "custom-model"


def test_llm_client_alias_normalizes_known_alias() -> None:
    """Alias normalization collapses multi-word names."""
    assert _LLMClientAliasAdapter._normalize("StarCoder 16B") == "starcoder"
    assert _LLMClientAliasAdapter._normalize("Mistral-7B") == "mistral"
