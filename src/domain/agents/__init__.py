"""Domain agents module.

Agents are the core entities representing specialized AI agents
capable of performing tasks like code generation and review.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

from src.domain.agents.base_agent import BaseAgent, TaskMetadata
from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent

__all__ = [
    "BaseAgent",
    "TaskMetadata",
    "CodeGeneratorAgent",
    "CodeReviewerAgent",
]
