"""Chat handler for Butler Agent IDLE mode.

Handles general conversation and fallback responses.
Following Python Zen: Simple is better than complex.
"""

import logging
import re
from typing import Optional

from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.llm_client import LLMClientProtocol

logger = logging.getLogger(__name__)


class ChatHandler(Handler):
    """Handler for IDLE mode - general conversation.

    Uses LLM for natural conversation responses.
    Following SOLID: Single Responsibility Principle.
    """

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
    ):
        """Initialize chat handler.

        Args:
            llm_client: LLM client for conversation
            default_model: Default model name
            hybrid_classifier: Optional hybrid intent classifier for intent confirmation
        """
        self.llm_client = llm_client
        self.default_model = default_model
        self.hybrid_classifier = hybrid_classifier

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle general conversation.

        Uses hybrid classifier to confirm IDLE intent and provide context-aware responses.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text from LLM
        """
        # Use hybrid classifier to confirm IDLE intent (if available)
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                logger.debug(
                    f"ChatHandler: intent={intent_result.intent.value}, "
                    f"confidence={intent_result.confidence:.2f}, entities={intent_result.entities}"
                )

                # If intent is clearly NOT IDLE, log warning (but still respond as chat)
                if intent_result.intent not in [
                    IntentType.IDLE,
                    IntentType.GENERAL_CHAT,
                    IntentType.GENERAL_QUESTION,
                ]:
                    logger.debug(
                        f"ChatHandler received non-IDLE intent: {intent_result.intent.value} "
                        f"(confidence: {intent_result.confidence:.2f}). "
                        f"Responding as chat but intent may need different handler."
                    )
            except Exception as e:
                logger.debug(f"Hybrid classifier failed in ChatHandler: {e}")

        try:
            prompt = self.CHAT_PROMPT.format(message=message)
            response = await self.llm_client.make_request(
                model_name=self.default_model,
                prompt=prompt,
                max_tokens=256,
                temperature=0.7,
            )
            # Clean response from duplicate prefixes and formatting
            cleaned = self._clean_response(response)
            return cleaned
        except Exception as e:
            logger.error(f"Chat handling failed: {e}", exc_info=True)
            return "I'm here to help! Try asking me to create a task or show data insights."

    def _clean_response(self, response: str) -> str:
        """Clean LLM response from formatting artifacts.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned response text
        """
        text = response.strip()

        # Remove common prefixes if present (more aggressive)
        prefixes_to_remove = [
            "User:",
            "Butler:",
            "Assistant:",
            "AI:",
        ]
        for prefix in prefixes_to_remove:
            # Remove at start
            if text.startswith(prefix):
                text = text[len(prefix) :].strip()
            # Remove anywhere in text (LLM sometimes includes it in middle)
            text = re.sub(rf"^{re.escape(prefix)}\s*", "", text, flags=re.MULTILINE)
            text = re.sub(rf"\s*{re.escape(prefix)}\s*", " ", text)

        # Detect and remove bilingual responses (Russian + English)
        # Check if text contains both Russian and English
        has_russian = bool(re.search(r"[а-яА-Я]", text))
        has_english = bool(
            re.search(r"\b[A-Z][a-z]+", text)
        )  # English words starting with capital

        if has_russian and has_english:
            # Split by periods, commas, or sentence boundaries
            sentences = re.split(r"[.!?]\s+|,\s+(?=[A-ZА-Я])", text)
            russian_parts = []
            english_parts = []

            for sent in sentences:
                if not sent.strip():
                    continue
                # Count Russian vs English characters
                ru_chars = len(re.findall(r"[а-яА-Я]", sent))
                en_words = len(re.findall(r"\b[A-Z][a-z]+", sent))

                # If Russian chars dominate, it's Russian
                if ru_chars > en_words * 2:
                    russian_parts.append(sent.strip())
                elif en_words > 0 and ru_chars == 0:
                    english_parts.append(sent.strip())
                elif ru_chars > 0:
                    # Mixed or mostly Russian
                    russian_parts.append(sent.strip())

            # Keep Russian if we have Russian parts, otherwise keep what we have
            if russian_parts and len(russian_parts) >= len(english_parts):
                text = ". ".join(russian_parts)
                if text and not text.endswith((".", "!", "?")):
                    text += "."

        # Remove duplicate text patterns (e.g., "Russian (English)")
        # Split by common separators and keep only first meaningful part
        if "\n\n" in text:
            parts = text.split("\n\n")
            if len(parts) > 1:
                # Check if second part is a translation
                first = parts[0].strip()
                second = parts[1].strip()
                # If second part is shorter and doesn't contain Russian, likely translation
                if first and second:
                    first_has_ru = bool(re.search(r"[а-яА-Я]", first))
                    second_has_ru = bool(re.search(r"[а-яА-Я]", second))
                    if (
                        first_has_ru
                        and not second_has_ru
                        and len(second) < len(first) * 1.5
                    ):
                        text = first
                    elif not first_has_ru and second_has_ru:
                        text = second

        # Remove parenthetical translations like "(Hello there, user!)" or "(English text)"
        # More aggressive: remove any parentheses that contain English-only text
        def replace_parentheses(match):
            content = match.group(1)
            # If content is English-only (no Russian), remove it
            if not re.search(r"[а-яА-Я]", content):
                return ""
            return match.group(0)  # Keep if contains Russian

        text = re.sub(r"\(([^)]+)\)", replace_parentheses, text)

        # Remove redundant greeting patterns
        text = re.sub(r"^Здравствуйте[^!]*!\s*", "", text, flags=re.IGNORECASE)

        # Remove "User:", "Butler:", "User message:", "Response:" patterns anywhere in text
        text = re.sub(r"User\s*(message)?\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Butler\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"Response\s*:\s*", "", text, flags=re.IGNORECASE)

        # Clean up multiple spaces
        text = re.sub(r"\s+", " ", text)

        # Final cleanup - remove any remaining prefix artifacts
        text = text.strip()
        # Remove leading punctuation that might be left from prefix removal
        text = re.sub(r"^[:\-\s]+", "", text)

        return text.strip()
