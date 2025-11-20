#!/usr/bin/env python
"""Day 7 · Agent interaction demo.

Purpose:
    Example demonstrating interaction between two agents with different roles.
    Agent 1 performs a task (e.g., code generation), Agent 2 reviews and
    validates the result. Shows how agents can collaborate by passing structured
    data between them.

Usage:
    $ python examples/day07_agent_interaction.py "Write a function to calculate factorial"

Note:
    This file exceeds the recommended 150 lines per file guideline (~333 lines)
    but is intentionally kept as a single file for educational/demo purposes.
    The file demonstrates a complete agent interaction workflow including multiple
    classes, data structures, and orchestration logic. In a production codebase,
    this would be split into separate modules (agents, orchestrator, DTOs, etc.).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class TaskResult:
    """Result from Agent 1 (task executor)."""

    task: str
    output: str
    status: str  # "success", "partial", "error"
    metadata: dict[str, Any]


@dataclass
class ReviewResult:
    """Result from Agent 2 (reviewer)."""

    task_result: TaskResult
    review_score: float  # 0-1
    issues: list[str]
    approval: bool


class TaskAgent:
    """Agent 1: Executes tasks and produces output."""

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

    def execute_task(self, task: str) -> TaskResult:
        """Execute a task and produce output.

        Args:
            task: Task description.

        Returns:
            TaskResult with output and metadata.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        prompt = f"""Execute the following task and provide the result.

Task: {task}

Provide your output in a clear, structured format that can be easily
reviewed by another agent. Include any code, explanations, or data as needed.

Output:"""

        response = self._client.post(
            f"{self._llm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 512,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        output = data["choices"][0]["message"]["content"]

        # Determine status based on output
        status = "success" if len(output) > 20 else "partial"

        metadata = {
            "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            "model": data.get("model", "unknown"),
        }

        return TaskResult(
            task=task,
            output=output,
            status=status,
            metadata=metadata,
        )

    def format_for_review(self, result: TaskResult) -> str:
        """Format task result for review by another agent.

        Args:
            result: TaskResult to format.

        Returns:
            Formatted string for reviewer.
        """
        return f"""Task Result:
Task: {result.task}
Status: {result.status}
Output:
{result.output}

Metadata: {json.dumps(result.metadata, indent=2)}
"""


class ReviewerAgent:
    """Agent 2: Reviews and validates work from Agent 1."""

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

    def review(self, task_result: TaskResult, formatted_result: str) -> ReviewResult:
        """Review task result from Agent 1.

        Args:
            task_result: Original TaskResult from Agent 1.
            formatted_result: Formatted string representation.

        Returns:
            ReviewResult with score, issues, and approval.

        Raises:
            httpx.HTTPError: If LLM API call fails.
        """
        prompt = f"""Review the following task result from another agent.

{formatted_result}

Evaluate:
1. Does the output complete the task?
2. Is the output correct and well-structured?
3. Are there any issues or improvements needed?

Provide your review in JSON format:
{{
    "score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "approval": true/false,
    "feedback": "brief feedback"
}}"""

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
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        review_data = json.loads(content)

        return ReviewResult(
            task_result=task_result,
            review_score=float(review_data.get("score", 0.5)),
            issues=review_data.get("issues", []),
            approval=bool(review_data.get("approval", False)),
        )


class AgentOrchestrator:
    """Orchestrates interaction between TaskAgent and ReviewerAgent."""

    def __init__(
        self,
        task_agent: TaskAgent,
        reviewer_agent: ReviewerAgent,
    ) -> None:
        """Initialise orchestrator with two agents.

        Args:
            task_agent: Agent 1 (task executor).
            reviewer_agent: Agent 2 (reviewer).
        """
        self._task_agent = task_agent
        self._reviewer_agent = reviewer_agent

    def execute_and_review(self, task: str) -> tuple[TaskResult, ReviewResult]:
        """Execute task and get it reviewed.

        Args:
            task: Task description.

        Returns:
            Tuple of (TaskResult, ReviewResult).
        """
        # Agent 1 executes task
        print(f"Agent 1 (Task Executor): Executing task...")
        task_result = self._task_agent.execute_task(task)
        print(f"✓ Task completed with status: {task_result.status}\n")

        # Format for review
        formatted = self._task_agent.format_for_review(task_result)

        # Agent 2 reviews
        print(f"Agent 2 (Reviewer): Reviewing task result...")
        review_result = self._reviewer_agent.review(task_result, formatted)
        print(f"✓ Review completed\n")

        return task_result, review_result


def format_output(task_result: TaskResult, review_result: ReviewResult) -> str:
    """Format final output from both agents.

    Args:
        task_result: TaskResult from Agent 1.
        review_result: ReviewResult from Agent 2.

    Returns:
        Formatted output string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("AGENT INTERACTION RESULTS")
    lines.append("=" * 60)
    lines.append("")

    lines.append("-" * 60)
    lines.append("AGENT 1: TASK RESULT")
    lines.append("-" * 60)
    lines.append(f"Task: {task_result.task}")
    lines.append(f"Status: {task_result.status}")
    lines.append(f"Output:")
    lines.append(task_result.output)
    lines.append("")

    lines.append("-" * 60)
    lines.append("AGENT 2: REVIEW RESULT")
    lines.append("-" * 60)
    lines.append(f"Review Score: {review_result.review_score:.2f}/1.0")
    lines.append(
        f"Approval: {'✓ Approved' if review_result.approval else '✗ Not Approved'}"
    )
    lines.append(f"Issues: {len(review_result.issues)}")
    if review_result.issues:
        for issue in review_result.issues:
            lines.append(f"  - {issue}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    if review_result.approval:
        lines.append("✓ Task completed and approved by reviewer.")
    else:
        lines.append("✗ Task completed but reviewer identified issues.")

    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point for Day 7 demo."""
    args = sys.argv[1:] if argv is None else argv

    task = " ".join(args) if args else "Write a function to calculate factorial"

    task_agent = TaskAgent()
    reviewer_agent = ReviewerAgent()

    try:
        orchestrator = AgentOrchestrator(task_agent, reviewer_agent)
        task_result, review_result = orchestrator.execute_and_review(task)

        output = format_output(task_result, review_result)
        print(output)

        return 0 if review_result.approval else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        task_agent.close()
        reviewer_agent.close()


if __name__ == "__main__":
    raise SystemExit(main())
