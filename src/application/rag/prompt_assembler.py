"""Prompt assembly service for RAG system."""

from __future__ import annotations

from typing import Sequence

from src.domain.rag import RetrievedChunk


class PromptAssembler:
    """Format prompts for RAG and non-RAG modes.

    Purpose:
        Encapsulate prompt formatting logic with token budget management.
    """

    _SYSTEM_PROMPT_NON_RAG = """Ты — помощник, отвечающий на вопросы по курсам Big Data
и Machine Learning.

Инструкции:
- Отвечай на русском языке, если вопрос задан на русском.
- Если не знаешь точного ответа, честно скажи об этом.
- Будь кратким и конкретным (2-4 абзаца максимум).
- Не выдумывай факты и не галлюцинируй.

Вопрос:
{question}
"""

    _SYSTEM_PROMPT_RAG = """Ты — помощник, отвечающий на вопросы по курсам Big Data
и Machine Learning.

Инструкции:
- Используй ТОЛЬКО информацию из предоставленного контекста для ответа.
- Если в контексте нет ответа, скажи:
- "В предоставленных документах информация не найдена."
- Отвечай на русском языке, если вопрос задан на русском.
- Будь кратким и конкретным (2-4 абзаца максимум).
- Если можешь, укажи источник информации
- (например, "Согласно документу X...").

Контекст (релевантные фрагменты документов):

{context}

---

Вопрос:
{question}
"""

    _CHUNK_TEMPLATE = """[Фрагмент {ordinal} | Релевантность: {score:.2f}]
Источник: {source_path}

{text}

---
"""

    def __init__(self, max_context_tokens: int = 3000) -> None:
        """Initialise prompt assembler with token budget.

        Purpose:
            Configure maximum context size for RAG prompts.

        Args:
            max_context_tokens: Maximum tokens for retrieved context (default: 3000).

        Example:
            >>> assembler = PromptAssembler(max_context_tokens=2000)
        """
        self._max_context_tokens = max_context_tokens

    def build_non_rag_prompt(self, question: str) -> str:
        """Build non-RAG prompt (baseline).

        Purpose:
            Format question without any retrieved context.

        Args:
            question: User question.

        Returns:
            Formatted prompt string.

        Example:
            >>> assembler = PromptAssembler()
            >>> prompt = assembler.build_non_rag_prompt("Что такое MapReduce?")
            >>> "MapReduce" in prompt
            False
            >>> "Вопрос:" in prompt
            True
        """
        return self._SYSTEM_PROMPT_NON_RAG.format(question=question)

    def build_rag_prompt(
        self,
        question: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        """Build RAG prompt with retrieved context.

        Purpose:
            Format question with retrieved document chunks, respecting token budget.

        Args:
            question: User question.
            chunks: Retrieved chunks (pre-sorted by relevance).

        Returns:
            Formatted prompt string with context.

        Raises:
            ValueError: If chunks list is empty.

        Example:
            >>> assembler = PromptAssembler(max_context_tokens=1000)
            >>> chunk = RetrievedChunk(
            ...     chunk_id="c1",
            ...     document_id="d1",
            ...     text="MapReduce — это модель программирования.",
            ...     similarity_score=0.9,
            ...     source_path="/docs/lectures/mapreduce.md",
            ...     metadata={},
            ... )
            >>> prompt = assembler.build_rag_prompt("Что такое MapReduce?", [chunk])
            >>> "Контекст" in prompt
            True
            >>> "MapReduce" in prompt
            True
        """
        if not chunks:
            raise ValueError("Cannot build RAG prompt with empty chunks list.")

        context = self._format_chunks(chunks, self._max_context_tokens)
        return self._SYSTEM_PROMPT_RAG.format(context=context, question=question)

    def _format_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        max_tokens: int,
    ) -> str:
        """Format chunks with token budget control.

        Purpose:
            Concatenate chunks into a single context string, truncating if needed.

        Args:
            chunks: Retrieved chunks to format.
            max_tokens: Maximum tokens for context.

        Returns:
            Formatted context string.

        Note:
            Uses simple heuristic (1 token ≈ 4 chars) for token estimation.
        """
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Heuristic: 1 token ≈ 4 chars (UTF-8)

        for idx, chunk in enumerate(chunks):
            formatted_chunk = self._CHUNK_TEMPLATE.format(
                ordinal=idx + 1,
                score=chunk.similarity_score,
                source_path=chunk.source_path,
                text=chunk.text,
            )

            chunk_chars = len(formatted_chunk)
            if total_chars + chunk_chars > max_chars:
                break  # Stop adding chunks to avoid overflow

            context_parts.append(formatted_chunk)
            total_chars += chunk_chars

        return "\n".join(context_parts)
