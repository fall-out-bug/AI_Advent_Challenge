"""Conversation entities for Mistral agent orchestration.

Following Clean Architecture and the Zen of Python:
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ConversationMessage:
    """Message in a conversation.

    Attributes:
        role: Message role (user/assistant)
        content: Message content
        timestamp: Message timestamp
        metadata: Optional metadata
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Conversation entity.

    Attributes:
        conversation_id: Unique identifier
        messages: List of messages
        context: Additional context
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    conversation_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add message to conversation.

        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        self.messages.append(
            ConversationMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
        )
        self.updated_at = datetime.utcnow()

    def get_recent_messages(self, limit: int = 5) -> List[ConversationMessage]:
        """Get recent messages.

        Args:
            limit: Maximum number of messages

        Returns:
            List of recent messages
        """
        return self.messages[-limit:] if len(self.messages) > limit else self.messages


@dataclass
class IntentAnalysis:
    """Intent analysis result.

    Attributes:
        primary_goal: Main goal of the request
        tools_needed: List of required tools
        parameters: Tool parameters
        confidence: Confidence score (0-1)
        needs_clarification: Whether clarification needed
        unclear_aspects: List of unclear aspects
    """

    primary_goal: str
    tools_needed: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    needs_clarification: bool = False
    unclear_aspects: List[str] = field(default_factory=list)


@dataclass
class ExecutionStep:
    """Single execution step.

    Attributes:
        tool: Tool name
        args: Tool arguments
        result: Optional result
    """

    tool: str
    args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionPlan:
    """Execution plan for multi-step workflow.

    Attributes:
        steps: List of execution steps
        estimated_time: Estimated execution time in seconds
        dependencies: List of dependencies
    """

    steps: List[ExecutionStep] = field(default_factory=list)
    estimated_time: float = 0.0
    dependencies: List[str] = field(default_factory=list)

