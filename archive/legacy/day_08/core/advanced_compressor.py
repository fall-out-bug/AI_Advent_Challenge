"""
Advanced text compression strategies.

This module implements multiple compression strategies including
LLM-based summarization, extractive summarization with TF-IDF,
and semantic chunking with importance scoring.
"""

import asyncio
import re
from typing import Optional, Protocol

from models.data_models import CompressionResult


class CompressionStrategy(Protocol):
    """Strategy interface for compression."""

    def compress(
        self, text: str, max_tokens: int, model_name: str
    ) -> CompressionResult:
        """Compress text using this strategy."""
        ...


class SummarizationCompressor:
    """
    LLM-based summarization compressor.

    Uses a fast model (TinyLlama) to summarize long text,
    providing high-quality compression with semantic understanding.
    """

    def __init__(self, model_client, token_counter):
        """
        Initialize summarization compressor.

        Args:
            model_client: Client for making model requests
            token_counter: Token counter for accurate counting
        """
        self.model_client = model_client
        self.token_counter = token_counter

    async def compress(
        self, text: str, max_tokens: int, model_name: str
    ) -> CompressionResult:
        """
        Summarize text using TinyLlama (fastest model).

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the target model

        Returns:
            CompressionResult: Result of summarization
        """
        original_tokens = self.token_counter.count_tokens(text, model_name).count

        # Calculate target summary length
        target_words = int(max_tokens / 1.3)  # Convert tokens to words

        # Create summarization prompt
        summary_prompt = f"""Summarize the following text in {target_words} words or less. 
Keep the most important information and key points:

{text}

Summary:"""

        try:
            # Use TinyLlama for fast summarization
            response = await self.model_client.make_request(
                model_name="tinyllama",
                prompt=summary_prompt,
                max_tokens=max_tokens // 2,  # Conservative output limit
                temperature=0.3,  # Lower temperature for more focused summaries
            )

            compressed_text = response.response.strip()

            # Clean up the response (remove prompt artifacts)
            compressed_text = self._clean_summary(compressed_text)

            compressed_tokens = self.token_counter.count_tokens(
                compressed_text, model_name
            ).count

            return CompressionResult(
                original_text=text,
                compressed_text=compressed_text,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=compressed_tokens / original_tokens
                if original_tokens > 0
                else 1.0,
                strategy_used="llm_summarization",
            )

        except Exception as e:
            # Fallback to original text if summarization fails
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used="llm_summarization_failed",
            )

    def _clean_summary(self, summary: str) -> str:
        """
        Clean up summary text by removing common artifacts.

        Args:
            summary: Raw summary text

        Returns:
            str: Cleaned summary text
        """
        # Remove common prompt artifacts
        artifacts = [
            "Summary:",
            "Here's a summary:",
            "The summary is:",
            "In summary:",
            "To summarize:",
        ]

        cleaned = summary
        for artifact in artifacts:
            if cleaned.startswith(artifact):
                cleaned = cleaned[len(artifact) :].strip()

        return cleaned


class ExtractiveCompressor:
    """
    TF-IDF based extractive summarization.

    Extracts the most important sentences using TF-IDF scoring,
    providing fast compression without requiring model inference.
    """

    def __init__(self, token_counter):
        """
        Initialize extractive compressor.

        Args:
            token_counter: Token counter for accurate counting
        """
        self.token_counter = token_counter

    def compress(
        self, text: str, max_tokens: int, model_name: str
    ) -> CompressionResult:
        """
        Extract most important sentences using TF-IDF.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            CompressionResult: Result of extraction
        """
        original_tokens = self.token_counter.count_tokens(text, model_name).count

        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 3:
            # Too few sentences, return original
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used="extractive_tfidf",
            )

        try:
            # Calculate TF-IDF scores
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Use TF-IDF to score sentences
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=1000,
                ngram_range=(1, 2),  # Include bigrams
            )
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Score sentences by sum of TF-IDF values
            scores = np.array(tfidf_matrix.sum(axis=1)).flatten()

            # Calculate target sentences
            max_words = int(max_tokens / 1.3)
            selected_sentences = []
            current_words = 0

            # Sort by score, take top sentences
            for idx in np.argsort(scores)[::-1]:
                sent_words = len(sentences[idx].split())
                if current_words + sent_words <= max_words:
                    selected_sentences.append((idx, sentences[idx]))
                    current_words += sent_words
                else:
                    break

            # Sort by original order to maintain coherence
            selected_sentences.sort(key=lambda x: x[0])
            compressed_text = " ".join([s[1] for s in selected_sentences])

            compressed_tokens = self.token_counter.count_tokens(
                compressed_text, model_name
            ).count

            return CompressionResult(
                original_text=text,
                compressed_text=compressed_text,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                compression_ratio=compressed_tokens / original_tokens
                if original_tokens > 0
                else 1.0,
                strategy_used="extractive_tfidf",
            )

        except ImportError:
            # Fallback if sklearn is not available
            return self._fallback_extraction(
                text, max_tokens, model_name, original_tokens
            )
        except Exception as e:
            # Fallback on any error
            return self._fallback_extraction(
                text, max_tokens, model_name, original_tokens
            )

    def _fallback_extraction(
        self, text: str, max_tokens: int, model_name: str, original_tokens: int
    ) -> CompressionResult:
        """
        Fallback extraction using simple sentence scoring.

        Args:
            text: Input text
            max_tokens: Maximum tokens
            model_name: Model name
            original_tokens: Original token count

        Returns:
            CompressionResult: Fallback result
        """
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 3:
            compressed_text = text
        else:
            # Simple scoring: longer sentences with more unique words
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                words = sentence.split()
                unique_words = len(set(word.lower() for word in words))
                score = unique_words / len(words) if words else 0
                scored_sentences.append((score, i, sentence))

            # Sort by score and select top sentences
            scored_sentences.sort(key=lambda x: x[0], reverse=True)

            max_words = int(max_tokens / 1.3)
            selected = []
            current_words = 0

            for score, idx, sentence in scored_sentences:
                sent_words = len(sentence.split())
                if current_words + sent_words <= max_words:
                    selected.append((idx, sentence))
                    current_words += sent_words

            # Sort by original order
            selected.sort(key=lambda x: x[0])
            compressed_text = " ".join([s[1] for s in selected])

        compressed_tokens = self.token_counter.count_tokens(
            compressed_text, model_name
        ).count

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens
            if original_tokens > 0
            else 1.0,
            strategy_used="extractive_fallback",
        )


class SemanticChunker:
    """
    Semantic chunking with importance scoring.

    Chunks text by semantic boundaries (paragraphs) and keeps
    the most important chunks based on content density.
    """

    def __init__(self, token_counter):
        """
        Initialize semantic chunker.

        Args:
            token_counter: Token counter for accurate counting
        """
        self.token_counter = token_counter

    def compress(
        self, text: str, max_tokens: int, model_name: str
    ) -> CompressionResult:
        """
        Chunk by semantic boundaries and keep important chunks.

        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model

        Returns:
            CompressionResult: Result of semantic chunking
        """
        original_tokens = self.token_counter.count_tokens(text, model_name).count

        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            paragraphs = [text]

        if len(paragraphs) <= 2:
            # Too few paragraphs, return original
            return CompressionResult(
                original_text=text,
                compressed_text=text,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                strategy_used="semantic_chunking",
            )

        # Score paragraphs by content density and length
        scored_chunks = []
        for para in paragraphs:
            words = para.split()
            if not words:
                continue

            # Score based on:
            # 1. Length (longer paragraphs often more important)
            # 2. Unique word density (more diverse vocabulary)
            # 3. Technical term density (words longer than 5 chars)
            unique_words = len(set(word.lower() for word in words))
            technical_words = len([w for w in words if len(w) > 5])

            length_score = min(len(words) / 100, 1.0)  # Normalize to 0-1
            diversity_score = unique_words / len(words)
            technical_score = technical_words / len(words)

            # Combined score
            score = length_score * 0.4 + diversity_score * 0.3 + technical_score * 0.3
            scored_chunks.append((score, para))

        # Sort by score and select chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        selected = []
        current_tokens = 0

        for score, chunk in scored_chunks:
            chunk_tokens = self.token_counter.count_tokens(chunk, model_name).count
            if current_tokens + chunk_tokens <= max_tokens:
                selected.append(chunk)
                current_tokens += chunk_tokens
            else:
                break

        # If we have space, add chunks in original order
        if current_tokens < max_tokens * 0.8:  # If we used less than 80%
            remaining_chunks = [
                (score, chunk)
                for score, chunk in scored_chunks
                if chunk not in selected
            ]
            remaining_chunks.sort(
                key=lambda x: paragraphs.index(x[1])
            )  # Sort by original order

            for score, chunk in remaining_chunks:
                chunk_tokens = self.token_counter.count_tokens(chunk, model_name).count
                if current_tokens + chunk_tokens <= max_tokens:
                    selected.append(chunk)
                    current_tokens += chunk_tokens

        compressed_text = "\n\n".join(selected)
        compressed_tokens = self.token_counter.count_tokens(
            compressed_text, model_name
        ).count

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens
            if original_tokens > 0
            else 1.0,
            strategy_used="semantic_chunking",
        )
