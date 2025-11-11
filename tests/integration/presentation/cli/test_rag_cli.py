"""CLI integration smoke tests for RAG commands."""

from __future__ import annotations

import json
from typing import List

import pytest
from click.testing import CliRunner

from src.domain.rag import Answer, ComparisonResult, Query, RetrievedChunk
from src.presentation.cli.rag_commands import rag_commands

pytestmark = pytest.mark.integration


class StubUseCase:
    """Stub use case that returns deterministic answers."""

    def __init__(self) -> None:
        self.calls: List[Query] = []
        self._counter = 0

    def execute(self, query: Query) -> ComparisonResult:
        self.calls.append(query)
        self._counter += 1
        suffix = str(self._counter)
        without_rag = Answer(
            text=f"baseline-{suffix}",
            model="stub",
            latency_ms=10,
            tokens_generated=10,
        )
        with_rag = Answer(
            text=f"rag-{suffix}",
            model="stub",
            latency_ms=12,
            tokens_generated=12,
        )
        chunk = RetrievedChunk(
            chunk_id=f"chunk-{suffix}",
            document_id="doc-stub",
            text="stub chunk text",
            similarity_score=0.9,
            source_path="stub/path.md",
            metadata={"source_path": "stub/path.md"},
        )
        return ComparisonResult(
            query=query,
            without_rag=without_rag,
            with_rag=with_rag,
            chunks_used=[chunk],
            timestamp="2025-11-11T00:00:00Z",
        )


@pytest.fixture
def stub_use_case(monkeypatch) -> StubUseCase:
    stub = StubUseCase()
    monkeypatch.setattr(
        "src.presentation.cli.rag_commands._build_use_case",
        lambda: stub,
    )
    return stub


def test_compare_command_uses_stub_use_case(stub_use_case: StubUseCase) -> None:
    runner = CliRunner()
    result = runner.invoke(
        rag_commands,
        ["compare", "--question", "Что такое MapReduce?"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["query"]["question"] == "Что такое MapReduce?"
    assert payload["with_rag"]["text"] == "rag-1"
    assert (
        stub_use_case.calls
        and stub_use_case.calls[0].question == "Что такое MapReduce?"
    )


def test_batch_command_writes_jsonl(tmp_path, stub_use_case: StubUseCase) -> None:
    queries = tmp_path / "queries.jsonl"
    out_file = tmp_path / "results.jsonl"
    lines = [
        {"id": "q1", "question": "Q1", "language": "ru"},
        {"id": "q2", "question": "Q2", "language": "ru"},
    ]
    with queries.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")

    runner = CliRunner()
    result = runner.invoke(
        rag_commands,
        [
            "batch",
            "--queries",
            str(queries),
            "--out",
            str(out_file),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert out_file.exists()
    with out_file.open("r", encoding="utf-8") as handle:
        payloads = [json.loads(line) for line in handle if line.strip()]
    assert len(payloads) == 2
    assert [call.question for call in stub_use_case.calls] == ["Q1", "Q2"]
    assert payloads[0]["with_rag"]["text"] == "rag-1"
    assert payloads[1]["with_rag"]["text"] == "rag-2"
