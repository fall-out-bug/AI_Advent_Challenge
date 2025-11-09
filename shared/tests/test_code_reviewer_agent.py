"""Tests for shared `CodeReviewerAgent`."""

from __future__ import annotations

import pytest

from shared.shared_package.agents.code_reviewer import CodeReviewerAgent
from shared.shared_package.agents.schemas import AgentRequest, TaskMetadata
from shared.shared_package.clients.base_client import ModelResponse


class _DummyClient:
    async def make_request(self, **_: str) -> ModelResponse:
        return ModelResponse(
            response="Issue: consider adding tests. Suggestion: add docstrings.",
            response_tokens=10,
            input_tokens=5,
            total_tokens=15,
            model_name="gpt-4",
            response_time=0.12,
        )


def _request() -> AgentRequest:
    return AgentRequest(
        task="def add(a, b):\n    return a + b",
        metadata=TaskMetadata(
            task_id="task-1",
            task_type="code_review",
            timestamp=123.0,
            model_name="gpt-4",
        ),
    )


@pytest.mark.asyncio
async def test_process_impl_returns_quality_metrics() -> None:
    agent = CodeReviewerAgent(client=_DummyClient())
    response = await agent._process_impl(_request())
    assert response.success is True
    assert response.quality is not None
    assert response.quality.issues_found >= 1
    assert response.metadata is not None
    assert response.metadata.task_type == "code_review"


def test_quality_analysis_scores_are_bounded() -> None:
    agent = CodeReviewerAgent(client=_DummyClient())
    metrics = agent._analyze_quality(
        "print('hello world')\n# comment line\nfor i in range(len(items)): pass",
        "Issue: something warning suggestion",
    )
    assert 0.0 <= metrics.readability <= 1.0
    assert 0.0 <= metrics.efficiency <= 1.0
    assert 0.0 <= metrics.correctness <= 1.0
    assert 0.0 <= metrics.maintainability <= 1.0
    assert 0.0 <= metrics.score <= 1.0


def test_count_issues_caps_at_twenty() -> None:
    agent = CodeReviewerAgent(client=_DummyClient())
    text = "issue " * 100
    assert agent._count_issues(text) == 20


def test_parameter_setters_update_state(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    agent = CodeReviewerAgent(client=_DummyClient())
    agent.set_model("qwen")
    agent.set_parameters(max_tokens=500, temperature=0.1)
    assert agent.model_name == "qwen"
    assert agent.max_tokens == 500
    assert agent.temperature == 0.1
    assert any("parameters updated" in message for message in caplog.text.splitlines())

