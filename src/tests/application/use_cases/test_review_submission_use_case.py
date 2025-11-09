"""Unit tests for `ReviewSubmissionUseCase` helpers."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from src.application.use_cases.review_submission_use_case import (
    ReviewSubmissionUseCase,
    _ReviewTaskContext,
)
from src.domain.value_objects.long_summarization_task import LongTask, TaskType
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import Settings


class _DummyZipArchiveService(ZipArchiveService):
    def __init__(self) -> None:
        super().__init__(Settings())

    def extract_submission(self, *args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(code_files={"main.py": "print('ok')"})

    def extract_logs(self, *args: Any, **kwargs: Any) -> dict[str, str]:
        return {"logs/app.log": "INFO Hello"}


@dataclass
class _DummyUnifiedClient:
    calls: list[dict[str, Any]]

    async def make_request(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            response='{"tool": "submit_review_result", "arguments": {}}'
        )


@dataclass
class _DummyRepository:
    saved: list[dict[str, Any]]

    async def save_review_session(self, **payload: Any) -> None:
        self.saved.append(payload)


@dataclass
class _DummyTasksRepository:
    completed: list[tuple[str, str]]
    failed: list[tuple[str, str]]

    async def complete(self, task_id: str, session_id: str) -> None:
        self.completed.append((task_id, session_id))

    async def fail(self, task_id: str, error_text: str) -> None:
        self.failed.append((task_id, error_text))


class _DummyPublisher:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    async def publish_review(self, payload: dict[str, Any]) -> None:
        self.payloads.append(payload)


class _DummyRateLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def ensure_within_limits(self, student_id: str, assignment_id: str) -> None:
        self.calls.append((student_id, assignment_id))


class _DummyMCPClient:
    def __init__(self) -> None:
        self.tool_calls: list[tuple[str, dict[str, Any]]] = []
        self.discovery_calls = 0

    async def discover_tools(self) -> list[dict[str, Any]]:
        self.discovery_calls += 1
        return [{"name": "submit_review_result", "input_schema": {"type": "object"}}]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> None:
        self.tool_calls.append((name, arguments))


@pytest.fixture
def use_case(monkeypatch: pytest.MonkeyPatch) -> ReviewSubmissionUseCase:
    archive_service = _DummyZipArchiveService()
    unified_client = _DummyUnifiedClient([])
    review_repo = _DummyRepository([])
    tasks_repo = _DummyTasksRepository([], [])
    publisher = _DummyPublisher()
    mcp_client = _DummyMCPClient()

    monkeypatch.setattr(
        "src.application.use_cases.review_submission_use_case.ReviewRateLimiter",
        lambda *_args, **_kwargs: _DummyRateLimiter(),
    )

    case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=SimpleNamespace(),
        unified_client=unified_client,  # type: ignore[arg-type]
        review_repository=review_repo,  # type: ignore[arg-type]
        tasks_repository=tasks_repo,  # type: ignore[arg-type]
        publisher=publisher,  # type: ignore[arg-type]
        mcp_client=mcp_client,  # type: ignore[arg-type]
    )
    return case


def _sample_context(task_id: str = "task-1") -> LongTask:
    return LongTask(
        task_id=task_id,
        task_type=TaskType.CODE_REVIEW,
        user_id=7,
        metadata={
            "new_submission_path": "/tmp/new.zip",
            "previous_submission_path": None,
            "assignment_id": "hw1",
            "new_commit": "abc123",
        },
    )


def test_extract_task_context_success(use_case: ReviewSubmissionUseCase) -> None:
    task = _sample_context()
    context = use_case._extract_task_context(task)
    assert isinstance(context, _ReviewTaskContext)
    assert context.assignment_id == "hw1"
    assert context.repo_name == "7_hw1"


def test_extract_task_context_missing_fields(use_case: ReviewSubmissionUseCase) -> None:
    task = _sample_context()
    task.metadata.pop("new_submission_path", None)
    with pytest.raises(ValueError):
        use_case._extract_task_context(task)


def test_extract_overall_score_heuristics(use_case: ReviewSubmissionUseCase) -> None:
    report = SimpleNamespace(
        pass_1=SimpleNamespace(metadata={"overall_score": 91}),
        total_findings=0,
    )
    assert use_case._extract_overall_score(report) == 91

    report.pass_1.metadata.pop("overall_score")
    report.total_findings = 3
    assert use_case._extract_overall_score(report) == 80

    report.total_findings = "invalid"
    assert use_case._extract_overall_score(report) == 50


def test_parse_tool_call_response_variants(use_case: ReviewSubmissionUseCase) -> None:
    payload = use_case._parse_tool_call_response(
        '{"tool": "submit_review_result", "arguments": {"a": 1}}'
    )
    assert payload == {"a": 1}

    fallback = use_case._parse_tool_call_response(
        '{"student_id": "1", "submission_hash": "h", "review_content": "# R"}'
    )
    assert fallback is not None and fallback["student_id"] == "1"

    assert use_case._parse_tool_call_response("not json") is None


def test_enrich_tool_arguments(use_case: ReviewSubmissionUseCase) -> None:
    arguments: dict[str, Any] = {}
    use_case._enrich_tool_arguments(
        arguments,
        student_id="s1",
        submission_hash="hash",
        review_markdown="# Review",
        session_id="session-1",
        overall_score=75,
    )
    assert arguments["student_id"] == "s1"
    assert arguments["overall_score"] == 75


@pytest.mark.asyncio
async def test_publish_review_via_mcp_success(
    monkeypatch: pytest.MonkeyPatch,
    use_case: ReviewSubmissionUseCase,
) -> None:
    async def _fake_prepare_context(**_: Any) -> tuple[str, list[dict[str, Any]]]:
        return "prompt", [{"name": "submit_review_result", "input_schema": {}}]

    monkeypatch.setattr(
        use_case,
        "_prepare_mcp_publish_context",
        _fake_prepare_context,
    )

    async def _fake_request(**_: Any) -> SimpleNamespace:
        return SimpleNamespace(
            response=(
                '{"tool": "submit_review_result", "arguments": {"student_id": "s"}}'
            )
        )

    use_case.unified_client.calls.clear()
    use_case.unified_client.make_request = _fake_request  # type: ignore[assignment]

    published = await use_case._publish_review_via_mcp(
        student_id="s",
        assignment_id="hw1",
        submission_hash="hash",
        review_markdown="# review",
        session_id="session-1",
        overall_score=80,
        task_id="task-1",
    )

    assert published is True
    assert use_case.mcp_client.tool_calls  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_publish_review_via_mcp_fallback_when_no_arguments(
    monkeypatch: pytest.MonkeyPatch,
    use_case: ReviewSubmissionUseCase,
) -> None:
    async def _fake_prepare_context(**_: Any) -> tuple[str, list[dict[str, Any]]]:
        return "prompt", [{"name": "submit_review_result", "input_schema": {}}]

    monkeypatch.setattr(
        use_case,
        "_prepare_mcp_publish_context",
        _fake_prepare_context,
    )

    use_case.unified_client.make_request = (  # type: ignore[method-assign]
        lambda **_: SimpleNamespace(response="{}")
    )

    published = await use_case._publish_review_via_mcp(
        student_id="s",
        assignment_id="hw1",
        submission_hash="hash",
        review_markdown="# review",
        session_id="session-1",
        overall_score=None,
        task_id="task-1",
    )

    assert published is False
    # Fallback publisher receives payload via same object
    assert use_case.publisher.payloads  # type: ignore[attr-defined]


def test_set_log_analysis_status(use_case: ReviewSubmissionUseCase) -> None:
    report = SimpleNamespace()
    use_case._set_log_analysis_status(report, "skipped", "Disabled")
    assert report.pass_4_logs == {"status": "skipped", "reason": "Disabled"}


def test_handle_log_analysis_error(use_case: ReviewSubmissionUseCase) -> None:
    report = SimpleNamespace()
    use_case._handle_log_analysis_error(report, RuntimeError("boom"))
    assert report.pass_4_logs["status"] == "error"


@pytest.mark.asyncio
async def test_publish_via_fallback_handles_optional_score(use_case: ReviewSubmissionUseCase) -> None:
    await use_case._publish_via_fallback(
        assignment_id="hw1",
        student_id="s",
        submission_hash="hash",
        session_id="session-1",
        overall_score=77,
        task_id="task-1",
    )
    payloads = use_case.publisher.payloads  # type: ignore[attr-defined]
    assert payloads[0]["overall_score"] == 77

