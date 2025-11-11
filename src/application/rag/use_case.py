"""Use case for comparing RAG vs non-RAG answers."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.domain.embedding_index import EmbeddingGateway
from src.domain.rag import Answer, ComparisonResult, Query
from src.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from src.domain.rag import LLMService

    from .prompt_assembler import PromptAssembler
    from .retrieval_service import RetrievalService


class CompareRagAnswersUseCase:
    """Orchestrate side-by-side comparison of RAG vs non-RAG answers.

    Purpose:
        Coordinate the dual-path workflow (baseline + RAG) and return a
        structured comparison result.
    """

    def __init__(
        self,
        embedding_gateway: EmbeddingGateway,
        retrieval_service: RetrievalService,
        prompt_assembler: PromptAssembler,
        llm_service: LLMService,
        top_k: int = 5,
        score_threshold: float = 0.3,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> None:
        """Initialise use case with dependencies.

        Purpose:
            Capture injected collaborators and retrieval configuration.

        Args:
            embedding_gateway: Service for embedding query text.
            retrieval_service: Service for retrieving chunks.
            prompt_assembler: Service for formatting prompts.
            llm_service: Service for generating answers.
            top_k: Number of chunks to retrieve (default: 5).
            score_threshold: Minimum similarity score (default: 0.3).
            max_tokens: Maximum tokens for LLM generation (default: 1000).
            temperature: Sampling temperature (default: 0.7).

        Example:
            >>> use_case = CompareRagAnswersUseCase(  # doctest: +SKIP
            ...     embedding_gateway=...,
            ...     retrieval_service=...,
            ...     prompt_assembler=...,
            ...     llm_service=...,
            ... )
        """
        self._embedding_gateway = embedding_gateway
        self._retrieval_service = retrieval_service
        self._prompt_assembler = prompt_assembler
        self._llm_service = llm_service
        self._top_k = top_k
        self._score_threshold = score_threshold
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._logger = get_logger(__name__)

    def execute(self, query: Query) -> ComparisonResult:
        """Execute RAG vs non-RAG comparison for a query.

        Purpose:
            Generate answers in both modes and return structured comparison.

        Args:
            query: User query to answer.

        Returns:
            ComparisonResult with both answers and retrieved chunks.

        Raises:
            RuntimeError: If LLM or embedding service is unavailable.

        Example:
            >>> use_case = CompareRagAnswersUseCase(...)  # doctest: +SKIP
            >>> query = Query(id="q1", question="Что такое MapReduce?")
            >>> result = use_case.execute(query)
        """
        self._logger.info(
            "rag_comparison_started",
            query_id=query.id,
            question=query.question[:50],
        )

        # 1. Non-RAG path (baseline)
        non_rag_prompt = self._prompt_assembler.build_non_rag_prompt(query.question)
        without_rag = self._generate_answer(
            prompt=non_rag_prompt,
            mode="without_rag",
        )

        # 2. RAG path (retrieval + context-augmented generation)
        try:
            # 2.1 Embed query
            query_embedding = self._embed_query(query.question)

            # 2.2 Retrieve chunks
            chunks = self._retrieval_service.retrieve(
                query_vector=query_embedding,
                top_k=self._top_k,
                score_threshold=self._score_threshold,
            )
            self._logger.info(
                "rag_retrieval_completed",
                chunks_retrieved=len(chunks),
            )

            # 2.3 Generate RAG answer
            if chunks:
                rag_prompt = self._prompt_assembler.build_rag_prompt(
                    question=query.question,
                    chunks=chunks,
                )
                with_rag = self._generate_answer(
                    prompt=rag_prompt,
                    mode="with_rag",
                )
            else:
                # No chunks retrieved, use non-RAG answer as fallback
                self._logger.warning("rag_empty_retrieval", query_id=query.id)
                with_rag = without_rag
                chunks = []
        except Exception as error:
            # Graceful fallback: use non-RAG answer if retrieval fails
            self._logger.error(
                "rag_retrieval_failed",
                query_id=query.id,
                error=str(error),
            )
            with_rag = without_rag
            chunks = []

        # 3. Assemble result
        timestamp = datetime.now(timezone.utc).isoformat()
        result = ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=chunks,
            timestamp=timestamp,
        )

        self._logger.info(
            "rag_comparison_completed",
            query_id=query.id,
            chunks_used=len(chunks),
        )

        return result

    def _embed_query(self, text: str):
        """Embed query text using embedding gateway.

        Purpose:
            Convert query text to embedding vector for retrieval.

        Args:
            text: Query text to embed.

        Returns:
            EmbeddingVector for the query.

        Raises:
            RuntimeError: If embedding service is unavailable.
        """
        # Note: This assumes EmbeddingGateway has been extended with embed_query
        # or we use embed() with a dummy chunk. Implementation deferred to
        # infrastructure layer.
        from src.domain.embedding_index import DocumentChunk

        dummy_chunk = DocumentChunk(
            chunk_id="query",
            document_id="query",
            ordinal=0,
            text=text,
            token_count=len(text.split()),
        )
        vectors = self._embedding_gateway.embed([dummy_chunk])
        return vectors[0]

    def _generate_answer(self, *, prompt: str, mode: str) -> Answer:
        """Safely call LLM service and fall back on errors."""
        try:
            answer = self._llm_service.generate(
                prompt=prompt,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
        except Exception as error:  # noqa: BLE001
            self._logger.error(
                "rag_llm_failed",
                mode=mode,
                error=str(error),
            )
            return Answer(
                text=f"[{mode}] LLM unavailable: {error}",
                model="fallback",
                latency_ms=0,
                tokens_generated=0,
                metadata={"error": "llm_unavailable"},
            )

        self._logger.info(
            "rag_llm_completed",
            mode=mode,
            latency_ms=answer.latency_ms,
            tokens=answer.tokens_generated,
        )
        return self._sanitize_answer(answer)

    def _sanitize_answer(self, answer: Answer) -> Answer:
        """Return answer with Markdown artefacts removed."""
        cleaned_text = self._strip_markdown(answer.text)
        if cleaned_text == answer.text:
            return answer
        return Answer(
            text=cleaned_text,
            model=answer.model,
            latency_ms=answer.latency_ms,
            tokens_generated=answer.tokens_generated,
            metadata=answer.metadata,
        )

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Convert common Markdown formatting to plain text."""
        normalised = text.replace("\r\n", "\n")
        # Remove code fences/backticks
        normalised = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", normalised, flags=re.DOTALL)
        # Remove bold/italic markers
        normalised = re.sub(r"(\*\*|__)(.*?)\1", r"\2", normalised)
        normalised = re.sub(r"(\*|_)(.*?)\1", r"\2", normalised)
        # Strip heading markers
        normalised = re.sub(r"^\s{0,3}#{1,6}\s*", "", normalised, flags=re.MULTILINE)
        # Replace bullet markers with unicode bullet
        normalised = re.sub(r"^\s*[-*+]\s+", "• ", normalised, flags=re.MULTILINE)
        # Remove horizontal rules
        normalised = re.sub(r"^\s*([-*_]){3,}\s*$", "", normalised, flags=re.MULTILINE)
        return normalised.strip()
