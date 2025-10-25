"""
Accurate token counting module using HuggingFace tokenizers.

This module provides precise token counting using actual model tokenizers,
replacing the simple word-based estimation with real tokenization.
"""

from typing import Dict, Optional

from transformers import AutoTokenizer

from models.data_models import TokenInfo


class AccurateTokenCounter:
    """
    Accurate token counter using HuggingFace tokenizers.

    Provides precise token counting by using the actual tokenizers
    from HuggingFace Transformers library, cached for performance.
    """

    def __init__(self):
        """Initialize with empty tokenizer cache."""
        self._tokenizers: Dict[str, AutoTokenizer] = {}
        self._model_map = {
            "starcoder": "bigcode/starcoder2-7b",
            "mistral": "mistralai/Mistral-7B-v0.1",
            "qwen": "Qwen/Qwen-7B",
            "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        }

    def _get_tokenizer(self, model_name: str) -> AutoTokenizer:
        """
        Lazy load and cache tokenizer for model.

        Args:
            model_name: Name of the model

        Returns:
            AutoTokenizer: Cached tokenizer instance

        Raises:
            ValueError: If model name is not supported
        """
        if model_name not in self._model_map:
            raise ValueError(f"Unsupported model: {model_name}")

        if model_name not in self._tokenizers:
            model_id = self._model_map[model_name]
            try:
                self._tokenizers[model_name] = AutoTokenizer.from_pretrained(
                    model_id, trust_remote_code=True
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load tokenizer for {model_name}: {e}")

        return self._tokenizers[model_name]

    def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens using actual tokenizer.

        Args:
            text: Input text to count tokens for
            model_name: Name of the model (default: "starcoder")

        Returns:
            TokenInfo: Accurate token count and metadata
        """
        if not text:
            return TokenInfo(count=0, estimated_cost=0.0, model_name=model_name)

        try:
            tokenizer = self._get_tokenizer(model_name)
            tokens = tokenizer.encode(text, add_special_tokens=False)

            return TokenInfo(
                count=len(tokens),
                estimated_cost=0.0,  # Local models have no cost
                model_name=model_name,
            )
        except Exception as e:
            # Fallback to simple estimation if tokenizer fails
            word_count = len(text.split())
            token_count = int(word_count * 1.3)

            return TokenInfo(
                count=token_count, estimated_cost=0.0, model_name=model_name
            )

    def get_available_models(self) -> list[str]:
        """
        Get list of supported model names.

        Returns:
            list[str]: List of supported model names
        """
        return list(self._model_map.keys())

    def add_model(self, model_name: str, model_id: str) -> None:
        """
        Add support for additional model.

        Args:
            model_name: Name to use for the model
            model_id: HuggingFace model identifier
        """
        self._model_map[model_name] = model_id
        # Clear cache for this model if it exists
        if model_name in self._tokenizers:
            del self._tokenizers[model_name]

    def clear_cache(self) -> None:
        """Clear tokenizer cache to free memory."""
        self._tokenizers.clear()
