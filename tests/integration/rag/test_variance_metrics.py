"""Integration tests for RAG++ variance and fallback metrics."""

from __future__ import annotations

from typing import Sequence

from prometheus_client import REGISTRY

from src.domain.rag import RetrievedChunk
from src.infrastructure.rag import LLMRerankerAdapter
from src.infrastructure.metrics import rag_variance_ratio, rag_fallback_reason_total


class _DummyLLMClient:
    async def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        return '{"scores": {"c1": 0.1, "c2": 0.4, "c3": 0.9}, "reasoning": "ok"}'


def _make_chunks() -> Sequence[RetrievedChunk]:
    return (
        RetrievedChunk(
            chunk_id="c1",
            document_id="d1",
            text="one",
            similarity_score=0.1,
            source_path="/docs/d1.md",
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="c2",
            document_id="d1",
            text="two",
            similarity_score=0.2,
            source_path="/docs/d1.md",
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="c3",
            document_id="d1",
            text="three",
            similarity_score=0.3,
            source_path="/docs/d1.md",
            metadata={},
        ),
    )


async def test_variance_metric_updated_on_successful_rerank() -> None:
    """rag_variance_ratio should be updated after rerank."""
    adapter = LLMRerankerAdapter(
        llm_client=_DummyLLMClient(),
        timeout_seconds=5,
        temperature=0.1,
        max_tokens=64,
        seed=123,
    )
    await adapter.rerank(query="q", chunks=_make_chunks())

    value = REGISTRY.get_sample_value(
        "rag_variance_ratio", labels={"window": "current"}
    )
    assert value is not None
    assert value >= 0.0


async def test_fallback_metrics_updated_on_timeout(monkeypatch) -> None:
    """Fallback metrics should be updated when reranker times out."""

    adapter = LLMRerankerAdapter(
        llm_client=_DummyLLMClient(),
        timeout_seconds=1,
        temperature=0.1,
        max_tokens=64,
        seed=456,
    )

    adapter._record_fallback("timeout")  # type: ignore[attr-defined]

    value = REGISTRY.get_sample_value(
        "rag_fallback_reason_total", labels={"reason": "timeout"}
    )
    assert value is not None
    assert value >= 1.0


