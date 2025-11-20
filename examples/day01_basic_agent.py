#!/usr/bin/env python
"""Day 1 · Basic agent demo.

Purpose:
    Minimal example of an agent that receives a question from stdin,
    calls a (mock) tool, and prints the response. This is a standalone
    script for Challenge Day 1 (Первый агент).

Usage:
    $ python examples/day01_basic_agent.py "What can you do?"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Simple tool result."""

    content: str


class EchoTool:
    """Mock tool that echoes user question with a canned prefix."""

    def run(self, query: str) -> ToolResult:
        """Execute the tool.

        Args:
            query: User question.

        Returns:
            ToolResult with simple echo message.
        """
        return ToolResult(content=f"[echo_tool] You asked: {query}")


class BasicAgent:
    """Minimal agent that forwards questions to a tool."""

    def __init__(self, tool: EchoTool) -> None:
        """Initialise agent with a tool dependency."""
        self._tool = tool

    def handle(self, query: str) -> str:
        """Handle user query by calling the tool and formatting a reply."""
        result = self._tool.run(query)
        return f"Agent reply -> {result.content}"


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 1 demo."""
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print('Usage: day01_basic_agent.py "your question"')
        return 1

    question = " ".join(args)
    agent = BasicAgent(tool=EchoTool())
    reply = agent.handle(question)
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
