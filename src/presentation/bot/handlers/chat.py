"""Chat handler for Butler bot IDLE mode."""

from __future__ import annotations

import logging
import re
from typing import Optional

from src.application.dtos.butler_dialog_dtos import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.llm_client import LLMClientProtocol
from src.presentation.bot.handlers.base import Handler

logger = logging.getLogger(__name__)


class ChatHandler(Handler):
    """Handle general conversation and fallback responses."""

    CHAT_PROMPT = """You are Butler, a helpful assistant.
Respond naturally and helpfully to the user's message in the SAME LANGUAGE as the user.
Keep responses concise, friendly, and natural.
DO NOT include "User:", "Butler:", "User message:", or "Response:" prefixes.
DO NOT provide educational facts or translations unless explicitly asked.
DO NOT make up information - if you don't know something, say so simply.

Just respond naturally to what the user said. Be brief and helpful.

{message}"""

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        default_model: str = "mistral",
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
    ) -> None:
        """Initialize chat handler dependencies."""
        self.llm_client = llm_client
        self.default_model = default_model
        self.hybrid_classifier = hybrid_classifier

    async def handle(self, context: DialogContext, message: str) -> str:
        """Generate natural response for chat/idle messages."""
        if self.hybrid_classifier:
            await self._log_intent(message)

        try:
            prompt = self.CHAT_PROMPT.format(message=message)
            response = await self.llm_client.make_request(
                model_name=self.default_model,
                prompt=prompt,
                max_tokens=256,
                temperature=0.7,
            )
            return self._clean_response(response)
        except Exception as exc:  # noqa: BLE001
            logger.error("Chat handling failed: %s", exc, exc_info=True)
            return "Я здесь, чтобы помочь! Попробуйте создать задачу или запросить данные."

    async def _log_intent(self, message: str) -> None:
        """Run hybrid classifier to confirm idle intent."""
        if not self.hybrid_classifier:
            return
        try:
            intent_result = await self.hybrid_classifier.classify(message)
            logger.debug(
                "ChatHandler intent=%s confidence=%.2f entities=%s",
                intent_result.intent.value,
                intent_result.confidence,
                intent_result.entities,
            )
            if intent_result.intent not in {
                IntentType.IDLE,
                IntentType.GENERAL_CHAT,
                IntentType.GENERAL_QUESTION,
            }:
                logger.debug(
                    "ChatHandler received non-IDLE intent: %s (confidence=%.2f)",
                    intent_result.intent.value,
                    intent_result.confidence,
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Hybrid classifier failed in ChatHandler: %s", exc)

    def _clean_response(self, response: str) -> str:
        """Remove artifacts and translations from LLM output."""
        text = response.strip()
        prefixes = ["User:", "Butler:", "Assistant:", "AI:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
            text = re.sub(rf"^{re.escape(prefix)}\s*", "", text, flags=re.MULTILINE)
            text = re.sub(rf"\s*{re.escape(prefix)}\s*", " ", text)

        has_russian = bool(re.search(r"[а-яА-Я]", text))
        has_english = bool(re.search(r"\b[A-Z][a-z]+", text))
        if has_russian and has_english:
            sentences = re.split(r"[.!?]\s+|,\s+(?=[A-ZА-Я])", text)
            russian_parts: list[str] = []
            english_parts: list[str] = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                ru_chars = len(re.findall(r"[а-яА-Я]", sentence))
                en_words = len(re.findall(r"\b[A-Z][a-z]+", sentence))
                if ru_chars > en_words * 2:
                    russian_parts.append(sentence.strip())
                elif en_words > 0 and ru_chars == 0:
                    english_parts.append(sentence.strip())
                elif ru_chars > 0:
                    russian_parts.append(sentence.strip())
            if russian_parts and len(russian_parts) >= len(english_parts):
                text = ". ".join(russian_parts)
                if text and text[-1] not in ".!?":
                    text += "."

        if "\n\n" in text:
            first, *rest = [part.strip() for part in text.split("\n\n") if part.strip()]
            if rest:
                second = rest[0]
                first_has_ru = bool(re.search(r"[а-яА-Я]", first))
                second_has_ru = bool(re.search(r"[а-яА-Я]", second))
                if first_has_ru and not second_has_ru and len(second) < len(first) * 1.5:
                    text = first
                elif not first_has_ru and second_has_ru:
                    text = second

        def replace_parentheses(match: re.Match[str]) -> str:
            content = match.group(1)
            if not re.search(r"[а-яА-Я]", content):
                return ""
            return match.group(0)

        text = re.sub(r"\(([^)]+)\)", replace_parentheses, text)
        text = re.sub(r"^Здравствуйте[^!]*!\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"User\s*(message)?\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Butler\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Response\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^[:\-\s]+", "", text.strip())
        return text.strip()
