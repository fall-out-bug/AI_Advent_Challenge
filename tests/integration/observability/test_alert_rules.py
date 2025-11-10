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
