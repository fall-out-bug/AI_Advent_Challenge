"""Tests for LLMRerankerAdapter prompt construction."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Sequence

import pytest

from src.domain.rag import RetrievedChunk
from src.infrastructure.rag.llm_reranker_adapter import LLMRerankerAdapter


def _build_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=f"Content for {chunk_id}",
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={},
    )


@dataclass
class RecordingLLMClient:
    """Record prompts passed to LLM."""

    response_payload: dict[str, object]
    calls: list[dict[str, object]] = field(default_factory=list)

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return json.dumps(self.response_payload)


@pytest.mark.asyncio
async def test_llm_reranker_prompt_format() -> None:
    """Adapter should build prompt with query and top-3 chunks."""
    chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.8),
        _build_chunk("chunk-3", 0.7),
        _build_chunk("chunk-4", 0.6),
    ]
    llm_client = RecordingLLMClient(
        response_payload={
            "scores": {
                "chunk-1": 0.75,
                "chunk-2": 0.65,
                "chunk-3": 0.85,
            },
            "reasoning": "chunk-3 is most relevant",
        }
    )
    adapter = LLMRerankerAdapter(
        llm_client=llm_client,
        timeout_seconds=3,
        temperature=0.5,
        max_tokens=256,
    )

    result = await adapter.rerank("What is MapReduce?", chunks)

    assert llm_client.calls, "LLM client should be invoked once."
    call = llm_client.calls[0]
    prompt = call["prompt"]
    assert "Query: What is MapReduce?" in prompt
    assert "[1] chunk_id: chunk-1" in prompt
    assert "[2] chunk_id: chunk-2" in prompt
    assert "[3] chunk_id: chunk-3" in prompt
    assert "chunk-4" not in prompt, "Prompt must include only top-3 candidates."
    assert call["temperature"] == 0.5
    assert call["max_tokens"] == 256
    assert [chunk.chunk_id for chunk in result.chunks] == [
        "chunk-3",
        "chunk-1",
        "chunk-2",
    ]
    assert result.reasoning == "chunk-3 is most relevant"


@dataclass
class TimeoutLLMClient:
    """LLM client that times out to trigger fallback."""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        raise asyncio.TimeoutError("LLM call timed out")


@pytest.mark.asyncio
async def test_llm_reranker_timeout_fallback() -> None:
    """Timeout should return original order with fallback reasoning."""
    chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.8),
    ]
    adapter = LLMRerankerAdapter(
        llm_client=TimeoutLLMClient(),
        timeout_seconds=1,
        temperature=0.5,
        max_tokens=128,
    )

    result = await adapter.rerank("What is MapReduce?", chunks)

    assert [chunk.chunk_id for chunk in result.chunks] == ["chunk-1", "chunk-2"]
    assert "timeout" in (result.reasoning or "").lower()
