"""Sentence-aware text chunker with improved language support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from src.infrastructure.llm.token_counter import TokenCounter

try:
    from prometheus_client import Histogram, Summary  # type: ignore

    _chunking_duration = Histogram(
        "chunking_duration_seconds",
        "Time spent chunking text",
    )
    _chunk_count = Summary(
        "chunk_count_total",
        "Total number of chunks created",
    )
    _avg_tokens_per_chunk = Summary(
        "avg_tokens_per_chunk",
        "Average tokens per chunk",
    )
except Exception:  # pragma: no cover - metrics are optional
    _chunking_duration = None
    _chunk_count = None
    _avg_tokens_per_chunk = None


@dataclass
class TextChunk:
    """A single text chunk with metadata.

    Args:
        text: Chunk text content.
        token_count: Number of tokens in chunk.
        chunk_id: Sequential chunk identifier.
    """

    text: str
    token_count: int
    chunk_id: int


class SemanticChunker:
    """Chunk text at sentence boundaries with configurable overlap.

    Purpose:
        Split long texts into chunks that respect model context limits
        while preserving sentence boundaries and limited overlap for continuity.
        Supports Russian, English, and other languages.

    Args:
        token_counter: TokenCounter instance for accurate token counting.
        max_tokens: Maximum tokens per chunk (default: 3000).
        overlap_tokens: Target tokens to keep from previous chunk (default: 200).
        language: Primary language for sentence detection (default: "auto").
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        max_tokens: int = 3000,
        overlap_tokens: int = 200,
        language: str = "auto",
    ) -> None:
        self.token_counter = token_counter
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.language = language

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using improved regex patterns.

        Purpose:
            Detect sentence boundaries for Russian, English, and other languages.
            Handles various punctuation marks and sentence start patterns.

        Args:
            text: Input text to split.

        Returns:
            List of sentence strings (non-empty).
        """
        # Improved pattern for multiple languages:
        # - Russian: ! ? . … followed by space and capital letter or quote
        # - English: ! ? . followed by space and capital letter
        # - Handles quotes: « " ' followed by capital letter
        # - Handles abbreviations (basic): doesn't split on single capital after period

        # Pattern for sentence endings:
        # [.!?…] followed by optional space/newline, then capital letter or quote
        pattern = r"(?<=[.!?…])\s+(?=[А-ЯA-Z«\"']|\n[А-ЯA-Z«\"'])"

        sentences = re.split(pattern, text.strip())
        # Clean and filter empty sentences
        cleaned = [s.strip() for s in sentences if s and s.strip()]

        # Additional cleanup: merge sentences that are clearly part of one thought
        # (e.g., "Dr. Smith" should not be split)
        merged: List[str] = []
        for sent in cleaned:
            if merged and len(sent) < 10 and sent[0].islower():
                # Likely continuation (abbreviation or quote)
                merged[-1] += " " + sent
            else:
                merged.append(sent)

        return merged

    def chunk_text(self, text: str) -> List[TextChunk]:
        """Split text into chunks with overlap.

        Purpose:
            Creates chunks respecting max_tokens limit while preserving
            sentence boundaries and maintaining overlap for context continuity.

        Args:
            text: Input text to chunk.

        Returns:
            List of TextChunk objects with metadata.

        Raises:
            ValueError: If a single sentence exceeds max_tokens.
        """
        import time

        start_time = time.time()

        total_tokens = self.token_counter.count_tokens(text)
        if total_tokens <= self.max_tokens:
            chunk = [TextChunk(text=text, token_count=total_tokens, chunk_id=0)]
            duration = time.time() - start_time

            if _chunking_duration:
                _chunking_duration.observe(duration)
            if _chunk_count:
                _chunk_count.observe(1)
            if _avg_tokens_per_chunk:
                _avg_tokens_per_chunk.observe(total_tokens)

            return chunk

        sentences = self._split_sentences(text)
        sentence_tokens = self.token_counter.batch_count_tokens(sentences)

        chunks: List[TextChunk] = []
        current_sentences: List[str] = []
        current_tokens = 0

        for idx, (sent, tok) in enumerate(zip(sentences, sentence_tokens)):
            if tok > self.max_tokens:
                # If sentence is too long, split it by words
                # Use print for now since logger may not be available
                words = sent.split()
                current_word_chunk: List[str] = []
                current_word_tokens = 0
                
                for word in words:
                    word_tokens = self.token_counter.count_tokens(word)
                    if current_word_tokens + word_tokens > self.max_tokens and current_word_chunk:
                        # Create chunk from words
                        word_chunk_text = " ".join(current_word_chunk)
                        chunks.append(
                            TextChunk(
                                text=word_chunk_text,
                                token_count=current_word_tokens,
                                chunk_id=len(chunks),
                            )
                        )
                        current_word_chunk = [word]
                        current_word_tokens = word_tokens
                    else:
                        current_word_chunk.append(word)
                        current_word_tokens += word_tokens
                
                # Add remaining words to current_sentences as a pseudo-sentence
                if current_word_chunk:
                    sent = " ".join(current_word_chunk)
                    tok = current_word_tokens
                else:
                    continue  # Skip empty sentence

            if current_tokens + tok > self.max_tokens and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    TextChunk(
                        text=chunk_text, token_count=current_tokens, chunk_id=len(chunks)
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

        duration = time.time() - start_time
        avg_tokens = sum(c.token_count for c in chunks) / len(chunks) if chunks else 0

        if _chunking_duration:
            _chunking_duration.observe(duration)
        if _chunk_count:
            _chunk_count.observe(len(chunks))
        if _avg_tokens_per_chunk:
            _avg_tokens_per_chunk.observe(avg_tokens)

        return chunks
