"""Unit tests for PromptAssembler."""

from __future__ import annotations

import pytest

from src.application.rag import PromptAssembler
from src.domain.rag import RetrievedChunk


def _build_chunk(text: str, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        text=text,
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={"source_path": "/docs/specs/architecture.md"},
    )


class TestPromptAssembler:
    """Tests for prompt assembly logic."""

    def test_build_non_rag_prompt_includes_question(self) -> None:
        """Non-RAG prompt should contain the question."""
        assembler = PromptAssembler()
        question = "Что такое MapReduce?"

        prompt = assembler.build_non_rag_prompt(question)

        assert "Вопрос:" in prompt
        assert question in prompt

    def test_build_rag_prompt_requires_chunks(self) -> None:
        """Building RAG prompt without chunks should raise ValueError."""
        assembler = PromptAssembler()

        with pytest.raises(ValueError, match="empty chunks list"):
            assembler.build_rag_prompt("Что такое MapReduce?", [])

    def test_build_rag_prompt_respects_context_budget(self) -> None:
        """Prompt should truncate context when exceeding token budget."""
        # max_context_tokens=50 => max_chars ≈ 200
        assembler = PromptAssembler(max_context_tokens=50)
        long_text = "A" * 500  # definitely above remaining budget
        chunk = _build_chunk(text=long_text, score=0.95)
        short_chunk = _build_chunk(text="short", score=0.9)

        prompt = assembler.build_rag_prompt(
            question="Что такое MapReduce?",
            chunks=[short_chunk, chunk],
        )

        # Only the short chunk should be included due to budget
        assert "short" in prompt
        assert long_text not in prompt
        assert "Контекст" in prompt
