"""Mode classification service for Butler bot."""

from __future__ import annotations

import logging
from typing import Optional

from src.application.dtos.butler_dialog_dtos import DialogMode
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class ModeClassifier:
    """Classifies user messages into dialog modes using LLM and heuristics."""

    MODE_CLASSIFICATION_PROMPT = """Classify the user message into one of these modes:
- TASK: User wants to create, update, or manage a task
- DATA: User wants to get channel digests, student stats, subscriptions list, channel lists, or data summaries
- HOMEWORK_REVIEW: User wants to review homework (e.g., "сделай ревью {{hash}}", "покажи домашки")
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

Respond with ONLY the mode name: TASK, DATA, HOMEWORK_REVIEW, or IDLE.

Message: {message}"""

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        default_model: str = "mistral",
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ):
        """Initialize classifier with optional hybrid intent classifier."""
        self.llm_client = llm_client
        self.default_model = default_model
        self.hybrid_classifier = hybrid_classifier

    async def classify(self, message: str) -> DialogMode:
        """Classify user message into dialog mode."""
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                dialog_mode = self._intent_to_dialog_mode(intent_result.intent)
                logger.debug(
                    "Hybrid classifier: intent=%s, confidence=%.2f, mode=%s",
                    intent_result.intent.value,
                    intent_result.confidence,
                    dialog_mode.value,
                )
                return dialog_mode
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Hybrid classifier failed: %s, falling back to keyword matching",
                    exc,
                )

        message_lower = message.lower()
        if self._matches_homework_keywords(message_lower):
            return DialogMode.HOMEWORK_REVIEW
        if self._matches_data_keywords(message_lower):
            return DialogMode.DATA
        if self._matches_task_keywords(message_lower):
            return DialogMode.TASK

        try:
            prompt = self.MODE_CLASSIFICATION_PROMPT.format(message=message)
            response = await self.llm_client.make_request(
                model_name=self.default_model,
                prompt=prompt,
                max_tokens=10,
                temperature=0.1,
            )
            return self._parse_response(response)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Mode classification failed: %s, falling back to IDLE", exc)
            return DialogMode.IDLE

    def _matches_homework_keywords(self, message_lower: str) -> bool:
        """Return True when message matches homework mode keywords."""
        list_keywords = [
            "покажи домашки",
            "покажи домашк",
            "покажи домашние работы",
            "show homework",
            "homework list",
            "список домашек",
            "list homework",
            "домашки",
            "homework",
        ]
        review_keywords = [
            "сделай ревью",
            "do review",
            "review",
            "ревью",
            "проверь коммит",
            "check commit",
            "проверь домашку",
        ]
        if any(keyword in message_lower for keyword in list_keywords):
            if "статус" not in message_lower and "status" not in message_lower:
                logger.debug(
                    "Fast path: '%s' classified as HOMEWORK_REVIEW (list)",
                    message_lower,
                )
                return True
        if any(keyword in message_lower for keyword in review_keywords):
            logger.debug(
                "Fast path: '%s' classified as HOMEWORK_REVIEW (review)", message_lower
            )
            return True
        return False

    def _matches_data_keywords(self, message_lower: str) -> bool:
        """Return True when message matches data mode keywords."""
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
            logger.debug("Fast path: '%s' classified as DATA", message_lower)
            return True
        return False

    def _matches_task_keywords(self, message_lower: str) -> bool:
        """Return True when message matches task mode keywords."""
        task_keywords = [
            "создай задачу",
            "create task",
            "create a task",
            "добавь задачу",
            "add task",
            "add a task",
            "удалить задачу",
            "delete task",
            "delete a task",
            "задачи",
            "tasks",
        ]
        if any(keyword in message_lower for keyword in task_keywords):
            logger.debug("Fast path: '%s' classified as TASK", message_lower)
            return True
        return False

    def _intent_to_dialog_mode(self, intent: IntentType) -> DialogMode:
        """Map IntentType to DialogMode."""
        if intent == IntentType.TASK or intent.name.startswith("TASK_"):
            return DialogMode.TASK
        if intent == IntentType.DATA or intent.name.startswith("DATA_"):
            return DialogMode.DATA
        if intent.name.startswith("HOMEWORK_") or intent.name.startswith("REVIEW_"):
            return DialogMode.HOMEWORK_REVIEW
        return DialogMode.IDLE

    def _parse_response(self, response: str) -> DialogMode:
        """Parse LLM response into DialogMode."""
        response_upper = response.strip().upper()
        for mode in DialogMode:
            if mode.value.upper() in response_upper or mode.name in response_upper:
                return mode
        logger.warning("Could not parse mode from response: %s", response)
        return DialogMode.IDLE
