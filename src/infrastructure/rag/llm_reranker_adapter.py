"""LLM-powered reranker adapter."""

from __future__ import annotations

import asyncio
import json
import time
from statistics import pvariance
from typing import Sequence

from src.domain.rag import RerankResult, RetrievedChunk
from src.infrastructure.logging import get_logger
<<<<<<< HEAD
from src.infrastructure.metrics import rag_metrics
=======
from src.infrastructure.metrics import (
    rag_metrics,
    rag_variance_ratio,
    rag_fallback_reason_total,
)
>>>>>>> origin/master


class LLMRerankerAdapter:
    """LLM-based reranking with prompt-based scoring."""

    _MAX_CANDIDATES = 3

    def __init__(
        self,
        llm_client,
        timeout_seconds: int = 3,
        temperature: float = 0.5,
        max_tokens: int = 256,
<<<<<<< HEAD
=======
        seed: int | None = None,
>>>>>>> origin/master
    ) -> None:
        """Initialise adapter with client and configuration."""
        self._llm_client = llm_client
        self._timeout_seconds = timeout_seconds
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._logger = get_logger(__name__)
<<<<<<< HEAD
=======
        self._seed = seed
>>>>>>> origin/master

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        """Rerank chunks using LLM scoring."""
        selected = list(chunks)[: self._MAX_CANDIDATES]
        if not selected:
            raise ValueError("chunks cannot be empty for reranking.")

<<<<<<< HEAD
=======
        if self._seed is not None:
            self._logger.debug(
                "rag_rerank_seed",
                extra={"seed": self._seed},
            )

>>>>>>> origin/master
        prompt = self._build_prompt(query=query, chunks=selected)
        start_time = time.perf_counter()
        try:
            response_text = await asyncio.wait_for(
                self._llm_client.generate(
                    prompt=prompt,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                ),
                timeout=self._timeout_seconds,
            )
            result = self._parse_response(
                response_text=response_text,
                original_chunks=selected,
                start_time=start_time,
            )
            return result
        except asyncio.TimeoutError:
            self._record_fallback("timeout")
            return self._build_fallback_result(
                chunks=selected,
                start_time=start_time,
                reason="timeout",
            )
        except json.JSONDecodeError as error:
            self._logger.warning("rag_rerank_parse_error", extra={"error": str(error)})
            self._record_fallback("parse_error")
            return self._build_fallback_result(
                chunks=selected,
                start_time=start_time,
                reason="parse_error",
            )
        except Exception as error:  # noqa: BLE001
            self._logger.warning(
                "rag_rerank_exception",
                extra={"error": str(error), "exception_type": type(error).__name__},
            )
            self._record_fallback("exception")
            return self._build_fallback_result(
                chunks=selected,
                start_time=start_time,
                reason="exception",
            )

    def _build_prompt(
        self,
        *,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        lines: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            text = chunk.text.replace("\n", " ").strip()
            lines.append(f"[{index}] chunk_id: {chunk.chunk_id}")
            lines.append(f"    text: \"{text}\"")
        chunk_block = "\n".join(lines)
        return _render_prompt(query=query, chunks=chunk_block)

    def _parse_response(
        self,
        *,
        response_text: str,
        original_chunks: Sequence[RetrievedChunk],
        start_time: float,
    ) -> RerankResult:
        payload = json.loads(response_text)
        scores_field = payload.get("scores")
        if not isinstance(scores_field, dict):
            raise ValueError("scores field missing in reranker response.")

        rerank_scores: dict[str, float] = {}
        for chunk in original_chunks:
            if chunk.chunk_id not in scores_field:
                raise ValueError(
                    f"Missing rerank score for chunk_id={chunk.chunk_id}."
                )
            score = float(scores_field[chunk.chunk_id])
            rerank_scores[chunk.chunk_id] = score

        sorted_chunks = sorted(
            original_chunks,
            key=lambda chunk: rerank_scores[chunk.chunk_id],
            reverse=True,
        )

        duration = time.perf_counter() - start_time
        rag_metrics.rag_rerank_duration_seconds.labels(strategy="llm").observe(duration)
        self._record_score_delta(original_chunks, rerank_scores, sorted_chunks)
        self._record_variance(rerank_scores)

        reasoning = payload.get("reasoning")
        latency_ms = int(duration * 1000)
        return RerankResult(
            chunks=tuple(sorted_chunks),
            rerank_scores=rerank_scores,
            strategy="llm",
            latency_ms=latency_ms,
            reasoning=reasoning if isinstance(reasoning, str) else None,
        )

    def _build_fallback_result(
        self,
        *,
        chunks: Sequence[RetrievedChunk],
        start_time: float,
        reason: str,
    ) -> RerankResult:
        duration = time.perf_counter() - start_time
        rag_metrics.rag_rerank_duration_seconds.labels(strategy="llm").observe(
            duration
        )
        scores = {chunk.chunk_id: chunk.similarity_score for chunk in chunks}
        latency_ms = int(duration * 1000)
        return RerankResult(
            chunks=tuple(chunks),
            rerank_scores=scores,
            strategy="llm",
            latency_ms=latency_ms,
            reasoning=f"Fallback due to {reason}.",
        )

    def _record_fallback(self, reason: str) -> None:
        rag_metrics.rag_reranker_fallback_total.labels(reason=reason).inc()
<<<<<<< HEAD
=======
        try:
            rag_fallback_reason_total.labels(reason=reason).inc()
        except Exception:  # pragma: no cover - best-effort metric
            pass
>>>>>>> origin/master

    def _record_score_delta(
        self,
        original_chunks: Sequence[RetrievedChunk],
        rerank_scores: dict[str, float],
        sorted_chunks: Sequence[RetrievedChunk],
    ) -> None:
        original_top = original_chunks[0].similarity_score
        rerank_top = rerank_scores[sorted_chunks[0].chunk_id]
        rag_metrics.rag_rerank_score_delta.observe(rerank_top - original_top)

    def _record_variance(self, rerank_scores: dict[str, float]) -> None:
        values = list(rerank_scores.values())
        if len(values) < 2:
            rag_metrics.rag_rerank_score_variance.observe(0.0)
<<<<<<< HEAD
            return
        variance = pvariance(values)
        rag_metrics.rag_rerank_score_variance.observe(variance)
=======
            try:
                rag_variance_ratio.labels(window="current").set(0.0)
            except Exception:  # pragma: no cover - best-effort metric
                pass
            return
        variance = pvariance(values)
        rag_metrics.rag_rerank_score_variance.observe(variance)
        try:
            rag_variance_ratio.labels(window="current").set(variance)
        except Exception:  # pragma: no cover
            pass
>>>>>>> origin/master


def _load_prompt() -> str:
    from importlib import resources

    with resources.files("src.infrastructure.rag.prompts").joinpath(
        "rerank_prompt.md"
    ).open("r", encoding="utf-8") as handle:
        return handle.read()


def _render_prompt(*, query: str, chunks: str) -> str:
    template = _load_prompt()
    return template.format(query=query, chunks=chunks)

__all__ = ["LLMRerankerAdapter"]
