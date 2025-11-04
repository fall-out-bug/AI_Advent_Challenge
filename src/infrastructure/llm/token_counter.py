"""Token counting utilities for LLM models using HuggingFace tokenizers.

Purpose:
    Provide consistent token counting to guide chunk sizes for summarization.
    Supports multiple models (Mistral, GPT, Claude) with optimized batch processing.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, TYPE_CHECKING

# Check if transformers is available at module import time
_transformers_available = False
AutoTokenizer = None

if TYPE_CHECKING:
    from transformers import AutoTokenizer  # type: ignore
else:
    try:
        from transformers import AutoTokenizer  # type: ignore
        _transformers_available = True
    except ImportError:
        _transformers_available = False

# Model mappings for different providers
MODEL_MAPPINGS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
    "gpt-4": "gpt2",  # Approximate using GPT-2 tokenizer
    "gpt-3.5": "gpt2",
    "claude": "gpt2",  # Approximate using GPT-2 tokenizer
}


@lru_cache(maxsize=3)
def _load_tokenizer(model_name: str):
    """Load and cache a tokenizer for the given model.

    Purpose:
        Caches up to 3 different tokenizers for efficient reuse.
        Falls back gracefully if transformers unavailable.

    Args:
        model_name: HuggingFace model identifier

    Returns:
        AutoTokenizer instance (or None if transformers unavailable)
    """
    if not _transformers_available or AutoTokenizer is None:
        return None
    try:
        return AutoTokenizer.from_pretrained(model_name, use_fast=True)
    except Exception:
        # Fallback to GPT-2 if model not found
        if model_name not in ["gpt2"]:
            try:
                return AutoTokenizer.from_pretrained("gpt2", use_fast=True)
            except Exception:
                return None
        return None


class TokenCounter:
    """Count tokens for text strings using an HF tokenizer.

    Purpose:
        Used by chunkers and summarizers to obey context limits.
        Supports multiple model types with optimized batch processing.

    Args:
        model_name: Model id to select a compatible tokenizer.
            Can be HuggingFace model name or provider name (mistral, gpt-4, etc.).
    """

    def __init__(self, model_name: str | None = None) -> None:
        env_model = os.getenv("LLM_MODEL", "")
        raw_model = model_name or env_model or "mistralai/Mistral-7B-Instruct-v0.2"

        # Normalize model name (support provider names)
        self.model_name = MODEL_MAPPINGS.get(raw_model.lower(), raw_model)
        self.tokenizer = (
            _load_tokenizer(self.model_name) if _transformers_available else None
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in a single text.

        Purpose:
            Efficiently count tokens for a single text string.
            Uses approximation fallback if tokenizer unavailable.

        Args:
            text: Input text

        Returns:
            Number of tokens including special tokens
            (approximated if transformers unavailable: ~4 chars per token)
        """
        if not self.tokenizer:
            # Fallback: approximate 1 token = 4 characters
            # This is a rough estimate for English/Russian
            return len(text) // 4

        try:
            return len(self.tokenizer.encode(text, add_special_tokens=True))
        except Exception:
            # If encoding fails, fallback to approximation
            return len(text) // 4

    def batch_count_tokens(self, texts: List[str]) -> List[int]:
        """Count tokens for a list of texts efficiently.

        Purpose:
            Batch processing is more efficient than individual calls.
            Handles empty lists and encoding errors gracefully.

        Args:
            texts: List of input strings

        Returns:
            List with token counts per input text
            (approximated if transformers unavailable)
        """
        if not texts:
            return []

        if not self.tokenizer:
            # Fallback: approximate 1 token = 4 characters
            return [len(text) // 4 for text in texts]

        try:
            # Batch encode is more efficient
            encoded = self.tokenizer(texts, add_special_tokens=True, padding=False)
            return [len(ids) for ids in encoded["input_ids"]]
        except Exception:
            # If batch encoding fails, fallback to approximation
            return [len(text) // 4 for text in texts]

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using character-based approximation.

        Purpose:
            Quick estimation without tokenizer (useful for fallback).
            More accurate than simple division for mixed languages.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Improved approximation:
        # - English: ~4 chars per token
        # - Russian: ~3 chars per token
        # - Mixed: average
        char_count = len(text)
        # Rough heuristic: count Cyrillic characters for Russian ratio
        cyrillic_count = sum(1 for c in text if "\u0400" <= c <= "\u04FF")
        russian_ratio = cyrillic_count / char_count if char_count > 0 else 0

        # Weighted average
        avg_chars_per_token = 4.0 * (1 - russian_ratio) + 3.0 * russian_ratio
        return int(char_count / avg_chars_per_token)

