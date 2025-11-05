"""LLM client Protocol interface."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Protocol for LLM client implementations.

    Purpose:
        Defines the interface that all LLM clients must implement.
        Supports both single and batch generation.
    """

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate a text completion for a prompt.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (0.0-2.0). Higher = more creative.
            max_tokens: Maximum tokens to generate.
            stop_sequences: Optional list of stop sequences to end generation.

        Returns:
            Generated text completion.

        Raises:
            Exception: On generation errors (implementation-specific).
        """
        ...

    async def batch_generate(
        self,
        prompts: list[str],
        temperature: float = 0.2,
        max_tokens: int = 256,
        stop_sequences: list[str] | None = None,
    ) -> list[str]:
        """Generate completions for multiple prompts in parallel.

        Args:
            prompts: List of input prompts.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per completion.
            stop_sequences: Optional stop sequences.

        Returns:
            List of generated texts (one per prompt).

        Raises:
            Exception: On batch generation errors.
        """
        ...
