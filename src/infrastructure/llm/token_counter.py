"""Token counting utilities for LLM models using HuggingFace tokenizers.

Purpose:
    Provide consistent token counting to guide chunk sizes for summarization.

"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from transformers import AutoTokenizer  # type: ignore


@lru_cache(maxsize=1)
def _load_tokenizer(model_name: str) -> AutoTokenizer:
    """Load and cache a tokenizer for the given model.

    Args:
        model_name: HuggingFace model identifier

    Returns:
        AutoTokenizer instance
    """
    return AutoTokenizer.from_pretrained(model_name, use_fast=True)


class TokenCounter:
    """Count tokens for text strings using an HF tokenizer.

    Purpose:
        Used by chunkers and summarizers to obey context limits.

    Args:
        model_name: Model id to select a compatible tokenizer.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
        self.tokenizer = _load_tokenizer(self.model_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in a single text.

        Args:
            text: Input text

        Returns:
            Number of tokens including special tokens
        """
        return len(self.tokenizer.encode(text, add_special_tokens=True))

    def batch_count_tokens(self, texts: List[str]) -> List[int]:
        """Count tokens for a list of texts efficiently.

        Args:
            texts: List of input strings

        Returns:
            List with token counts per input text
        """
        encoded = self.tokenizer(texts, add_special_tokens=True)
        return [len(ids) for ids in encoded["input_ids"]]


