"""Tests for FilesystemDocumentCollector."""

from __future__ import annotations

from pathlib import Path

from src.infrastructure.embedding_index.collectors.filesystem_collector import (
    FilesystemDocumentCollector,
)
from src.infrastructure.embedding_index.preprocessing.text_preprocessor import (
    TextPreprocessor,
)


def test_collect_yields_payloads(tmp_path: Path) -> None:
    """Ensure collector yields document payloads for supported files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "sample.md"
    file_path.write_text("Hello world", encoding="utf-8")

    collector = FilesystemDocumentCollector(preprocessor=TextPreprocessor())
    payloads = list(
        collector.collect(
            sources=[str(docs_dir)],
            max_file_size_bytes=1024,
            extra_tags={"stage": "19", "language": "ru"},
        )
    )

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload.record.source == "docs"
    assert payload.record.tags["stage"] == "19"
    assert payload.content == "Hello world"


def test_collect_skips_large_files(tmp_path: Path) -> None:
    """Ensure files exceeding size limit are skipped."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    large_file = docs_dir / "large.md"
    large_file.write_text("x" * 2048, encoding="utf-8")

    collector = FilesystemDocumentCollector(preprocessor=TextPreprocessor())
    payloads = list(
        collector.collect(
            sources=[str(docs_dir)],
            max_file_size_bytes=1024,
            extra_tags={"stage": "19", "language": "ru"},
        )
    )

    assert payloads == []

