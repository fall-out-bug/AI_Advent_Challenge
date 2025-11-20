"""Unit tests for RAG++ configuration and metrics."""

from __future__ import annotations

from pathlib import Path

from prometheus_client import REGISTRY

from src.infrastructure.config.rag_rerank import load_rag_rerank_config
from src.infrastructure.metrics import rag_fallback_reason_total


def test_rag_config_includes_new_fields(tmp_path: Path) -> None:
    """RAG config should expose seed, variance_window, adaptive_threshold."""
    config_yaml = tmp_path / "retrieval_rerank_config.yaml"
    config_yaml.write_text(
        "retrieval:\n"
        "  top_k: 5\n"
        "  score_threshold: 0.3\n"
        "reranker:\n"
        "  enabled: true\n"
        '  strategy: "llm"\n'
        "  seed: 123\n"
        '  variance_window: "rolling_5m"\n'
        "  adaptive_threshold: 0.4\n",
        encoding="utf-8",
    )

    config = load_rag_rerank_config(path=config_yaml)

    assert config.reranker.seed == 123
    assert config.reranker.variance_window == "rolling_5m"
    assert config.reranker.adaptive_threshold == 0.4


def test_rag_fallback_reason_total_metric_registered() -> None:
    """rag_fallback_reason_total metric should be registered in Prometheus."""
    rag_fallback_reason_total.labels(reason="timeout").inc()
    value = REGISTRY.get_sample_value(
        "rag_fallback_reason_total", labels={"reason": "timeout"}
    )
    assert value is not None
    assert value >= 1.0
