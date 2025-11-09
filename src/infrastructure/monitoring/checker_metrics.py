"""Prometheus metrics helpers for modular review checkers."""

from __future__ import annotations

from typing import Any

from prometheus_client import Counter, Histogram

from src.domain.models.code_review_models import PassFindings, SeverityLevel

checker_findings_total = Counter(
    "review_checker_findings_total",
    "Total findings produced by modular review passes",
    ["checker", "severity"],
)

checker_runtime_seconds = Histogram(
    "review_checker_runtime_seconds",
    "Execution duration recorded for modular review passes",
    ["checker"],
    buckets=[0.05, 0.1, 0.5, 1, 2, 5, 10, 30],
)


def observe_pass(pass_findings: PassFindings | None) -> None:
    """Record metrics for a single modular review pass."""

    if pass_findings is None:
        return

    status = getattr(pass_findings, "status", None) or pass_findings.metadata.get(
        "status"
    )
    if isinstance(status, str) and status.lower() not in {"completed", "success"}:
        return

    checker_name = pass_findings.pass_name or "unknown"

    for finding in pass_findings.findings:
        severity = _normalise_severity(getattr(finding, "severity", None))
        checker_findings_total.labels(checker=checker_name, severity=severity).inc()

    duration = pass_findings.metadata.get("duration_seconds")
    if isinstance(duration, (int, float)) and duration >= 0:
        checker_runtime_seconds.labels(checker=checker_name).observe(duration)


def _normalise_severity(severity: Any) -> str:
    if severity is None:
        return "unknown"
    if isinstance(severity, SeverityLevel):
        return severity.value
    value = getattr(severity, "value", None)
    if isinstance(value, str):
        return value
    if isinstance(severity, str):
        return severity
    return "unknown"
