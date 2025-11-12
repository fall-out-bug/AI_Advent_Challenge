"""Tests for rag CLI commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from src.domain.rag import Answer, ComparisonResult, FilterConfig, Query, RetrievedChunk
from src.presentation.cli import rag_commands


def _default_rag_config() -> rag_commands.RagRerankConfig:
    return rag_commands.RagRerankConfig()


def test_compute_filter_config_applies_overrides() -> None:
    """Overrides should apply on top of configuration defaults."""
    config = _default_rag_config()

    filter_config = rag_commands._compute_filter_config(  # type: ignore[attr-defined]
        config,
        filter_override=True,
        threshold_override=0.42,
        reranker_override="llm",
    )

    assert filter_config.score_threshold == pytest.approx(0.42)
    assert filter_config.top_k == config.retrieval.top_k
    assert filter_config.reranker_enabled is True
    assert filter_config.reranker_strategy == "llm"


def test_compute_filter_config_disables_filter() -> None:
    """Disabling filter should zero the threshold and reranker."""
    config = _default_rag_config()

    filter_config = rag_commands._compute_filter_config(  # type: ignore[attr-defined]
        config,
        filter_override=False,
        threshold_override=None,
        reranker_override="off",
    )

    assert filter_config.score_threshold == 0.0
    assert filter_config.reranker_enabled is False
    assert filter_config.reranker_strategy == "off"


def _build_result(query: Query) -> ComparisonResult:
    answer = Answer(text="answer", model="qwen", latency_ms=10, tokens_generated=5)
    return ComparisonResult(
        query=query,
        without_rag=answer,
        with_rag=answer,
        chunks_used=[
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                text="text",
                similarity_score=0.9,
                source_path="/path",
                metadata={},
            )
        ],
        timestamp="2025-11-12T00:00:00Z",
    )


def test_compare_command_applies_cli_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI should honour filter and reranker flags."""
    captured: dict[str, Any] = {}

    class StubUseCase:
        async def execute(
            self,
            query: Query,
            filter_config: FilterConfig | None = None,
        ) -> ComparisonResult:
            captured["filter_config"] = filter_config
            return _build_result(query)

    def fake_build_pipeline() -> tuple[StubUseCase, rag_commands.RagRerankConfig]:
        return StubUseCase(), _default_rag_config()

    monkeypatch.setattr(rag_commands, "_build_pipeline", fake_build_pipeline)

    runner = CliRunner()
    result = runner.invoke(
        rag_commands.rag_commands,
        [
            "compare",
            "--question",
            "Что такое MapReduce?",
            "--filter",
            "--threshold",
            "0.4",
            "--reranker",
            "llm",
        ],
    )

    assert result.exit_code == 0
    filter_config = captured["filter_config"]
    assert isinstance(filter_config, FilterConfig)
    assert filter_config.score_threshold == pytest.approx(0.4)
    assert filter_config.reranker_enabled is True
    assert filter_config.reranker_strategy == "llm"


def test_run_batch_writes_results(tmp_path: Path) -> None:
    """Batch runner should execute queries and emit JSON lines."""
    queries_path = tmp_path / "queries.jsonl"
    output_path = tmp_path / "out.jsonl"
    queries_path.write_text(
        json.dumps({"id": "q1", "question": "Что такое MapReduce?"}) + "\n",
        encoding="utf-8",
    )

    class StubUseCase:
        async def execute(
            self,
            query: Query,
            filter_config: FilterConfig | None = None,
        ) -> ComparisonResult:
            return _build_result(query)

    filter_config = FilterConfig()

    asyncio.run(
        rag_commands._run_batch(  # type: ignore[attr-defined]
            use_case=StubUseCase(),
            queries_path=queries_path,
            out_path=output_path,
            filter_config=filter_config,
        )
    )

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["query"]["question"] == "Что такое MapReduce?"
