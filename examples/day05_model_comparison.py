#!/usr/bin/env python
"""Day 5 · Model version comparison demo.

Purpose:
    Example demonstrating comparison of different LLM models on the same query.
    Measures response time, token count, cost (if applicable), and response
    quality. Compares models from different categories (small, medium, large).

Usage:
    $ python examples/day05_model_comparison.py "What is machine learning?"
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ModelResult:
    """Result of LLM call with specific model."""

    model: str
    response: str
    response_time_ms: float
    tokens_prompt: int
    tokens_completion: int
    tokens_total: int
    cost_usd: float  # 0.0 if unknown/free
    quality_score: float  # 0-1, estimated from response length/coherence


# Model pricing (example rates, adjust based on actual provider)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
    "gpt-3.5-turbo": {"prompt": 0.0015 / 1000, "completion": 0.002 / 1000},
    "mistral-7b-instruct": {"prompt": 0.0, "completion": 0.0},  # Free/local
    "llama-2-7b": {"prompt": 0.0, "completion": 0.0},  # Free/local
}


class ModelComparisonAgent:
    """Agent that compares different LLM models on the same query."""

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
        self._client = httpx.Client(timeout=120.0)

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def test_model(
        self, prompt: str, model: str, category: str = "unknown"
    ) -> ModelResult:
        """Test a specific model with the prompt.

        Args:
            prompt: User prompt.
            model: Model identifier.
            category: Model category (small/medium/large).

        Returns:
            ModelResult with metrics.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        start_time = time.time()

        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 512,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()

        elapsed_ms = (time.time() - start_time) * 1000

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_prompt = usage.get("prompt_tokens", 0)
        tokens_completion = usage.get("completion_tokens", 0)
        tokens_total = usage.get("total_tokens", tokens_prompt + tokens_completion)

        # Calculate cost
        pricing = MODEL_PRICING.get(model, {"prompt": 0.0, "completion": 0.0})
        cost_usd = (
            tokens_prompt * pricing["prompt"]
            + tokens_completion * pricing["completion"]
        )

        # Estimate quality: normalized by length and coherence (simple heuristic)
        word_count = len(content.split())
        quality_score = min(1.0, word_count / 100.0)  # Rough estimate

        return ModelResult(
            model=model,
            response=content,
            response_time_ms=elapsed_ms,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=tokens_total,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def compare_models(
        self, prompt: str, models: list[str]
    ) -> list[ModelResult]:
        """Compare multiple models on the same prompt.

        Args:
            prompt: User prompt to test.
            models: List of model identifiers.

        Returns:
            List of ModelResult for each model.
        """
        results = []
        for model in models:
            try:
                result = self.test_model(prompt, model)
                results.append(result)
            except Exception as e:
                print(f"Error testing {model}: {e}", file=sys.stderr)
        return results


def format_comparison(results: list[ModelResult]) -> str:
    """Format model comparison results.

    Args:
        results: List of ModelResult objects.

    Returns:
        Formatted comparison string.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("MODEL COMPARISON")
    lines.append("=" * 80)
    lines.append("")

    # Table header
    lines.append(
        f"{'Model':<25} {'Time (ms)':<12} {'Tokens':<10} {'Cost ($)':<12} {'Quality':<10}"
    )
    lines.append("-" * 80)

    for result in results:
        cost_str = f"${result.cost_usd:.6f}" if result.cost_usd > 0 else "Free"
        lines.append(
            f"{result.model:<25} {result.response_time_ms:>10.1f}  "
            f"{result.tokens_total:>8}  {cost_str:<12} {result.quality_score:>8.2f}"
        )

    lines.append("")
    lines.append("=" * 80)
    lines.append("DETAILED RESULTS")
    lines.append("=" * 80)
    lines.append("")

    for result in results:
        lines.append(f"Model: {result.model}")
        lines.append(f"Response time: {result.response_time_ms:.1f} ms")
        lines.append(f"Tokens: {result.tokens_prompt} prompt + {result.tokens_completion} completion = {result.tokens_total} total")
        lines.append(f"Cost: ${result.cost_usd:.6f}" if result.cost_usd > 0 else "Cost: Free")
        lines.append(f"Quality score: {result.quality_score:.2f}")
        lines.append("Response:")
        lines.append(result.response[:300] + ("..." if len(result.response) > 300 else ""))
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("=" * 80)
    if results:
        fastest = min(results, key=lambda r: r.response_time_ms)
        cheapest = min(results, key=lambda r: r.cost_usd if r.cost_usd > 0 else float('inf'))
        highest_quality = max(results, key=lambda r: r.quality_score)

        lines.append(f"Fastest: {fastest.model} ({fastest.response_time_ms:.1f} ms)")
        lines.append(f"Cheapest: {cheapest.model} (${cheapest.cost_usd:.6f})" if cheapest.cost_usd > 0 else f"Cheapest: {cheapest.model} (Free)")
        lines.append(f"Highest quality: {highest_quality.model} (score: {highest_quality.quality_score:.2f})")

    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 5 demo."""
    args = sys.argv[1:] if argv is None else argv

    prompt = (
        " ".join(args) if args
        else "What is machine learning?"
    )

    # Models from different categories (adjust based on available models)
    models = [
        "gpt-3.5-turbo",  # Medium (fast, affordable)
        "gpt-4",  # Large (slow, expensive, high quality)
        "mistral-7b-instruct",  # Small (fast, free, local)
    ]

    agent = ModelComparisonAgent()

    try:
        print(f"Testing prompt: '{prompt}'")
        print(f"Models: {', '.join(models)}\n")

        results = agent.compare_models(prompt, models)

        if not results:
            print("No results obtained. Check model availability.", file=sys.stderr)
            return 1

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

