#!/usr/bin/env python
"""Day 2 · Output schema demo.

Purpose:
    Example of an agent that requests structured JSON output from an LLM
    using a prompt schema and response_format. This demonstrates Challenge
    Day 2 (Настройка AI - формат результата).

Usage:
    $ python examples/day02_output_schema.py "What is the weather like today?"
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class WeatherResponse:
    """Structured weather response schema."""

    location: str
    temperature: float
    condition: str
    humidity: int


class StructuredAgent:
    """Agent that requests structured JSON output from LLM."""

    def __init__(self, llm_url: str | None = None) -> None:
        """Initialise agent with LLM endpoint.

        Args:
            llm_url: Base URL for LLM API. Defaults to env or localhost.
        """
        self._llm_url = (
            llm_url or os.environ.get("LLM_URL") or "http://localhost:8000/v1"
        ).rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def _build_prompt(self, user_query: str) -> str:
        """Build prompt with output schema instructions.

        Args:
            user_query: User's question.

        Returns:
            Prompt with schema specification.
        """
        schema_example = json.dumps(
            {
                "location": "Moscow",
                "temperature": 15.5,
                "condition": "Partly cloudy",
                "humidity": 65,
            },
            indent=2,
        )

        return f"""Answer the user's question and return the result as a valid JSON object.

Schema:
{{
    "location": "string (city name)",
    "temperature": "float (degrees Celsius)",
    "condition": "string (weather condition)",
    "humidity": "int (percentage 0-100)"
}}

Example output:
{schema_example}

User question: {user_query}

Return ONLY valid JSON, no additional text."""

    def handle(self, query: str) -> WeatherResponse:
        """Handle user query and return structured response.

        Args:
            query: User's question.

        Returns:
            Parsed WeatherResponse object.

        Raises:
            httpx.HTTPError: If LLM API call fails.
            json.JSONDecodeError: If response is not valid JSON.
            KeyError: If required fields are missing.
        """
        prompt = self._build_prompt(query)

        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 256,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return WeatherResponse(
            location=parsed["location"],
            temperature=float(parsed["temperature"]),
            condition=parsed["condition"],
            humidity=int(parsed["humidity"]),
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 2 demo."""
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print('Usage: day02_output_schema.py "your question"')
        return 1

    question = " ".join(args)
    agent = StructuredAgent()

    try:
        result = agent.handle(question)
        print(f"Location: {result.location}")
        print(f"Temperature: {result.temperature}°C")
        print(f"Condition: {result.condition}")
        print(f"Humidity: {result.humidity}%")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        agent.close()


if __name__ == "__main__":
    raise SystemExit(main())
