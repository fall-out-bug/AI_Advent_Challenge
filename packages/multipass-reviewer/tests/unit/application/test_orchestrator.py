"""Unit tests for the MultiPassReviewer orchestrator."""

from __future__ import annotations

from typing import List

import pytest
from multipass_reviewer.application.config import ReviewConfig
from multipass_reviewer.application.orchestrator import MultiPassReviewerAgent
from multipass_reviewer.domain.interfaces.review_logger import ReviewLoggerProtocol
from multipass_reviewer.domain.models.review_models import MultiPassReport, PassFindings
from multipass_reviewer.domain.passes.base_pass import BaseReviewPass


class FakeArchiveReader:
    async def read_latest(self, *_args: object, **_kwargs: object) -> dict[str, str]:
        return {"main.py": "print('hello')"}


class FakeLLMClient:
    def __init__(self) -> None:
        self.requests: List[str] = []

    async def make_request(
        self, model_name: str, prompt: str, **_kwargs: object
    ) -> str:
        self.requests.append(f"{model_name}:{len(prompt)}")
        return "summary"


class FakeLogger(ReviewLoggerProtocol):
    def __init__(self) -> None:
        self.entries: List[tuple[str, str]] = []

    session_id: str | None = None
    trace_id: str | None = "trace-test"

    def log_work_step(
        self, step: str, data: object | None = None, status: str = "info"
    ) -> None:
        self.entries.append((step, status))

    def log_review_pass(
        self, pass_name: str, event: str, data: object | None = None
    ) -> None:
        self.entries.append((pass_name, event))

    def log_model_interaction(self, *args: object, **kwargs: object) -> None:
        self.entries.append(("model", "interaction"))

    def log_reasoning(
        self,
        reasoning: str,
        pass_name: str = "generic",
        context: object | None = None,
    ) -> None:
        self.entries.append((pass_name, "reasoning"))

    def get_all_logs(self) -> dict[str, object]:
        return {"entries": list(self.entries)}

    def get_model_responses(self) -> List[dict]:
        return []

    def get_reasoning_log(self) -> List[dict]:
        return []


class FakeSuccessPass(BaseReviewPass):
    def __init__(self, name: str, review_logger: ReviewLoggerProtocol | None) -> None:
        super().__init__(name, review_logger)

    async def run(self, archive: dict[str, str]) -> PassFindings:
        self._start_timer_if_needed()
        return self._build_result(
            findings=[{"severity": "major", "message": f"{self.name} finding"}],
            summary=f"summary for {self.name}",
        )


class FakeFailingPass(BaseReviewPass):
    def __init__(self, name: str, review_logger: ReviewLoggerProtocol | None) -> None:
        super().__init__(name, review_logger)

    async def run(self, archive: dict[str, str]) -> PassFindings:
        self._start_timer_if_needed()
        raise RuntimeError("simulated failure")


@pytest.mark.asyncio
async def test_orchestrator_runs_passes_in_sequence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orchestrator should execute configured passes using injected dependencies."""
    config = ReviewConfig(language_checkers=["python"], enable_haiku=True)

    def fake_factory(_config: ReviewConfig, review_logger: FakeLogger):
        return (
            FakeSuccessPass("architecture", review_logger),
            FakeSuccessPass("component", review_logger),
            FakeSuccessPass("synthesis", review_logger),
        )

    monkeypatch.setattr(
        "multipass_reviewer.application.orchestrator.create_passes",
        fake_factory,
    )

    orchestrator = MultiPassReviewerAgent(
        archive_reader=FakeArchiveReader(),
        llm_client=FakeLLMClient(),
        logger=FakeLogger(),
        config=config,
    )

    report = await orchestrator.review_from_archives(
        new_archive_path="/tmp/new.zip",
        previous_archive_path=None,
        assignment_id="hw",
        student_id="123",
    )

    assert isinstance(report, MultiPassReport)
    assert report.pass_1 and report.pass_1.status == "completed"
    assert report.pass_2 and report.pass_2.status == "completed"
    assert report.pass_3 and report.pass_3.status == "completed"
    assert not report.errors


@pytest.mark.asyncio
async def test_orchestrator_handles_pass_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Failing passes should produce partial results and error entries."""
    config = ReviewConfig(language_checkers=["python"])

    def fake_factory(_config: ReviewConfig, review_logger: FakeLogger):
        return (
            FakeSuccessPass("architecture", review_logger),
            FakeFailingPass("component", review_logger),
            FakeSuccessPass("synthesis", review_logger),
        )

    monkeypatch.setattr(
        "multipass_reviewer.application.orchestrator.create_passes",
        fake_factory,
    )

    orchestrator = MultiPassReviewerAgent(
        archive_reader=FakeArchiveReader(),
        llm_client=FakeLLMClient(),
        logger=FakeLogger(),
        config=config,
    )

    report = await orchestrator.review_from_archives(
        new_archive_path="/tmp/new.zip",
        previous_archive_path=None,
        assignment_id="hw",
        student_id="123",
    )

    assert report.pass_1 and report.pass_1.status == "completed"
    assert report.pass_2 and report.pass_2.status == "failed"
    assert report.pass_2.error == "simulated failure"
    assert report.errors and report.errors[0]["pass"] == "component"


@pytest.mark.asyncio
async def test_orchestrator_handles_llm_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = ReviewConfig(language_checkers=["python"])

    def fake_factory(_config: ReviewConfig, review_logger: FakeLogger):
        return (
            FakeSuccessPass("architecture", review_logger),
            FakeSuccessPass("component", review_logger),
            FakeSuccessPass("synthesis", review_logger),
        )

    class FailingLLM(FakeLLMClient):
        async def make_request(
            self, model_name: str, prompt: str, **kwargs: object
        ) -> str:
            raise RuntimeError("llm offline")

    monkeypatch.setattr(
        "multipass_reviewer.application.orchestrator.create_passes",
        fake_factory,
    )

    orchestrator = MultiPassReviewerAgent(
        archive_reader=FakeArchiveReader(),
        llm_client=FailingLLM(),
        logger=FakeLogger(),
        config=config,
    )

    report = await orchestrator.review_from_archives(
        new_archive_path="/tmp/new.zip",
        previous_archive_path=None,
        assignment_id="hw",
        student_id="123",
    )

    assert report.errors and report.errors[0]["stage"] == "summary_llm"
    assert all(pass_result.status == "completed" for pass_result in report.passes)
