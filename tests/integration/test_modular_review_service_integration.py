"""Integration tests for modular multipass reviewer package within AI_Challenge."""

from __future__ import annotations

import zipfile
import re
from pathlib import Path
from typing import Any
def _normalise_model_name(model_name: str) -> str:
    candidate = model_name.lower()
    slug = re.sub(r"[^a-z0-9]+", " ", candidate)
    tokens = slug.split()
    for alias in ("mistral", "qwen", "tinyllama", "starcoder", "perplexity", "chadgpt"):
        if alias in tokens or alias in candidate:
            return alias
    return candidate.replace(" ", "")


import pytest
from multipass_reviewer.application.config import ReviewConfig, ReviewConfigBuilder
from shared_package.clients.unified_client import UnifiedModelClient

from src.application.services.modular_review_service import ModularReviewService
from src.domain.models.code_review_models import MultiPassReport
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import get_settings


class DummyLLMClient:
    """Lightweight stand-in for the shared UnifiedModelClient."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def make_request(self, model_name: str, prompt: str, **_: Any) -> str:
        self.prompts.append(f"{model_name}:{len(prompt)}")
        # Return minimal JSON compatible payload expected by package tests
        return '{"findings": [], "recommendations": []}'


def _create_zip(tmp_path: Path, filename: str, files: dict[str, str]) -> Path:
    archive_path = tmp_path / filename
    with zipfile.ZipFile(archive_path, "w") as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)
    return archive_path


@pytest.mark.asyncio
async def test_modular_service_reviews_python_archive(tmp_path: Path) -> None:
    """Modular review service should produce a multipass report for Python archives."""

    settings = get_settings()
    archive_service = ZipArchiveService(settings)
    diff_analyzer = DiffAnalyzer()
    llm_client = DummyLLMClient()

    review_config: ReviewConfig = (
        ReviewConfigBuilder()
        .with_language("python")
        .with_static_analysis(["linter", "type_checker"])
        .enable_haiku()
        .build()
    )

    service = ModularReviewService(
        archive_service=archive_service,
        diff_analyzer=diff_analyzer,
        llm_client=llm_client,
        review_config=review_config,
    )

    new_archive = _create_zip(
        tmp_path,
        "new_submission.zip",
        {"main.py": "def greet(name: str) -> str:\n    return f'Hello {name}'\n"},
    )

    report = await service.review_submission(
        new_archive_path=str(new_archive),
        previous_archive_path=None,
        assignment_id="HW_MODULAR",
        student_id="student-42",
    )

    assert isinstance(report, MultiPassReport)
    assert report.assignment_id == "HW_MODULAR"
    assert report.session_id.startswith("session_")
    assert report.pass_1 is not None
    assert llm_client.prompts  # Ensure LLM client was invoked
    assert isinstance(report.pass_2_results, dict)


@pytest.mark.asyncio
async def test_modular_service_handles_custom_config(tmp_path: Path) -> None:
    """Service should accept externally provided ReviewConfig objects."""

    service = ModularReviewService(
        archive_service=ZipArchiveService(get_settings()),
        diff_analyzer=DiffAnalyzer(),
        llm_client=DummyLLMClient(),
        review_config=ReviewConfig(enable_haiku=False, token_budget=5000),
    )

    archive = _create_zip(
        tmp_path,
        "sample.zip",
        {"utils/helpers.py": "def helper() -> None:\n    pass\n"},
    )

    report = await service.review_submission(
        new_archive_path=str(archive),
        previous_archive_path=None,
        assignment_id="HW_CONFIG",
        student_id="student-1",
    )

    assert report.assignment_id == "HW_CONFIG"
    assert report.pass_1 is not None
    assert isinstance(report.pass_2_results, dict)
    assert report.pass_3 is not None


@pytest.mark.asyncio
async def test_modular_service_with_real_llm(tmp_path: Path) -> None:
    """Run modular review against the real LLM if it is configured."""

    settings = get_settings()
    model_name = getattr(settings, "llm_model", None)
    if not model_name:
        pytest.skip("LLM model not configured")

    timeout = getattr(settings, "review_llm_timeout", 30.0)
    async with UnifiedModelClient(timeout=timeout) as client:  # type: ignore[attr-defined]
        try:
            model_alias = _normalise_model_name(model_name)
            await client.make_request(model_alias, "Health check ping", max_tokens=16)
        except Exception as exc:  # pragma: no cover - depends on external infra
            pytest.skip(f"Real LLM unavailable: {exc}")

        archive_service = ZipArchiveService(settings)
        diff_analyzer = DiffAnalyzer()

        review_config = (
            ReviewConfigBuilder()
            .with_language("python")
            .with_static_analysis(["linter"])
            .enable_haiku()
            .build()
        )

        service = ModularReviewService(
            archive_service=archive_service,
            diff_analyzer=diff_analyzer,
            llm_client=client,
            review_config=review_config,
            settings=settings,
        )

        new_archive = _create_zip(
            tmp_path,
            "real_llm_submission.zip",
            {
                "app/main.py": (
                    "def add(a: int, b: int) -> int:\n"
                    "    return a + b\n\n"
                    "if __name__ == '__main__':\n"
                    "    print(add(1, 2))\n"
                )
            },
        )

        report = await service.review_submission(
            new_archive_path=str(new_archive),
            previous_archive_path=None,
            assignment_id="HW_REAL_LLM",
            student_id="student-99",
        )

        assert isinstance(report, MultiPassReport)
        assert report.assignment_id == "HW_REAL_LLM"
        assert report.pass_3 is not None
        assert report.pass_3.status == "completed"
        assert not report.errors
