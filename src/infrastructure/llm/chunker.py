"""Sentence-aware text chunker with token-based limits and overlap.

Purpose:
    Split long texts into chunks that respect model context limits while
    preserving sentence boundaries and limited overlap for continuity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .token_counter import TokenCounter


@dataclass
class TextChunk:
    """A single text chunk with metadata useful for logging and stats."""

    text: str
    token_count: int
    chunk_id: int


class SemanticChunker:
    """Chunk text at sentence boundaries with configurable overlap.

    Args:
        token_counter: TokenCounter instance for accurate token counting.
        max_tokens: Maximum tokens per chunk.
        overlap_tokens: Target tokens to keep from the end of the previous chunk.
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        max_tokens: int = 3000,
        overlap_tokens: int = 200,
    ) -> None:
        self.token_counter = token_counter
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def _split_sentences(self, text: str) -> List[str]:
        # Russian/English aware end punctuation with lookarounds
        pattern = r"(?<=[.!?…])\s+(?=[А-ЯA-Z«\"])"
        sentences = re.split(pattern, text.strip())
        return [s.strip() for s in sentences if s and s.strip()]

    def chunk_text(self, text: str) -> List[TextChunk]:
        """Split text into chunks with overlap.

        Raises:
            ValueError: If a single sentence exceeds max_tokens.
        """
        total_tokens = self.token_counter.count_tokens(text)
        if total_tokens <= self.max_tokens:
            return [TextChunk(text=text, token_count=total_tokens, chunk_id=0)]

        sentences = self._split_sentences(text)
        sentence_tokens = self.token_counter.batch_count_tokens(sentences)

        chunks: List[TextChunk] = []
        current_sentences: List[str] = []
        current_tokens = 0

        for idx, (sent, tok) in enumerate(zip(sentences, sentence_tokens)):
            if tok > self.max_tokens:
                raise ValueError(
                    f"Sentence {idx} has {tok} tokens, exceeds max {self.max_tokens}."
                )

            if current_tokens + tok > self.max_tokens and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        token_count=current_tokens,
                        chunk_id=len(chunks),
                    )
                )

                # Build overlap from the end backward
                overlap_sents: List[str] = []
                overlap_sum = 0
                # Walk back through the sentences just added
                walk_tokens = self.token_counter.batch_count_tokens(current_sentences)
                for s, t in zip(reversed(current_sentences), reversed(walk_tokens)):
                    if overlap_sum + t <= self.overlap_tokens:
                        overlap_sents.insert(0, s)
                        overlap_sum += t
                    else:
                        break

                current_sentences = overlap_sents
                current_tokens = overlap_sum

            current_sentences.append(sent)
            current_tokens += tok

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                TextChunk(
                    text=chunk_text, token_count=current_tokens, chunk_id=len(chunks)
                )
            )

        return chunks
