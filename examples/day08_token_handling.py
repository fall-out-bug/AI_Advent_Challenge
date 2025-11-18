#!/usr/bin/env python
"""Day 8 · Token counting and text compression demo.

Purpose:
    Example demonstrating token counting, handling of long requests, and
    text compression/summarization when text exceeds model token limits.

Usage:
    $ PYTHONPATH=. python examples/day08_token_handling.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: This example intentionally imports from src.infrastructure to demonstrate
# how infrastructure components (TokenCounter) are used in practice. In a real
# application, this would be injected via dependency injection, but for this
# demo we use direct import to show the actual usage pattern.
from src.infrastructure.llm.token_counter import TokenCounter


@dataclass
class TokenAnalysis:
    """Token analysis result."""

    text: str
    token_count: int
    char_count: int
    tokens_per_char: float
    exceeds_limit: bool
    limit: int


class TokenHandlingAgent:
    """Agent that handles token counting and text compression."""

    def __init__(self, token_limit: int = 1000) -> None:
        """Initialise agent with token limit.

        Args:
            token_limit: Maximum token limit for model context.
        """
        self._token_limit = token_limit
        self._counter = TokenCounter()

    def analyze_text(self, text: str) -> TokenAnalysis:
        """Analyze text token usage.

        Args:
            text: Input text to analyze.

        Returns:
            TokenAnalysis with metrics.
        """
        token_count = self._counter.count_tokens(text)
        char_count = len(text)
        tokens_per_char = token_count / char_count if char_count > 0 else 0.0

        return TokenAnalysis(
            text=text,
            token_count=token_count,
            char_count=char_count,
            tokens_per_char=tokens_per_char,
            exceeds_limit=token_count > self._token_limit,
            limit=self._token_limit,
        )

    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit.

        Args:
            text: Input text.
            max_tokens: Maximum tokens allowed.

        Returns:
            Truncated text.
        """
        # Simple word-based truncation (can be improved with sentence-aware)
        words = text.split()
        truncated_words = []

        current_tokens = 0
        for word in words:
            word_tokens = self._counter.count_tokens(word + " ")
            if current_tokens + word_tokens <= max_tokens:
                truncated_words.append(word)
                current_tokens += word_tokens
            else:
                break

        return " ".join(truncated_words) + "..."

    def summarize_text(self, text: str, target_tokens: int) -> str:
        """Summarize text to target token count (simple heuristic).

        Args:
            text: Input text.
            target_tokens: Target token count.

        Returns:
            Summarized text.
        """
        # Simple heuristic: take first N sentences until target tokens
        sentences = text.split(". ")
        summarized = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._counter.count_tokens(sentence + ". ")
            if current_tokens + sentence_tokens <= target_tokens:
                summarized.append(sentence)
                current_tokens += sentence_tokens
            else:
                break

        summary = ". ".join(summarized)
        if summary and not summary.endswith("."):
            summary += "."

        return summary + " [Summary: original text truncated]"

    def compare_requests(self, short: str, long: str, overflow: str) -> None:
        """Compare token usage for different request sizes.

        Args:
            short: Short request text.
            long: Long request text.
            overflow: Text that exceeds token limit.
        """
        print("=" * 60)
        print("TOKEN HANDLING COMPARISON")
        print("=" * 60)
        print()

        # Short request
        short_analysis = self.analyze_text(short)
        print("-" * 60)
        print("SHORT REQUEST")
        print("-" * 60)
        print(f"Text: {short[:100]}...")
        print(f"Characters: {short_analysis.char_count}")
        print(f"Tokens: {short_analysis.token_count}")
        print(f"Tokens/char: {short_analysis.tokens_per_char:.3f}")
        print(f"Exceeds limit ({self._token_limit}): {short_analysis.exceeds_limit}")
        print()

        # Long request
        long_analysis = self.analyze_text(long)
        print("-" * 60)
        print("LONG REQUEST")
        print("-" * 60)
        print(f"Text: {long[:100]}...")
        print(f"Characters: {long_analysis.char_count}")
        print(f"Tokens: {long_analysis.token_count}")
        print(f"Tokens/char: {long_analysis.tokens_per_char:.3f}")
        print(f"Exceeds limit ({self._token_limit}): {long_analysis.exceeds_limit}")
        print()

        # Overflow request
        overflow_analysis = self.analyze_text(overflow)
        print("-" * 60)
        print("OVERFLOW REQUEST")
        print("-" * 60)
        print(f"Text: {overflow[:100]}...")
        print(f"Characters: {overflow_analysis.char_count}")
        print(f"Tokens: {overflow_analysis.token_count}")
        print(f"Tokens/char: {overflow_analysis.tokens_per_char:.3f}")
        print(f"Exceeds limit ({self._token_limit}): {overflow_analysis.exceeds_limit}")
        print()

        # Handle overflow
        if overflow_analysis.exceeds_limit:
            print("-" * 60)
            print("HANDLING OVERFLOW")
            print("-" * 60)

            # Option 1: Truncate
            truncated = self.truncate_text(overflow, self._token_limit)
            truncated_analysis = self.analyze_text(truncated)
            print("Option 1: Truncation")
            print(f"Truncated text: {truncated[:150]}...")
            print(f"Tokens after truncation: {truncated_analysis.token_count}")
            print()

            # Option 2: Summarize
            summary = self.summarize_text(overflow, self._token_limit)
            summary_analysis = self.analyze_text(summary)
            print("Option 2: Summarization")
            print(f"Summarized text: {summary[:150]}...")
            print(f"Tokens after summarization: {summary_analysis.token_count}")
            print()

        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Token limit: {self._token_limit}")
        print(f"Short request: {short_analysis.token_count} tokens (OK)")
        print(f"Long request: {long_analysis.token_count} tokens ({'OK' if not long_analysis.exceeds_limit else 'EXCEEDS'})")
        print(f"Overflow request: {overflow_analysis.token_count} tokens (EXCEEDS)")
        if overflow_analysis.exceeds_limit:
            print("\nWhen text exceeds limit:")
            print("  - Truncation: Cuts text at word boundary")
            print("  - Summarization: Keeps first sentences within limit")
        print()


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 8 demo."""
    # Sample texts
    short_text = "What is machine learning?"

    long_text = """Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience without being explicitly programmed.
    It focuses on the development of computer programs that can access data and use it
    to learn for themselves. The process of learning begins with observations or data,
    such as examples, direct experience, or instruction, in order to look for patterns
    in data and make better decisions in the future based on the examples that we provide.
    The primary aim is to allow the computers to learn automatically without human intervention
    or assistance and adjust actions accordingly."""

    overflow_text = """Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience without being explicitly programmed.
    It focuses on the development of computer programs that can access data and use it
    to learn for themselves. The process of learning begins with observations or data,
    such as examples, direct experience, or instruction, in order to look for patterns
    in data and make better decisions in the future based on the examples that we provide.
    The primary aim is to allow the computers to learn automatically without human intervention
    or assistance and adjust actions accordingly. Machine learning algorithms build mathematical
    models based on training data in order to make predictions or decisions without being
    explicitly programmed to perform the task. There are different types of machine learning:
    supervised learning, where the algorithm learns from labeled training data; unsupervised
    learning, where the algorithm finds patterns in unlabeled data; and reinforcement learning,
    where the algorithm learns through interaction with an environment. Deep learning, a subset
    of machine learning, uses neural networks with multiple layers to model and understand
    complex patterns in data. This approach has been particularly successful in image recognition,
    natural language processing, and speech recognition tasks. """ * 5  # Repeat to ensure overflow

    agent = TokenHandlingAgent(token_limit=1000)

    try:
        agent.compare_requests(short_text, long_text, overflow_text)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
