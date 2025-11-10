"""LLM-based intent parser.

Extracted from IntentOrchestrator to follow Single Responsibility Principle.
Following the Zen of Python: Explicit is better than implicit.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Optional

from src.domain.entities.intent import IntentParseResult
from src.domain.exceptions.intent_exceptions import LLMParseError
from src.infrastructure.llm.prompts import get_intent_parse_prompt

# Add shared to path for imports
shared_path = Path(__file__).parent.parent.parent.parent / "shared"
if shared_path.exists():
    sys.path.insert(0, str(shared_path))

logger = logging.getLogger(__name__)

# Try UnifiedModelClient first, but prefer ResilientLLMClient since it's more reliable
USE_UNIFIED_CLIENT = False
try:
    from shared_package.clients.unified_client import UnifiedModelClient

    USE_UNIFIED_CLIENT = False  # Force use of ResilientLLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    USE_UNIFIED_CLIENT = False

# Always use ResilientLLMClient as fallback
if not LLM_AVAILABLE:
    try:
        pass

        LLM_AVAILABLE = True
        USE_UNIFIED_CLIENT = False
    except ImportError:
        LLM_AVAILABLE = False


class IntentLLMParser:
    """Parser using LLM for intent extraction.

    Single responsibility: parse intent using LLM.
    """

    def __init__(
        self,
        model_name: str = "mistral",
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> None:
        """Initialize LLM parser.

        Args:
            model_name: LLM model name (mistral, qwen, etc.)
            temperature: LLM temperature for generation
            max_tokens: Maximum tokens for LLM response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm_client: Optional[UnifiedModelClient] = None
        self._fallback_llm_client = None  # ResilientLLMClient fallback
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize LLM clients."""
        if not LLM_AVAILABLE:
            logger.warning("LLM not available, parser will fail gracefully")
            return

        try:
            if USE_UNIFIED_CLIENT:
                self.llm_client = UnifiedModelClient(timeout=30.0)
                logger.info(
                    f"IntentLLMParser initialized with UnifiedModelClient: {self.model_name}"
                )
            else:
                from src.infrastructure.clients.llm_client import ResilientLLMClient

                self._fallback_llm_client = ResilientLLMClient()
                logger.info(
                    f"IntentLLMParser initialized with ResilientLLMClient: {self.model_name}"
                )
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")

    def _detect_language(self, text: str) -> str:
        """Detect language (RU/EN) from text.

        Args:
            text: Input text

        Returns:
            Language code: "ru" or "en"
        """
        ru_chars = len(re.findall(r"[а-яё]", text.lower()))
        en_chars = len(re.findall(r"[a-z]", text.lower()))
        return "ru" if ru_chars > en_chars else "en"

    async def parse(self, text: str, context: Dict) -> Optional[IntentParseResult]:
        """Parse intent using LLM.

        Args:
            text: User input
            context: Conversation context

        Returns:
            IntentParseResult or None if parsing fails

        Raises:
            LLMParseError: If LLM parsing fails unexpectedly
        """
        if not self.llm_client and not self._fallback_llm_client:
            logger.debug("No LLM client available")
            return None

        language = self._detect_language(text)
        prompt = get_intent_parse_prompt(text, language=language, context=context)

        try:
            logger.debug(
                f"Calling LLM with model={self.model_name}, max_tokens={self.max_tokens}"
            )

            response_text = await self._call_llm(prompt)
            if not response_text:
                return None

            logger.debug(f"LLM response (first 200 chars): {response_text[:200]}")

            parsed = self._parse_response(response_text)
            if not parsed:
                logger.warning(f"Failed to parse LLM response: {response_text[:200]}")
                return None

            logger.debug(f"Parsed LLM response: {parsed}")
            return IntentParseResult(
                title=parsed.get("title", text.strip()),
                description=parsed.get("description"),
                deadline_iso=parsed.get("deadline_iso"),
                priority=parsed.get("priority", "medium"),
                tags=parsed.get("tags", []),
                needs_clarification=parsed.get("needs_clarification", False),
                questions=parsed.get("questions", []),
            )
        except Exception as e:
            raise LLMParseError(f"LLM parsing error: {e}", original_error=e) from e

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM with prompt.

        Args:
            prompt: Prompt text

        Returns:
            Response text or None
        """
        if self._fallback_llm_client:
            return await self._fallback_llm_client.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        elif self.llm_client:
            response = await self.llm_client.make_request(
                model_name=self.model_name,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.response if hasattr(response, "response") else str(response)
        else:
            logger.warning("No LLM client available")
            return None

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response from LLM.

        Args:
            response_text: LLM response text

        Returns:
            Parsed dictionary or None if parsing fails
        """
        if not response_text or not response_text.strip():
            logger.warning("Empty LLM response")
            return None

        # Try to extract JSON from response (handles cases where LLM adds extra text)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                logger.debug("Successfully parsed JSON from response")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse extracted JSON: {e}, text: {json_match.group(0)[:200]}"
                )

        # Try parsing entire response as JSON
        try:
            parsed = json.loads(response_text.strip())
            logger.debug("Successfully parsed entire response as JSON")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse LLM response as JSON: {e}, response: {response_text[:200]}"
            )
            return None
