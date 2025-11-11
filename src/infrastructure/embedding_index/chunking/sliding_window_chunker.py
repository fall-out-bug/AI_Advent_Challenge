"""Sliding window chunker for document indexing."""

from __future__ import annotations

from dataclasses import replace
from typing import List

from src.domain.embedding_index import Chunker, ChunkingSettings, DocumentChunk, DocumentPayload


class SlidingWindowChunker(Chunker):
    """Generate overlapping chunks based on token windows.

    Purpose:
        Produce deterministic chunks that respect configured token size and
        overlap while preserving source order.
    """

    def build_chunks(
        self,
        payload: DocumentPayload,
        settings: ChunkingSettings,
    ) -> List[DocumentChunk]:
        """Split payload into ordered chunks."""
        tokens = self._tokenize(payload.content)
        if not tokens:
            return []
        windows = self._generate_windows(tokens, settings)
        return self._build_chunks(payload, windows, settings)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text using whitespace splitting."""
        return [token for token in text.split() if token.strip()]

    def _generate_windows(
        self,
        tokens: List[str],
        settings: ChunkingSettings,
    ) -> List[List[str]]:
        """Generate token windows using configured overlap."""
        window: List[List[str]] = []
        step = settings.chunk_size_tokens - settings.chunk_overlap_tokens
        for start in range(0, len(tokens), max(step, 1)):
            end = min(start + settings.chunk_size_tokens, len(tokens))
            slice_tokens = tokens[start:end]
            if len(slice_tokens) < settings.min_chunk_tokens and window:
                window[-1].extend(slice_tokens)
                break
            window.append(slice_tokens)
            if end == len(tokens):
                break
        return window

    def _build_chunks(
        self,
        payload: DocumentPayload,
        windows: List[List[str]],
        settings: ChunkingSettings,
    ) -> List[DocumentChunk]:
        """Convert token windows into DocumentChunk instances."""
        chunks: List[DocumentChunk] = []
        for index, tokens in enumerate(windows):
            text = " ".join(tokens)
            chunk_id = f"{payload.record.document_id}:{index:04d}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=payload.record.document_id,
                ordinal=index,
                text=text,
                token_count=len(tokens),
                metadata={"chunk_strategy": "sliding_window"},
            )
            chunks.append(replace(chunk, metadata=dict(chunk.metadata or {})))
        return chunks
