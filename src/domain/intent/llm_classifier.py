"""LLM-based intent classifier.

Uses Mistral-7B via LLMClientProtocol for intent classification.
Following Python Zen: Simple is better than complex.
"""

import asyncio
import json
import re
import time
from typing import Optional

from src.domain.intent.intent_classifier import IntentClassifierProtocol, IntentResult, IntentType
from src.domain.interfaces.llm_client import LLMClientProtocol
from src.infrastructure.logging import get_logger

logger = get_logger("llm_classifier")

# System prompt for intent classification
# Note: Use {{ and }} for literal braces in format strings
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a Telegram bot assistant.

Classify the user message into one of these intent types:
- TASK, TASK_CREATE, TASK_LIST, TASK_UPDATE, TASK_DELETE
- DATA, DATA_DIGEST, DATA_SUBSCRIPTION_LIST, DATA_SUBSCRIPTION_ADD, DATA_SUBSCRIPTION_REMOVE, DATA_STATS
- REMINDERS, REMINDER_SET, REMINDER_LIST, REMINDER_DELETE
- IDLE, GENERAL_CHAT, GENERAL_QUESTION

Return ONLY a JSON object with this structure:
{{
  "intent": "intent_type_name",
  "confidence": 0.8,
  "entities": {{}}
}}

Examples:
- "Create a task to buy milk" → {{"intent": "TASK_CREATE", "confidence": 0.9, "entities": {{"title": "buy milk"}}}}
- "Give me my subscriptions" → {{"intent": "DATA_SUBSCRIPTION_LIST", "confidence": 0.95, "entities": {{}}}}
- "Hello" → {{"intent": "GENERAL_CHAT", "confidence": 0.8, "entities": {{}}}}

Message: {message}"""


class LLMClassifier:
    """LLM-based intent classifier.

    Uses Mistral-7B for intent classification with timeout and error handling.
    Returns fixed confidence of 0.8 for LLM results.

    Attributes:
        llm_client: LLM client protocol implementation
        model_name: Model name to use
        timeout_seconds: Request timeout in seconds
        temperature: Generation temperature (low for classification)
    """

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        model_name: str = "mistral",
        timeout_seconds: float = 5.0,
        temperature: float = 0.2,
    ):
        """Initialize LLM classifier.

        Args:
            llm_client: LLM client protocol implementation
            model_name: Model name to use
            timeout_seconds: Request timeout (default: 5.0)
            temperature: Generation temperature (default: 0.2 for classification)
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        logger.info(
            f"LLMClassifier initialized: model={model_name}, timeout={timeout_seconds}s, "
            f"temperature={temperature}"
        )

    async def classify(self, message: str) -> IntentResult:
        """Classify message using LLM.

        Args:
            message: User message text

        Returns:
            IntentResult with LLM classification, or IDLE on failure

        Example:
            >>> classifier = LLMClassifier(llm_client)
            >>> result = await classifier.classify("Create a task")
            >>> result.intent == IntentType.TASK_CREATE
            True
        """
        start_time = time.time()
        message = message.strip()

        if not message:
            latency_ms = (time.time() - start_time) * 1000
            return IntentResult(
                intent=IntentType.IDLE,
                confidence=0.5,
                source="llm",
                entities={},
                latency_ms=latency_ms,
            )

        try:
            # Build prompt
            prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)

            # Call LLM with timeout
            logger.debug(f"Calling LLM for intent classification: {message[:100]}")
            response_text = await asyncio.wait_for(
                self.llm_client.make_request(
                    model_name=self.model_name,
                    prompt=prompt,
                    max_tokens=200,  # Intent classification doesn't need many tokens
                    temperature=self.temperature,
                ),
                timeout=self.timeout_seconds,
            )

            # Parse response
            parsed = self._parse_response(response_text)
            if parsed:
                intent_type = self._parse_intent_type(parsed.get("intent"))
                entities = parsed.get("entities", {})
                confidence = parsed.get("confidence", 0.8)  # Default LLM confidence

                latency_ms = (time.time() - start_time) * 1000
                result = IntentResult(
                    intent=intent_type,
                    confidence=min(confidence, 0.95),  # Cap at 0.95 for LLM
                    source="llm",
                    entities=entities,
                    latency_ms=latency_ms,
                )
                logger.info(
                    f"LLM classification: intent={result.intent.value}, confidence={result.confidence:.2f}, "
                    f"latency={latency_ms:.2f}ms"
                )
                return result
            else:
                logger.warning(f"Failed to parse LLM response: {response_text[:200]}")
        except asyncio.TimeoutError:
            logger.warning(f"LLM classification timeout after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"LLM classification failed: {e}", exc_info=True)

        # Fallback to IDLE on error
        latency_ms = (time.time() - start_time) * 1000
        return IntentResult(
            intent=IntentType.IDLE,
            confidence=0.3,
            source="llm",
            entities={},
            latency_ms=latency_ms,
        )

    def _parse_response(self, response_text: str) -> Optional[dict]:
        """Parse JSON response from LLM.

        Args:
            response_text: LLM response text

        Returns:
            Parsed dictionary or None if parsing fails
        """
        if not response_text or not response_text.strip():
            return None

        # Try to extract JSON from response (handles cases where LLM adds extra text)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return parsed
            except json.JSONDecodeError:
                pass

        # Try parsing entire response as JSON
        try:
            parsed = json.loads(response_text.strip())
            return parsed
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse LLM response as JSON: {response_text[:200]}")
            return None

    def _parse_intent_type(self, intent_str: Optional[str]) -> IntentType:
        """Parse intent type string to IntentType enum.

        Args:
            intent_str: Intent type string from LLM

        Returns:
            IntentType enum value, defaults to IDLE if parsing fails
        """
        if not intent_str:
            return IntentType.IDLE

        # Try to find matching IntentType
        intent_str_upper = intent_str.strip().upper()
        for intent_type in IntentType:
            if intent_type.name == intent_str_upper or intent_type.value.upper() == intent_str_upper:
                return intent_type

        # Try partial matching
        for intent_type in IntentType:
            if intent_str_upper in intent_type.name or intent_str_upper in intent_type.value.upper():
                return intent_type

        logger.warning(f"Unknown intent type from LLM: {intent_str}, defaulting to IDLE")
        return IntentType.IDLE

