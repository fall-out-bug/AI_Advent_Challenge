"""Filesystem document collector for the embedding index pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence

from src.domain.embedding_index import DocumentCollector, DocumentPayload, DocumentRecord
from src.infrastructure.embedding_index.preprocessing.text_preprocessor import (
    TextPreprocessor,
)
from src.infrastructure.logging import get_logger


class FilesystemDocumentCollector(DocumentCollector):
    """Collect documents from local filesystem paths.

    Purpose:
        Traverse configured directories, converting supported files into
        ``DocumentPayload`` instances ready for preprocessing.
    """

    def __init__(self, preprocessor: TextPreprocessor) -> None:
        """Initialise collector."""
        self._preprocessor = preprocessor
        self._logger = get_logger(__name__)

    def collect(
        self,
        sources: Sequence[str],
        max_file_size_bytes: int,
        extra_tags: Mapping[str, str],
    ) -> Iterable[DocumentPayload]:
        """Yield document payloads from provided sources."""
        for root in self._resolve_sources(sources):
            tag = self._determine_source_tag(root)
            yield from self._collect_root(
                root=root,
                source_tag=tag,
                max_file_size_bytes=max_file_size_bytes,
                extra_tags=extra_tags,
            )

    def _resolve_sources(self, sources: Sequence[str]) -> Iterator[Path]:
        for raw in sources:
            path = Path(raw).expanduser()
            if not path.exists():
                self._logger.warning("source_missing", path=str(path))
                continue
            yield path

    def _collect_root(
        self,
        root: Path,
        source_tag: str,
        max_file_size_bytes: int,
        extra_tags: Mapping[str, str],
    ) -> Iterator[DocumentPayload]:
        for file_path in self._iter_files(root):
            if self._should_skip(file_path, max_file_size_bytes):
                continue
            if not self._preprocessor.supports(file_path):
                continue
            content = self._preprocessor.preprocess(file_path)
            if not content:
                continue
            record = self._build_record(
                file_path=file_path,
                source_tag=source_tag,
                content=content,
                extra_tags=extra_tags,
            )
            yield DocumentPayload(record=record, content=content)

    def _iter_files(self, root: Path) -> Iterator[Path]:
        if root.is_file():
            yield root
            return
        for file_path in root.rglob("*"):
            if file_path.is_file():
                yield file_path

    def _should_skip(self, path: Path, max_file_size_bytes: int) -> bool:
        try:
            size = path.stat().st_size
        except OSError:
            self._logger.warning("file_stat_failed", path=str(path))
            return True
        if size > max_file_size_bytes:
            self._logger.info(
                "file_skipped_due_to_size",
                path=str(path),
                size=size,
                limit=max_file_size_bytes,
            )
            return True
        return False

    def _build_record(
        self,
        file_path: Path,
        source_tag: str,
        content: str,
        extra_tags: Mapping[str, str],
    ) -> DocumentRecord:
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        document_id = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()
        tags = dict(extra_tags)
        tags.setdefault("source", source_tag)
        record = DocumentRecord(
            document_id=document_id,
            source_path=str(file_path.resolve()),
            source=source_tag,
            language=extra_tags.get("language", "ru"),
            sha256=sha256,
            tags=tags,
        )
        return replace(record, tags=dict(tags))

    def _determine_source_tag(self, root: Path) -> str:
        lower_parts = [part.lower() for part in root.parts]
        if "mlsd" in lower_parts:
            return "mlsd_lections"
        if "bigdata" in lower_parts:
            return "bigdata_lections"
        return root.name or "unknown"

