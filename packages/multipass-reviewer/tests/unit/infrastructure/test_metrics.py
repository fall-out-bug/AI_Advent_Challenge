"""Tests for Prometheus metrics utilities."""

from __future__ import annotations

from multipass_reviewer.infrastructure.monitoring import metrics


def test_observe_checker_findings_increments_counter() -> None:
    warning_before = metrics.CHECKER_FINDINGS.labels(
        checker="lint", severity="warning"
    )._value.get()
    unknown_before = metrics.CHECKER_FINDINGS.labels(
        checker="lint", severity="unknown"
    )._value.get()
    metrics.observe_checker_findings("lint", [{"severity": "warning"}, {}])
    assert (
        metrics.CHECKER_FINDINGS.labels(checker="lint", severity="warning")._value.get()
        == warning_before + 1
    )
    assert (
        metrics.CHECKER_FINDINGS.labels(checker="lint", severity="unknown")._value.get()
        == unknown_before + 1
    )


def test_record_llm_usage_updates_counters() -> None:
    prompt_before = metrics.LLM_TOKENS.labels(
        model="summary", direction="prompt"
    )._value.get()
    response_before = metrics.LLM_TOKENS.labels(
        model="summary", direction="response"
    )._value.get()
    metrics.record_llm_usage(
        model="summary", prompt_tokens=10, response_tokens=5, latency=0.5
    )
    assert (
        metrics.LLM_TOKENS.labels(model="summary", direction="prompt")._value.get()
        == prompt_before + 10
    )
    assert (
        metrics.LLM_TOKENS.labels(model="summary", direction="response")._value.get()
        == response_before + 5
    )


def test_observe_checker_runtime_records_histogram() -> None:
    metrics.observe_checker_runtime("lint", 0.1)
    sample = metrics.CHECKER_RUNTIME.labels(checker="lint")._sum.get()
    assert sample >= 0.1


def test_observe_pass_runtime_records_histogram() -> None:
    metrics.observe_pass_runtime("pass", 0.2)
    sample = metrics.PASS_RUNTIME.labels(pass_name="pass")._sum.get()
    assert sample >= 0.2
