#!/usr/bin/env python
"""Day 6 · Chain of Thought (CoT) comparison demo.

Purpose:
    Example demonstrating the effect of Chain of Thought prompting on LLM
    reasoning. Compares direct answer vs step-by-step reasoning for arithmetic
    or logical problems.

Usage:
    $ python examples/day06_chain_of_thought.py "2x + 6 = 14"
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class CoTComparison:
    """Comparison of direct vs Chain of Thought responses."""

    problem: str
    direct_response: str
    cot_response: str
    direct_answer: str | None
    cot_answer: str | None
    is_correct_direct: bool | None
    is_correct_cot: bool | None


class CoTAgent:
    """Agent that compares direct vs Chain of Thought reasoning."""

    def __init__(self, llm_url: str | None = None) -> None:
        """Initialise agent with LLM endpoint.

        Args:
            llm_url: Base URL for LLM API. Defaults to env or localhost.
        """
        self._llm_url = (
            llm_url or os.environ.get("LLM_URL") or "http://localhost:8000/v1"
        ).rstrip("/")
        self._client = httpx.Client(timeout=60.0)

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def _generate_response(self, prompt: str, use_cot: bool = False) -> str:
        """Generate LLM response with or without CoT.

        Args:
            prompt: Problem prompt.
            use_cot: Whether to use Chain of Thought instructions.

        Returns:
            LLM response text.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        if use_cot:
            enhanced_prompt = f"""Solve this problem step by step. Show your reasoning process.

Problem: {prompt}

Instructions:
1. Break down the problem into smaller steps
2. Show each step of your reasoning
3. Provide the final answer at the end

Let's solve this step by step:"""
        else:
            enhanced_prompt = prompt

        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": enhanced_prompt}],
                "temperature": 0.0,  # Deterministic for comparison
                "max_tokens": 512,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    def _extract_answer(self, response: str, problem: str) -> str | None:
        """Extract final answer from response.

        Args:
            response: LLM response text.
            problem: Original problem statement.

        Returns:
            Extracted answer string, or None if not found.
        """
        # Try to find answer patterns
        response_lower = response.lower()

        # Look for "answer:", "result:", "x =", etc.
        markers = ["answer:", "result:", "solution:", "x =", "="]
        for marker in markers:
            idx = response_lower.find(marker)
            if idx != -1:
                # Extract text after marker
                after_marker = response[idx + len(marker) :].strip()
                # Take first line or number
                lines = after_marker.split("\n")
                if lines:
                    return lines[0].strip()

        # Fallback: try to find a number
        words = response.split()
        for i, word in enumerate(words):
            if word.isdigit() or (word.startswith("-") and word[1:].isdigit()):
                return word

        return None

    def _check_correctness(self, answer: str | None, problem: str) -> bool | None:
        """Check if answer is correct (simple heuristic).

        Args:
            answer: Extracted answer string.
            problem: Original problem statement.

        Returns:
            True if correct, False if incorrect, None if unknown.
        """
        if answer is None:
            return None

        # Simple validation for "2x + 6 = 14" -> x = 4
        if "2x + 6 = 14" in problem:
            return answer.strip() == "4" or "x = 4" in answer or "4" in answer.split()

        # For other problems, return None (cannot validate automatically)
        return None

    def compare_cot(self, problem: str) -> CoTComparison:
        """Compare direct vs Chain of Thought responses.

        Args:
            problem: Problem to solve.

        Returns:
            CoTComparison with both responses and analysis.
        """
        # Get direct response
        direct_response = self._generate_response(problem, use_cot=False)

        # Get CoT response
        cot_response = self._generate_response(problem, use_cot=True)

        # Extract answers
        direct_answer = self._extract_answer(direct_response, problem)
        cot_answer = self._extract_answer(cot_response, problem)

        # Check correctness
        is_correct_direct = self._check_correctness(direct_answer, problem)
        is_correct_cot = self._check_correctness(cot_answer, problem)

        return CoTComparison(
            problem=problem,
            direct_response=direct_response,
            cot_response=cot_response,
            direct_answer=direct_answer,
            cot_answer=cot_answer,
            is_correct_direct=is_correct_direct,
            is_correct_cot=is_correct_cot,
        )


def format_comparison(comparison: CoTComparison) -> str:
    """Format CoT comparison results.

    Args:
        comparison: CoTComparison object.

    Returns:
        Formatted comparison string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("CHAIN OF THOUGHT COMPARISON")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Problem: {comparison.problem}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("DIRECT ANSWER (No CoT)")
    lines.append("-" * 60)
    lines.append(comparison.direct_response)
    lines.append("")
    lines.append(f"Extracted answer: {comparison.direct_answer or 'Not found'}")
    lines.append(f"Correct: {comparison.is_correct_direct or 'Unknown'}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("CHAIN OF THOUGHT (Step-by-step)")
    lines.append("-" * 60)
    lines.append(comparison.cot_response)
    lines.append("")
    lines.append(f"Extracted answer: {comparison.cot_answer or 'Not found'}")
    lines.append(f"Correct: {comparison.is_correct_cot or 'Unknown'}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)

    if (
        comparison.is_correct_direct is not None
        and comparison.is_correct_cot is not None
    ):
        if comparison.is_correct_cot and not comparison.is_correct_direct:
            lines.append("✓ CoT improved correctness")
        elif comparison.is_correct_direct and not comparison.is_correct_cot:
            lines.append("✗ Direct answer was more correct")
        elif comparison.is_correct_direct == comparison.is_correct_cot:
            lines.append("= Both methods produced same correctness")
    else:
        lines.append(
            "Note: Automatic correctness checking not available for this problem type."
        )
        lines.append("Please compare the responses manually.")

    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 6 demo."""
    args = sys.argv[1:] if argv is None else argv

    problem = " ".join(args) if args else "2x + 6 = 14"

    agent = CoTAgent()

    try:
        print(f"Problem: {problem}\n")
        comparison = agent.compare_cot(problem)

        output = format_comparison(comparison)
        print(output)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        agent.close()


if __name__ == "__main__":
    raise SystemExit(main())
