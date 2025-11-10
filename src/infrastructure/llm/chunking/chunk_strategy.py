"""Chunking strategy abstractions."""

from __future__ import annotations

from typing import Protocol

from .semantic_chunker import TextChunk


class ChunkStrategy(Protocol):
    """Protocol for text chunking strategies.

    Purpose:
        Defines interface for different chunking approaches
        (semantic, fixed-size, etc.).
    """

    def chunk_text(self, text: str) -> list[TextChunk]:
        """Split text into chunks.

        Args:
            text: Input text to chunk.

        Returns:
            List of TextChunk objects.
        """
        ...


class SemanticChunkStrategy:
    """Wrapper for SemanticChunker to implement ChunkStrategy protocol."""

    def __init__(self, chunker) -> None:
        """Initialize with SemanticChunker instance.

        Args:
            chunker: SemanticChunker instance.
        """
        self.chunker = chunker

    def chunk_text(self, text: str) -> list[TextChunk]:
        """Chunk text using semantic chunker.

        Args:
            text: Input text.

        Returns:
            List of TextChunk objects.
        """
        return self.chunker.chunk_text(text)


class FixedSizeChunkStrategy:
    """Fixed-size chunking strategy (character-based).

    Purpose:
        Simple chunking by fixed character count.
        Useful for cases where token counting is unavailable.

    Args:
        chunk_size: Number of characters per chunk (default: 1000).
        overlap_chars: Overlap characters between chunks (default: 100).
    """

    def __init__(self, chunk_size: int = 1000, overlap_chars: int = 100) -> None:
        self.chunk_size = chunk_size
        self.overlap_chars = overlap_chars

    def chunk_text(self, text: str) -> list[TextChunk]:
        """Chunk text by fixed character size.

        Args:
            text: Input text.

        Returns:
            List of TextChunk objects.
        """
        chunks: list[TextChunk] = []
        text_length = len(text)

        if text_length <= self.chunk_size:
            return [TextChunk(text=text, token_count=0, chunk_id=0)]

        start = 0
        chunk_id = 0

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_text = text[start:end]
            chunks.append(TextChunk(text=chunk_text, token_count=0, chunk_id=chunk_id))
            chunk_id += 1
            start = end - self.overlap_chars

            if start >= text_length:
                break

        return chunks
