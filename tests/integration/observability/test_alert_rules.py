"""Validate Prometheus alert rule content."""

from __future__ import annotations

import yaml

from pathlib import Path

ALERTS_FILE = Path("prometheus/alerts.yml")


def _load_alerts() -> list[dict[str, object]]:
    with ALERTS_FILE.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    groups = data.get("groups", []) if isinstance(data, dict) else []
    alerts: list[dict[str, object]] = []
    for group in groups:
        for rule in group.get("rules", []):
            alerts.append(rule)
    return alerts


def test_unified_worker_alerts_present() -> None:
    alerts = _load_alerts()
    names = {rule.get("alert") for rule in alerts}
    assert {"UnifiedWorkerDown", "UnifiedWorkerHighErrorRate"}.issubset(names)


def test_mcp_alert_uses_new_metric() -> None:
    alerts = _load_alerts()
    mcp_rule = next(rule for rule in alerts if rule.get("alert") == "MCPServerHighErrorRate")
    expr = mcp_rule.get("expr")
    assert "mcp_requests_total" in expr
<<<<<<< HEAD
=======


def test_epic23_observability_alerts_present() -> None:
    """Verify Epic 23 observability alerts are present."""
    alerts = _load_alerts()
    names = {rule.get("alert") for rule in alerts}
    assert "SharedInfraBootstrapFailed" in names
    assert "BenchmarkExportSlow" in names
    assert "StructuredLogsVolumeSpike" in names
    assert "RAGVarianceThresholdExceeded" in names


def test_loki_alerts_present() -> None:
    """Verify Loki alert rules are present."""
    alerts = _load_alerts()
    names = {rule.get("alert") for rule in alerts}
    assert "LokiHighErrorRate" in names
    assert "LokiIngestionBacklog" in names


def test_epic23_alerts_use_new_metrics() -> None:
    """Verify Epic 23 alerts use new metrics from observability_labels.md."""
    alerts = _load_alerts()
    bootstrap_rule = next(
        rule for rule in alerts if rule.get("alert") == "SharedInfraBootstrapFailed"
    )
    expr = bootstrap_rule.get("expr")
    assert "shared_infra_bootstrap_status" in expr

    export_rule = next(rule for rule in alerts if rule.get("alert") == "BenchmarkExportSlow")
    expr = export_rule.get("expr")
    assert "benchmark_export_duration_seconds" in expr

    logs_rule = next(rule for rule in alerts if rule.get("alert") == "StructuredLogsVolumeSpike")
    expr = logs_rule.get("expr")
    assert "structured_logs_total" in expr

    rag_rule = next(rule for rule in alerts if rule.get("alert") == "RAGVarianceThresholdExceeded")
    expr = rag_rule.get("expr")
    assert "rag_variance_ratio" in expr
>>>>>>> origin/master
