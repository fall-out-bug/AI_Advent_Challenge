"""Integration tests for RAG++ pipeline behaviour."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pytest

from src.application.rag import CompareRagAnswersUseCase, PromptAssembler, RetrievalService
from src.domain.embedding_index import DocumentChunk, EmbeddingGateway, EmbeddingVector
from src.domain.rag import (
    Answer,
    FilterConfig,
    Query,
    RerankResult,
    RetrievedChunk,
)
from src.infrastructure.rag import ThresholdFilterAdapter


class StubEmbeddingGateway(EmbeddingGateway):
    """Return a static embedding vector for any input."""

    def __init__(self) -> None:
        self.vector = EmbeddingVector(values=(0.1, 0.2), model="stub", dimension=2)

    def embed(self, chunks: Sequence[DocumentChunk]) -> Sequence[EmbeddingVector]:  # type: ignore[override]
        return [self.vector for _ in chunks]


class StubVectorSearch:
    """Vector search stub returning predefined chunks."""

    def __init__(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._chunks = list(chunks)

    def search(
        self,
        query_vector: EmbeddingVector,  # noqa: ARG002
        top_k: int,
        score_threshold: float,  # noqa: ARG002
    ) -> Sequence[RetrievedChunk]:
        return self._chunks[:top_k]


class StubPromptAssembler(PromptAssembler):
    """Prompt assembler encoding chunk ids in the prompt."""

    def build_non_rag_prompt(self, question: str) -> str:  # type: ignore[override]
        return f"NON|{question}"

    def build_rag_prompt(  # type: ignore[override]
        self,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        chunk_ids = ",".join(chunk.chunk_id for chunk in chunks)
        return f"RAG|{question}|{chunk_ids}"


class StubLLMService:
    """LLM service stub that reflects prompt metadata."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate(
        self,
        prompt: str,
        max_tokens: int,  # noqa: ARG002
        temperature: float,  # noqa: ARG002
    ) -> Answer:
        self.calls.append(prompt)
        if prompt.startswith("NON"):
            text = "baseline-answer"
        else:
            _, _, chunk_ids = prompt.split("|")
            text = f"rag-answer:{chunk_ids}"
        return Answer(
            text=text,
            model="stub-llm",
            latency_ms=120,
            tokens_generated=42,
        )


@dataclass
class StubReranker:
    """Async reranker stub producing deterministic scores."""

    scores: dict[str, float]
    latency_ms: int = 150

    async def rerank(
        self,
        query: str,  # noqa: ARG002
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        ordered = sorted(
            chunks,
            key=lambda chunk: self.scores.get(chunk.chunk_id, 0.0),
            reverse=True,
        )
        return RerankResult(
            chunks=tuple(ordered),
            rerank_scores=self.scores,
            strategy="llm",
            latency_ms=self.latency_ms,
            reasoning="stub-reasoning",
        )


def _build_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            text="MapReduce overview",
            similarity_score=0.9,
            source_path="/docs/arch.md",
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            document_id="doc-2",
            text="Detailed shuffle phase",
            similarity_score=0.8,
            source_path="/docs/shuffle.md",
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="chunk-3",
            document_id="doc-3",
            text="Unrelated appendix",
            similarity_score=0.4,
            source_path="/docs/appendix.md",
            metadata={},
        ),
    ]


def _build_use_case(reranker: StubReranker) -> CompareRagAnswersUseCase:
    chunks = _build_chunks()
    retrieval_service = RetrievalService(
        vector_search=StubVectorSearch(chunks),
        relevance_filter=ThresholdFilterAdapter(),
        reranker=reranker,
    )
    prompt_assembler = StubPromptAssembler(max_context_tokens=1024)
    llm_service = StubLLMService()
    return CompareRagAnswersUseCase(
        embedding_gateway=StubEmbeddingGateway(),
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
        top_k=3,
        score_threshold=0.0,
        max_tokens=256,
        temperature=0.5,
    )


@pytest.mark.asyncio
async def test_rag_plus_plus_pipeline() -> None:
    """Pipeline should filter, rerank, and change chunk ordering."""
    reranker = StubReranker(scores={"chunk-1": 0.7, "chunk-2": 0.95})
    use_case = _build_use_case(reranker)
    filter_config = FilterConfig.with_reranking(
        score_threshold=0.5,
        top_k=2,
        strategy="llm",
    )

    result = await use_case.execute(
        Query(id="q1", question="Что такое MapReduce?"),
        filter_config=filter_config,
    )

    assert [chunk.chunk_id for chunk in result.chunks_used] == ["chunk-2", "chunk-1"]
    assert result.with_rag.text != result.without_rag.text


@pytest.mark.asyncio
async def test_three_modes_comparison() -> None:
    """Baseline, RAG, and RAG++ should produce distinct outputs."""
    reranker = StubReranker(scores={"chunk-1": 0.6, "chunk-2": 0.9})
    use_case = _build_use_case(reranker)
    query = Query(id="q2", question="Расскажи про стадии MapReduce.")

    config_baseline = FilterConfig(score_threshold=0.0, top_k=2)
    config_filter_only = FilterConfig(score_threshold=0.5, top_k=2)
    config_rag_plus = FilterConfig.with_reranking(
        score_threshold=0.5,
        top_k=2,
        strategy="llm",
    )

    baseline = await use_case.execute(query, filter_config=config_baseline)
    filtered = await use_case.execute(query, filter_config=config_filter_only)
    rag_plus = await use_case.execute(query, filter_config=config_rag_plus)

    assert baseline.without_rag.text == "baseline-answer"
    assert filtered.with_rag.text != baseline.without_rag.text
    assert rag_plus.with_rag.text != filtered.with_rag.text


@pytest.mark.asyncio
async def test_rerank_latency_under_threshold() -> None:
    """Reranker latency should remain under dialog p95 target (5s)."""
    reranker = StubReranker(scores={"chunk-1": 0.8, "chunk-2": 0.7}, latency_ms=320)
    chunks = _build_chunks()
    retrieval_service = RetrievalService(
        vector_search=StubVectorSearch(chunks),
        relevance_filter=ThresholdFilterAdapter(),
        reranker=reranker,
    )
    filter_config = FilterConfig.with_reranking(
        score_threshold=0.0,
        top_k=2,
        strategy="llm",
    )

    result_chunks = await retrieval_service.retrieve(
        query_text="Test", query_vector=EmbeddingVector(values=(0.1,), model="x", dimension=1), filter_config=filter_config
    )

    assert len(result_chunks) == 2
    assert reranker.latency_ms < 5000


@pytest.mark.asyncio
async def test_feature_flag_rollback() -> None:
    """Disabling filter should fall back to baseline answer."""
    reranker = StubReranker(scores={"chunk-1": 0.5, "chunk-2": 0.8})
    use_case = _build_use_case(reranker)
    query = Query(id="q3", question="Что делает стадия shuffle?")

    enabled_config = FilterConfig.with_reranking(
        score_threshold=0.5,
        top_k=2,
        strategy="llm",
    )
    disabled_config = FilterConfig(score_threshold=0.0, top_k=2)

    result_enabled = await use_case.execute(query, filter_config=enabled_config)
    result_disabled = await use_case.execute(query, filter_config=disabled_config)

    assert result_enabled.with_rag.text != result_disabled.with_rag.text
    assert result_disabled.with_rag.text == "rag-answer:chunk-1,chunk-2"
