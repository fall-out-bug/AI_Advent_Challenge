"""Reminders handler for Butler Agent REMINDERS mode.

Handles listing and managing reminders.
Following Python Zen: Simple is better than complex.
"""

import logging
from typing import Optional

from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class RemindersHandler(Handler):
    """Handler for REMINDERS mode - list active reminders.

    Uses MCP tools to retrieve and format reminders.
    Following SOLID: Single Responsibility Principle.
    """

    def __init__(
        self,
        tool_client: ToolClientProtocol,
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ):
        """Initialize reminders handler.

        Args:
            tool_client: MCP tool client for reminders
            hybrid_classifier: Optional hybrid intent classifier for intent detection and entity extraction
        """
        self.tool_client = tool_client
        self.hybrid_classifier = hybrid_classifier

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle reminders request.

        Uses hybrid classifier to detect intent (list vs set) and extract entities.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text with reminders list or confirmation
        """
        # Use hybrid classifier if available (preferred method)
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                logger.debug(
                    f"RemindersHandler: intent={intent_result.intent.value}, "
                    f"confidence={intent_result.confidence:.2f}, entities={intent_result.entities}"
                )

                # Route based on intent type
                if intent_result.intent == IntentType.REMINDER_SET:
                    reminder_text = intent_result.entities.get("reminder_text")
                    if reminder_text:
                        # Create reminder via MCP tool
                        try:
                            result = await self.tool_client.call_tool(
                                "create_reminder",
                                {
                                    "user_id": int(context.user_id),
                                    "text": reminder_text,
                                },
                            )
                            if result.get("status") == "created":
                                return f"✅ Напоминание создано: {reminder_text}"
                            else:
                                return f"❌ Не удалось создать напоминание."
                        except Exception as e:
                            logger.error(
                                f"Failed to create reminder: {e}", exc_info=True
                            )
                            return "❌ Не удалось создать напоминание. Попробуйте позже."
                    else:
                        return (
                            "❓ Что именно нужно напомнить? Укажите текст напоминания."
                        )

                elif intent_result.intent == IntentType.REMINDER_LIST:
                    # List reminders (fall through to default behavior)
                    pass

                elif intent_result.intent == IntentType.REMINDER_DELETE:
                    # Delete reminder - would need reminder_id from entities
                    # For now, just show message
                    return "❌ Удаление напоминаний через бота пока не поддерживается."
            except Exception as e:
                logger.warning(
                    f"Hybrid classifier failed in RemindersHandler: {e}, falling back to listing"
                )

        # Default: list reminders
        try:
            result = await self.tool_client.call_tool(
                "list_reminders", {"user_id": context.user_id}
            )
            reminders = result.get("reminders", [])
            if not reminders:
                return "⏰ No active reminders."
            return self._format_reminders(reminders)
        except Exception as e:
            logger.error(f"Failed to list reminders: {e}", exc_info=True)
            return "❌ Failed to retrieve reminders. Please try again."

    def _format_reminders(self, reminders: list) -> str:
        """Format reminders for display.

        Args:
            reminders: List of reminder dictionaries

        Returns:
            Formatted text
        """
        lines = ["⏰ Active Reminders:\n"]
        for reminder in reminders[:10]:
            text = reminder.get("text", "No text")
            time = reminder.get("time", "Unknown time")
            lines.append(f"• {text} - {time}")
        return "\n".join(lines)
