"""Context window manager for conversation context.

Following Python Zen: "Simple is better than complex."
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages conversation context with automatic summarization."""

    def __init__(
        self,
        max_tokens: int = 4000,
        summary_threshold: float = 0.8,
        recent_messages_to_preserve: int = 5,
    ) -> None:
        """Initialize context manager.

        Args:
            max_tokens: Maximum token budget
            summary_threshold: Threshold for triggering summarization (0-1)
            recent_messages_to_preserve: Number of recent messages to always keep
        """
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
        self.recent_messages_to_preserve = recent_messages_to_preserve

    def should_summarize(self, messages: List[Dict[str, Any]], estimated_tokens: int) -> bool:
        """Check if summarization is needed.

        Args:
            messages: Conversation messages
            estimated_tokens: Estimated token count

        Returns:
            True if summarization needed
        """
        utilization = estimated_tokens / self.max_tokens
        return utilization >= self.summary_threshold

    def create_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Create summary of old messages.

        Args:
            messages: Messages to summarize

        Returns:
            Summary string
        """
        if not messages:
            return ""

        # Extract key information
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        summary_parts = []
        if user_messages:
            summary_parts.append(f"User had {len(user_messages)} messages")
        if assistant_messages:
            summary_parts.append(f"Assistant responded {len(assistant_messages)} times")

        return f"Summary: {', '.join(summary_parts)}"

    def prioritize_messages(
        self, messages: List[Dict[str, Any]], budget: int
    ) -> List[Dict[str, Any]]:
        """Prioritize messages within token budget.

        Args:
            messages: All messages
            budget: Token budget

        Returns:
            Prioritized message list
        """
        # Always preserve recent messages
        recent = messages[-self.recent_messages_to_preserve:]
        
        # For remaining budget, include tool results
        remaining_budget = budget - self._estimate_tokens(recent)
        prioritized = recent.copy()

        for msg in reversed(messages[:-self.recent_messages_to_preserve]):
            msg_tokens = self._estimate_tokens([msg])
            if remaining_budget >= msg_tokens:
                prioritized.insert(0, msg)
                remaining_budget -= msg_tokens
            else:
                break

        return prioritized

    def get_context_window(self, messages: List[Dict[str, Any]]) -> str:
        """Get formatted context window.

        Args:
            messages: Conversation messages

        Returns:
            Formatted context string
        """
        estimated_tokens = self._estimate_tokens(messages)

        if self.should_summarize(messages, estimated_tokens):
            # Summarize old messages, preserve recent
            old_messages = messages[:-self.recent_messages_to_preserve]
            recent_messages = messages[-self.recent_messages_to_preserve:]
            
            summary = self.create_summary(old_messages)
            context_parts = [summary] if summary else []
            
            for msg in recent_messages:
                context_parts.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")
            
            return "\n".join(context_parts)
        else:
            # Use all messages
            return "\n".join(
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in messages
            )

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages.

        Args:
            messages: Messages

        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
        return int(total_chars / 4)

