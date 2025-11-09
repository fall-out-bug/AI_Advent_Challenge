"""Integration tests for Prometheus metric exporters."""

from __future__ import annotations

from typing import Dict

from src.infrastructure.monitoring import mcp_metrics, worker_metrics


def _sample_value(metric, label_values: Dict[str, str]) -> float:
    for collected in metric.collect():
        for sample in collected.samples:
            if sample.labels == label_values:
                return sample.value
    return 0.0


def test_record_mcp_request_increments_counter() -> None:
    labels = {"tool": "pytest-tool", "status": "success"}
    before = _sample_value(mcp_metrics.MCP_REQUESTS_TOTAL, labels)

    mcp_metrics.record_mcp_request("pytest-tool", "success", 0.5)

    after = _sample_value(mcp_metrics.MCP_REQUESTS_TOTAL, labels)
    assert after == before + 1


def test_record_worker_task_updates_metrics() -> None:
    labels = {"task_type": "code_review", "status": "success"}
    before = _sample_value(worker_metrics.UNIFIED_WORKER_TASKS_TOTAL, labels)

    worker_metrics.record_worker_task("code_review", "success", 2.5)

    after = _sample_value(worker_metrics.UNIFIED_WORKER_TASKS_TOTAL, labels)
    assert after == before + 1


def test_set_worker_queue_depth_sets_gauge() -> None:
    worker_metrics.set_worker_queue_depth("code_review", 42)
    value = _sample_value(
        worker_metrics.UNIFIED_WORKER_QUEUE_DEPTH, {"task_type": "code_review"}
    )
    assert value == 42
