"""Mode classification service for Butler Agent.

Classifies user messages into one of 4 modes: TASK, DATA, REMINDERS, IDLE.
Following Python Zen: Simple is better than complex.
"""

import logging
from enum import Enum
from typing import Optional

from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class DialogMode(Enum):
    """Dialog mode enumeration.

    Represents the 5 possible modes for Butler Agent.
    """

    TASK = "task"
    DATA = "data"
    REMINDERS = "reminders"
    HOMEWORK_REVIEW = "homework_review"
    IDLE = "idle"


class ModeClassifier:
    """Classifies user messages into dialog modes using LLM.

    Uses LLM to classify user intent into one of 4 modes.
    Falls back to IDLE if LLM is unavailable.

    Attributes:
        llm_client: LLM client protocol for classification
        default_model: Default model name for classification
    """

    MODE_CLASSIFICATION_PROMPT = """Classify the user message into one of these modes:
- TASK: User wants to create, update, or manage a task
- DATA: User wants to get channel digests, student stats, subscriptions list, channel lists, or data summaries
- REMINDERS: User wants to see or manage reminders
- HOMEWORK_REVIEW: User wants to review homework (e.g., "сделай ревью {hash}", "покажи домашки")
- IDLE: General conversation, questions, or unclear intent

Examples:
- "Дай мои подписки" → DATA
- "Список каналов" → DATA
- "Дайджест по каналу" → DATA
- "мои подписки" → DATA
- "Покажи домашки" → HOMEWORK_REVIEW
- "Сделай ревью abc123" → HOMEWORK_REVIEW
- "Привет" → IDLE
- "Создай задачу" → TASK

Respond with ONLY the mode name: TASK, DATA, REMINDERS, HOMEWORK_REVIEW, or IDLE.

Message: {message}"""

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        default_model: str = "mistral",
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ):
        """Initialize mode classifier.

        Args:
            llm_client: LLM client for classification (used as fallback if hybrid_classifier not provided)
            default_model: Default model name
            hybrid_classifier: Optional hybrid intent classifier (if provided, uses it for classification)
        """
        self.llm_client = llm_client
        self.default_model = default_model
        self.hybrid_classifier = hybrid_classifier

    async def classify(self, message: str) -> DialogMode:
        """Classify user message into dialog mode.

        Args:
            message: User message text

        Returns:
            DialogMode enum value

        Example:
            >>> classifier = ModeClassifier(llm_client)
            >>> mode = await classifier.classify("Create a task to buy milk")
            >>> mode == DialogMode.TASK
            True
        """
        # Use hybrid classifier if available (preferred method)
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                # Map IntentType to DialogMode
                dialog_mode = self._intent_to_dialog_mode(intent_result.intent)
                logger.debug(
                    f"Hybrid classifier: intent={intent_result.intent.value}, "
                    f"confidence={intent_result.confidence:.2f}, mode={dialog_mode.value}"
                )
                return dialog_mode
            except Exception as e:
                logger.warning(
                    f"Hybrid classifier failed: {e}, falling back to keyword matching"
                )

        # Fallback: Fast path - check for obvious keywords before LLM call
        message_lower = message.lower()

        # Check for HOMEWORK_REVIEW mode keywords (review, домашки list)
        # Priority: Check HOMEWORK_REVIEW FIRST before DATA to avoid conflicts
        # Patterns for listing commits (not status checks)
        homework_list_keywords = [
            "покажи домашки",
            "покажи домашк",
            "покажи домашние работы",
            "show homework",
            "homework list",
            "список домашек",
            "list homework",
            "домашки",
            "homework",  # Simple keywords
        ]
        # Patterns for review commands
        homework_review_keywords = [
            "сделай ревью",
            "do review",
            "review",
            "ревью",
            "проверь коммит",
            "check commit",
            "проверь домашку",
        ]

        # Check if message contains homework list keywords (but not status)
        if any(keyword in message_lower for keyword in homework_list_keywords):
            # Exclude status-related messages
            if "статус" not in message_lower and "status" not in message_lower:
                logger.debug(
                    f"Fast path: classified '{message}' as HOMEWORK_REVIEW (list) based on keywords"
                )
                return DialogMode.HOMEWORK_REVIEW

        # Check for review commands
        # Match "сделай ревью" even if followed by long commit hash
        if any(keyword in message_lower for keyword in homework_review_keywords):
            logger.debug(
                f"Fast path: classified '{message[:100]}...' as HOMEWORK_REVIEW (review) based on keywords"
            )
            return DialogMode.HOMEWORK_REVIEW

        # Check for DATA mode keywords (subscriptions, channels, digests, homework status)
        # Note: "статус домашек" is for status checks, not listing commits
        data_keywords = [
            "подписк",
            "подпиш",
            "subscription",
            "subscribe",
            "канал",
            "channels",
            "список каналов",
            "дайджест",
            "digest",
            "мои подписк",
            "мои каналы",
            "покажи подписк",
            "покажи канал",
            "show channels",
            "list channels",
            "добавь канал",
            "add channel",
            "статус проверки домашних",
            "статус проверки домашк",
            "статус домашних заданий",
            "статус домашк",
            "status домашек",
            "homework status",
            "hw status",
            "статус очеред",
            "queue status",
            "очередь",
            "перезапусти сабмит",
            "retry submission",
            "retry сабмит",
        ]
        if any(keyword in message_lower for keyword in data_keywords):
            logger.debug(f"Fast path: classified '{message}' as DATA based on keywords")
            return DialogMode.DATA

        # Check for TASK mode keywords
        task_keywords = [
            "создай задачу",
            "create task",
            "добавь задачу",
            "add task",
            "удалить задачу",
            "delete task",
            "задачи",
            "tasks",
        ]
        if any(keyword in message_lower for keyword in task_keywords):
            logger.debug(f"Fast path: classified '{message}' as TASK based on keywords")
            return DialogMode.TASK

        # Check for REMINDERS mode keywords
        reminder_keywords = ["напоминани", "reminder", "напомни", "remind"]
        if any(keyword in message_lower for keyword in reminder_keywords):
            logger.debug(
                f"Fast path: classified '{message}' as REMINDERS based on keywords"
            )
            return DialogMode.REMINDERS

        # Use LLM for ambiguous cases (fallback)
        try:
            prompt = self.MODE_CLASSIFICATION_PROMPT.format(message=message)
            response = await self.llm_client.make_request(
                model_name=self.default_model,
                prompt=prompt,
                max_tokens=10,
                temperature=0.1,
            )
            return self._parse_response(response)
        except Exception as e:
            logger.warning(f"Mode classification failed: {e}, falling back to IDLE")
            return DialogMode.IDLE

    def _intent_to_dialog_mode(self, intent: IntentType) -> DialogMode:
        """Map IntentType to DialogMode.

        Args:
            intent: IntentType from hybrid classifier

        Returns:
            DialogMode enum value
        """
        # Map mode-level intents directly
        if intent == IntentType.TASK or intent.name.startswith("TASK_"):
            return DialogMode.TASK
        elif intent == IntentType.DATA or intent.name.startswith("DATA_"):
            return DialogMode.DATA
        elif intent == IntentType.REMINDERS or intent.name.startswith("REMINDER_"):
            return DialogMode.REMINDERS
        elif intent.name.startswith("HOMEWORK_") or intent.name.startswith("REVIEW_"):
            return DialogMode.HOMEWORK_REVIEW
        else:
            return DialogMode.IDLE

    def _parse_response(self, response: str) -> DialogMode:
        """Parse LLM response into DialogMode.

        Args:
            response: LLM response text

        Returns:
            DialogMode enum value

        Raises:
            ValueError: If response cannot be parsed
        """
        response_upper = response.strip().upper()
        for mode in DialogMode:
            if mode.value.upper() in response_upper or mode.name in response_upper:
                return mode
        logger.warning(f"Could not parse mode from response: {response}")
        return DialogMode.IDLE
