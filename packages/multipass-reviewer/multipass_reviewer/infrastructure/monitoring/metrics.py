"""Prometheus metrics instruments for multipass reviewer."""

from __future__ import annotations

from typing import Iterable, Mapping

from prometheus_client import Counter, Histogram

CHECKER_FINDINGS = Counter(
    "multipass_checker_findings_total",
    "Total findings emitted by reviewer checkers",
    labelnames=("checker", "severity"),
)
CHECKER_RUNTIME = Histogram(
    "multipass_checker_runtime_seconds",
    "Execution time for reviewer checkers",
    labelnames=("checker",),
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)
PASS_RUNTIME = Histogram(
    "multipass_pass_runtime_seconds",
    "Execution time for review passes",
    labelnames=("pass_name",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 15.0),
)
LLM_TOKENS = Counter(
    "multipass_llm_tokens_total",
    "Total tokens spent on LLM calls",
    labelnames=("model", "direction"),
)
LLM_LATENCY = Histogram(
    "multipass_llm_latency_seconds",
    "LLM call latency",
    labelnames=("model",),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)


def observe_checker_runtime(checker: str, duration: float) -> None:
    """Record runtime for a checker."""

    CHECKER_RUNTIME.labels(checker=checker).observe(duration)


def observe_checker_findings(
    checker: str, findings: Iterable[Mapping[str, str]]
) -> None:
    """Record findings count by severity."""

    for finding in findings:
        severity = finding.get("severity", "unknown")
        CHECKER_FINDINGS.labels(checker=checker, severity=severity).inc()


def observe_pass_runtime(pass_name: str, duration: float) -> None:
    """Record runtime for a review pass."""

    PASS_RUNTIME.labels(pass_name=pass_name).observe(duration)


def record_llm_usage(
    model: str, prompt_tokens: int, response_tokens: int, latency: float
) -> None:
    """Record token usage and latency for LLM call."""

    LLM_TOKENS.labels(model=model, direction="prompt").inc(prompt_tokens)
    LLM_TOKENS.labels(model=model, direction="response").inc(response_tokens)
    LLM_LATENCY.labels(model=model).observe(latency)
