#!/usr/bin/env python
"""Day 4 · Temperature comparison demo.

Purpose:
    Example demonstrating the effect of temperature parameter on LLM output.
    Runs the same query with temperatures 0, 0.7, and 1.2, then compares
    results for accuracy, creativity, and diversity.

Usage:
    $ python examples/day04_temperature.py "Explain quantum computing in simple terms"
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class TemperatureResult:
    """Result of LLM call with specific temperature."""

    temperature: float
    response: str
    tokens_used: int
    creativity_score: float  # 0-1, estimated from variance


class TemperatureAgent:
    """Agent that tests LLM responses across different temperature values."""

    def __init__(self, llm_url: str | None = None) -> None:
        """Initialise agent with LLM endpoint.

        Args:
            llm_url: Base URL for LLM API. Defaults to env or localhost.
        """
        self._llm_url = (
            llm_url
            or os.environ.get("LLM_URL")
            or "http://localhost:8000/v1"
        ).rstrip("/")
        self._client = httpx.Client(timeout=60.0)

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def generate_response(
        self, prompt: str, temperature: float
    ) -> TemperatureResult:
        """Generate response with specific temperature.

        Args:
            prompt: User prompt.
            temperature: Sampling temperature (0.0-2.0).

        Returns:
            TemperatureResult with response and metadata.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 256,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)

        # Estimate creativity: count unique words / total words
        words = content.lower().split()
        unique_words = len(set(words))
        creativity_score = unique_words / len(words) if words else 0.0

        return TemperatureResult(
            temperature=temperature,
            response=content,
            tokens_used=tokens_used,
            creativity_score=creativity_score,
        )

    def compare_temperatures(
        self, prompt: str, temperatures: list[float]
    ) -> list[TemperatureResult]:
        """Run same prompt with multiple temperatures.

        Args:
            prompt: User prompt to test.
            temperatures: List of temperature values to test.

        Returns:
            List of TemperatureResult for each temperature.
        """
        results = []
        for temp in temperatures:
            result = self.generate_response(prompt, temp)
            results.append(result)
        return results


def format_comparison(results: list[TemperatureResult]) -> str:
    """Format temperature comparison results.

    Args:
        results: List of TemperatureResult objects.

    Returns:
        Formatted comparison string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("TEMPERATURE COMPARISON")
    lines.append("=" * 60)
    lines.append("")

    for result in results:
        lines.append(f"Temperature: {result.temperature}")
        lines.append(f"Tokens used: {result.tokens_used}")
        lines.append(f"Creativity score: {result.creativity_score:.2f}")
        lines.append("Response:")
        lines.append(result.response[:200] + ("..." if len(result.response) > 200 else ""))
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Most deterministic (T=0.0): Best for factual/accurate answers")
    lines.append(f"Balanced (T=0.7): Good balance of accuracy and creativity")
    lines.append(f"Most creative (T=1.2+): Best for creative/exploratory tasks")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 4 demo."""
    args = sys.argv[1:] if argv is None else argv

    prompt = (
        " ".join(args) if args
        else "Explain quantum computing in simple terms"
    )

    agent = TemperatureAgent()

    try:
        temperatures = [0.0, 0.7, 1.2]
        print(f"Testing prompt: '{prompt}'")
        print(f"Temperatures: {temperatures}\n")

        results = agent.compare_temperatures(prompt, temperatures)
        comparison = format_comparison(results)
        print(comparison)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        agent.close()


if __name__ == "__main__":
    raise SystemExit(main())
