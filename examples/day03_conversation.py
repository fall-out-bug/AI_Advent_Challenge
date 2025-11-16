#!/usr/bin/env python
"""Day 3 · Conversation with self-stopping agent.

Purpose:
    Example of an agent that conducts a multi-turn conversation with an LLM,
    collecting information until a completion condition is met (e.g., gathering
    requirements for a technical specification). The model stops itself when
    the result is ready.

Usage:
    $ python examples/day03_conversation.py
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class RequirementsSpec:
    """Technical requirements specification schema."""

    title: str
    description: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    acceptance_criteria: list[str]


class ConversationalAgent:
    """Agent that conducts multi-turn conversation until result is ready."""

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
        self._conversation_history: list[dict[str, str]] = []

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()

    def _build_system_prompt(self) -> str:
        """Build system prompt with stopping instructions.

        Returns:
            System prompt explaining the task and completion condition.
        """
        return """You are a requirements analyst. Your task is to gather
requirements for a technical specification through a conversation with the user.

Process:
1. Ask clarifying questions to understand the project needs.
2. Collect functional and non-functional requirements.
3. When you have enough information, output a COMPLETE SPECIFICATION.

Stop condition: When you have gathered sufficient requirements, output
ONLY a valid JSON object with this schema:
{
    "title": "string",
    "description": "string",
    "functional_requirements": ["string"],
    "non_functional_requirements": ["string"],
    "acceptance_criteria": ["string"]
}

Output nothing else after the JSON. Do not continue the conversation after
outputting the final specification."""

    def _send_message(self, content: str, role: str = "user") -> str:
        """Send message to LLM and get response.

        Args:
            content: Message content.
            role: Message role (user/assistant/system).

        Returns:
            LLM response content.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        if role == "system" and not self._conversation_history:
            self._conversation_history.append({"role": "system", "content": content})
        else:
            self._conversation_history.append({"role": role, "content": content})

        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": self._conversation_history,
                "temperature": 0.3,
                "max_tokens": 512,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        assistant_message = data["choices"][0]["message"]["content"]
        self._conversation_history.append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    def _extract_spec_from_response(self, response: str) -> RequirementsSpec | None:
        """Try to extract specification JSON from response.

        Args:
            response: LLM response text.

        Returns:
            Parsed RequirementsSpec if found, None otherwise.
        """
        # Try to find JSON block
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            return None

        try:
            json_str = response[start_idx:end_idx]
            parsed = json.loads(json_str)

            if all(
                key in parsed
                for key in [
                    "title",
                    "description",
                    "functional_requirements",
                    "non_functional_requirements",
                    "acceptance_criteria",
                ]
            ):
                return RequirementsSpec(
                    title=parsed["title"],
                    description=parsed["description"],
                    functional_requirements=parsed["functional_requirements"],
                    non_functional_requirements=parsed["non_functional_requirements"],
                    acceptance_criteria=parsed["acceptance_criteria"],
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return None

    def collect_requirements(
        self, initial_prompt: str, max_turns: int = 10
    ) -> RequirementsSpec:
        """Conduct conversation to collect requirements.

        Args:
            initial_prompt: User's initial request.
            max_turns: Maximum conversation turns before forcing stop.

        Returns:
            Final RequirementsSpec object.

        Raises:
            RuntimeError: If max turns exceeded without completion.
            httpx.HTTPError: If LLM API call fails.
        """
        system_prompt = self._build_system_prompt()
        self._send_message(system_prompt, role="system")

        self._send_message(initial_prompt, role="user")
        print(f"User: {initial_prompt}\n")

        for turn in range(max_turns):
            assistant_response = self._send_message("", role="user")
            print(f"Assistant (turn {turn + 1}): {assistant_response}\n")

            # Check if model output final specification
            spec = self._extract_spec_from_response(assistant_response)
            if spec is not None:
                print("✓ Specification collected successfully!\n")
                return spec

        raise RuntimeError(
            f"Max turns ({max_turns}) exceeded without completion. "
            "Model did not output final specification."
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 3 demo."""
    initial_prompt = (
        " ".join(argv[1:]) if argv and len(argv) > 1
        else "I want to build a task management system for a small team."
    )

    agent = ConversationalAgent()

    try:
        spec = agent.collect_requirements(initial_prompt)

        print("=" * 60)
        print("FINAL SPECIFICATION")
        print("=" * 60)
        print(f"Title: {spec.title}")
        print(f"\nDescription: {spec.description}")
        print(f"\nFunctional Requirements:")
        for req in spec.functional_requirements:
            print(f"  - {req}")
        print(f"\nNon-Functional Requirements:")
        for req in spec.non_functional_requirements:
            print(f"  - {req}")
        print(f"\nAcceptance Criteria:")
        for criterion in spec.acceptance_criteria:
            print(f"  - {criterion}")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        agent.close()


if __name__ == "__main__":
    raise SystemExit(main())

