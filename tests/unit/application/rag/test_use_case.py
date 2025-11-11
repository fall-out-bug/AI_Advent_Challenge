"""Unit tests for CompareRagAnswersUseCase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pytest

from src.application.rag import CompareRagAnswersUseCase
from src.domain.embedding_index import DocumentChunk, EmbeddingVector
from src.domain.rag import Answer, Query, RetrievedChunk


@dataclass
class StubEmbeddingGateway:
    """Stub embedding gateway returning a fixed vector."""

    vector: EmbeddingVector

    def embed(self, _: Sequence[DocumentChunk]) -> Sequence[EmbeddingVector]:
        return [self.vector]


@dataclass
class StubPromptAssembler:
    """Stub prompt assembler returning deterministic prompts."""

    non_rag_prompt: str
    rag_prompt: str

    def build_non_rag_prompt(self, question: str) -> str:
        return self.non_rag_prompt.format(question=question)

    def build_rag_prompt(
        self,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        assert chunks  # ensure chunks were passed
        return self.rag_prompt.format(question=question)


@dataclass
class StubRetrievalService:
    """Stub retrieval service with configurable behaviour."""

    chunks: Sequence[RetrievedChunk]
    should_raise: bool = False

    def retrieve(self, *args, **kwargs):
        if self.should_raise:
            raise RuntimeError("retrieval failed")
        return self.chunks


@dataclass
class StubLLMService:
    """Stub LLM service producing predefined answers."""

    responses: list[Answer]

    def generate(self, prompt: str, max_tokens: int, temperature: float) -> Answer:
        if not self.responses:
            raise AssertionError("No responses configured")
        return self.responses.pop(0)


def _build_retrieved_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        text="chunk text",
        similarity_score=0.9,
        source_path="/docs/specs/architecture.md",
        metadata={"source_path": "/docs/specs/architecture.md"},
    )


def _build_answer(text: str) -> Answer:
    return Answer(
        text=text,
        model="qwen",
        latency_ms=100,
        tokens_generated=42,
    )


def test_use_case_generates_rag_and_non_rag_answers() -> None:
    """Use case should call both paths when retrieval succeeds."""
    query = Query(id="arch_001", question="Что такое Clean Architecture?")
    embedding_vector = EmbeddingVector(
        values=(0.1, 0.2), model="all-MiniLM-L6-v2", dimension=2
    )
    embedding_gateway = StubEmbeddingGateway(vector=embedding_vector)
    prompt_assembler = StubPromptAssembler(
        non_rag_prompt="NON_RAG:{question}",
        rag_prompt="RAG:{question}",
    )
    chunk = _build_retrieved_chunk()
    retrieval_service = StubRetrievalService(chunks=[chunk])
    llm_service = StubLLMService(
        responses=[
            _build_answer("baseline answer"),
            _build_answer("rag answer"),
        ]
    )

    use_case = CompareRagAnswersUseCase(
        embedding_gateway=embedding_gateway,
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
        top_k=3,
        score_threshold=0.3,
        max_tokens=1000,
        temperature=0.7,
    )

    result = use_case.execute(query)

    assert result.query == query
    assert result.without_rag.text == "baseline answer"
    assert result.with_rag.text == "rag answer"
    assert result.chunks_used == [chunk]


def test_use_case_falls_back_when_retrieval_empty() -> None:
    """Empty retrieval should fall back to non-RAG answer."""
    query = Query(id="arch_002", question="Что такое CAP?")
    embedding_vector = EmbeddingVector(
        values=(0.2, 0.3), model="all-MiniLM-L6-v2", dimension=2
    )
    embedding_gateway = StubEmbeddingGateway(vector=embedding_vector)
    prompt_assembler = StubPromptAssembler(
        non_rag_prompt="NON_RAG:{question}",
        rag_prompt="RAG:{question}",
    )
    retrieval_service = StubRetrievalService(chunks=[])
    llm_service = StubLLMService(responses=[_build_answer("single answer")])

    use_case = CompareRagAnswersUseCase(
        embedding_gateway=embedding_gateway,
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
    )

    result = use_case.execute(query)

    assert result.without_rag.text == "single answer"
    assert result.with_rag.text == "single answer"
    assert result.chunks_used == []


def test_use_case_handles_retrieval_failure() -> None:
    """Exceptions during retrieval should be logged and fallback used."""
    query = Query(id="arch_003", question="Что такое RAG?")
    embedding_vector = EmbeddingVector(
        values=(0.3, 0.4), model="all-MiniLM-L6-v2", dimension=2
    )
    embedding_gateway = StubEmbeddingGateway(vector=embedding_vector)
    prompt_assembler = StubPromptAssembler(
        non_rag_prompt="NON_RAG:{question}",
        rag_prompt="RAG:{question}",
    )
    retrieval_service = StubRetrievalService(chunks=[], should_raise=True)
    llm_service = StubLLMService(responses=[_build_answer("fallback answer")])

    use_case = CompareRagAnswersUseCase(
        embedding_gateway=embedding_gateway,
        retrieval_service=retrieval_service,
        prompt_assembler=prompt_assembler,
        llm_service=llm_service,
    )

    result = use_case.execute(query)

    assert result.without_rag.text == "fallback answer"
    assert result.with_rag.text == "fallback answer"
    assert result.chunks_used == []
