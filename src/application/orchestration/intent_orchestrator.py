"""Intent parsing orchestrator using LLM for natural language understanding."""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.domain.entities.intent import IntentParseResult
from src.infrastructure.llm.prompts import get_intent_parse_prompt

# Add shared to path for imports
shared_path = Path(__file__).parent.parent.parent.parent / "shared"
if shared_path.exists():
    sys.path.insert(0, str(shared_path))

# Try UnifiedModelClient first, but prefer ResilientLLMClient since it's more reliable
USE_UNIFIED_CLIENT = False
try:
    from shared_package.clients.unified_client import UnifiedModelClient
    # Only use UnifiedModelClient if we can test it works
    # For now, prefer ResilientLLMClient as it's more reliable in Docker
    USE_UNIFIED_CLIENT = False  # Force use of ResilientLLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    USE_UNIFIED_CLIENT = False

# Always use ResilientLLMClient as fallback
if not LLM_AVAILABLE:
    try:
        from src.infrastructure.clients.llm_client import ResilientLLMClient
        LLM_AVAILABLE = True
        USE_UNIFIED_CLIENT = False
    except ImportError:
        LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

# Fallback parser constants
PRIORITY_KEYWORDS = {
    "high": {"urgent", "high", "asap", "срочно", "важно", "высокий"},
    "medium": {"soon", "important", "medium", "скоро", "важный", "средний"},
    "low": {"later", "low", "someday", "позже", "низкий"},
}

TIME_EXPRESSIONS = {
    "ru": {
        "today": {"сегодня", "сегодняшний"},
        "tomorrow": {"завтра", "завтрашний"},
        "yesterday": {"вчера"},
    },
    "en": {
        "today": {"today"},
        "tomorrow": {"tomorrow"},
        "yesterday": {"yesterday"},
    },
}


@dataclass
class IntentOrchestrator:
    """Parse natural language into structured task intent using LLM.

    Uses local LLM (Mistral/Qwen) for intent parsing with fallback to
    deterministic parser if LLM is unavailable.

    Methods:
        parse_task_intent: Extract fields using LLM or fallback parser
        generate_clarification_questions: Produce questions for missing fields
        validate_intent_completeness: Check completeness and report missing info
    """

    def __init__(
        self,
        model_name: str = "mistral",
        use_llm: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        """Initialize orchestrator.

        Args:
            model_name: LLM model name (mistral, qwen, etc.)
            use_llm: Whether to use LLM (False = deterministic parser only)
            temperature: LLM temperature for generation
            max_tokens: Maximum tokens for LLM response
        """
        self.model_name = model_name
        self.use_llm = use_llm and LLM_AVAILABLE
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.llm_client: Optional[UnifiedModelClient] = None
        self._fallback_llm_client = None  # ResilientLLMClient fallback

        if self.use_llm:
            try:
                if USE_UNIFIED_CLIENT:
                    self.llm_client = UnifiedModelClient(timeout=30.0)
                    logger.info(f"IntentOrchestrator initialized with UnifiedModelClient: {model_name}")
                else:
                    # Use ResilientLLMClient as fallback
                    from src.infrastructure.clients.llm_client import ResilientLLMClient
                    self._fallback_llm_client = ResilientLLMClient()
                    logger.info(f"IntentOrchestrator initialized with ResilientLLMClient: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.use_llm = False

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

    async def parse_task_intent(
        self, text: str, context: Optional[Dict] = None
    ) -> IntentParseResult:
        """Parse natural language task intent using LLM.

        Args:
            text: User's natural language input
            context: Optional conversation context

        Returns:
            IntentParseResult with parsed fields
        """
        context = context or {}

        # Try LLM parsing first
        if self.use_llm and (self.llm_client or self._fallback_llm_client):
            try:
                logger.debug(f"Attempting LLM parsing for text: {text[:100]}")
                result = await self._parse_with_llm(text, context)
                if result:
                    logger.info(f"LLM parsing successful: title={result.title}, deadline={result.deadline_iso}")
                    return result
                else:
                    logger.warning("LLM parsing returned None, using fallback")
            except Exception as e:
                logger.warning(f"LLM parsing failed, using fallback: {e}", exc_info=True)
        else:
            if not self.use_llm:
                logger.debug("LLM disabled, using fallback parser")
            elif not self.llm_client and not self._fallback_llm_client:
                logger.debug("LLM client not available, using fallback parser")

        # Fallback to deterministic parser
        logger.debug("Using fallback deterministic parser")
        return self._parse_with_fallback(text, context)

    async def _parse_with_llm(
        self, text: str, context: Dict
    ) -> Optional[IntentParseResult]:
        """Parse intent using LLM.

        Args:
            text: User input
            context: Conversation context

        Returns:
            IntentParseResult or None if parsing fails
        """
        if not self.use_llm:
            return None

        language = self._detect_language(text)
        prompt = get_intent_parse_prompt(text, language=language, context=context)

        try:
            logger.debug(f"Calling LLM with model={self.model_name}, max_tokens={self.max_tokens}")
            
            # Use ResilientLLMClient if UnifiedModelClient not available
            if self._fallback_llm_client:
                response_text = await self._fallback_llm_client.generate(
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
                response_text = response.response if hasattr(response, "response") else str(response)
            else:
                logger.warning("No LLM client available")
                return None

            logger.debug(f"LLM response (first 200 chars): {response_text[:200]}")
            
            parsed = self._parse_llm_response(response_text)

            if parsed:
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
            else:
                logger.warning(f"Failed to parse LLM response: {response_text[:200]}")
        except Exception as e:
            logger.error(f"LLM parsing error: {e}", exc_info=True)
            return None

        return None

    def _parse_llm_response(self, response_text: str) -> Optional[Dict]:
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
                logger.debug(f"Successfully parsed JSON from response")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse extracted JSON: {e}, text: {json_match.group(0)[:200]}")

        # Try parsing entire response as JSON
        try:
            parsed = json.loads(response_text.strip())
            logger.debug(f"Successfully parsed entire response as JSON")
            return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}, response: {response_text[:200]}")
            return None

    def _parse_with_fallback(self, text: str, context: Dict) -> IntentParseResult:
        """Fallback deterministic parser.

        Args:
            text: User input
            context: Conversation context

        Returns:
            IntentParseResult
        """
        deadline_iso = self._extract_iso_datetime(text)
        priority = self._infer_priority(text)
        title = self._extract_task_title(text)
        description = None

        needs_clarification = deadline_iso is None or not title
        questions: List[str] = []
        if needs_clarification:
            questions = self.generate_clarification_questions(
                title=title, deadline_iso=deadline_iso, priority=priority
            )

        return IntentParseResult(
            title=title,
            description=description,
            deadline_iso=deadline_iso,
            priority=priority,
            tags=[],
            needs_clarification=needs_clarification,
            questions=questions,
        )

    def _extract_task_title(self, text: str) -> str:
        """Extract task title by removing command words and time expressions.

        Args:
            text: Natural language input

        Returns:
            Cleaned task title
        """
        cleaned = text

        command_words = [
            "напомни", "напомнить", "remind", "remind me", "remind me to",
            "добавь", "добавить", "add", "create", "создай", "создать",
            "сделай", "сделать", "do", "make",
        ]

        for cmd in command_words:
            pattern = rf"^{re.escape(cmd)}\s+"
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        time_patterns = [
            r"(?:завтра|tomorrow|сегодня|today|вчера|yesterday)\s+в\s+\d{1,2}(?::\d{2})?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)?",
            r"(?:завтра|tomorrow|сегодня|today|вчера|yesterday)\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|morning|afternoon|evening|night)?",
            r"(?:завтра|tomorrow|сегодня|today|вчера|yesterday)\s+",
            r"\s+в\s+\d{1,2}(?::\d{2})?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)?",
            r"\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|morning|afternoon|evening|night)?",
            r"\s+\d{1,2}(?::\d{2})?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)",
            r"\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?",
        ]

        for pattern in time_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if cleaned else text.strip()

    def generate_clarification_questions(
        self, title: str, deadline_iso: Optional[str], priority: str
    ) -> List[str]:
        """Generate clarifying questions for missing fields.

        Args:
            title: Task title
            deadline_iso: ISO deadline or None
            priority: Priority level

        Returns:
            List of clarifying questions
        """
        questions: List[str] = []
        if not deadline_iso:
            questions.append("What is the deadline (date and time)?")
        if priority not in {"low", "medium", "high"}:
            questions.append("What is the priority? [low, medium, high]")
        if not title:
            questions.append("What should I name the task?")
        return questions

    def validate_intent_completeness(
        self, result: IntentParseResult
    ) -> Tuple[bool, List[str]]:
        """Validate intent completeness.

        Args:
            result: Intent parse result

        Returns:
            Tuple of (is_complete, missing_fields)
        """
        missing: List[str] = []
        if not result.title:
            missing.append("title")
        if result.deadline_iso is None:
            missing.append("deadline")
        if result.priority not in {"low", "medium", "high"}:
            missing.append("priority")
        return (len(missing) == 0, missing)

    def _extract_iso_datetime(self, text: str) -> Optional[str]:
        """Extract ISO datetime from natural language text (fallback).

        Args:
            text: Natural language text

        Returns:
            ISO datetime string or None
        """
        text_lower = text.lower()
        now = datetime.now()

        patterns = [
            r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2})",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                date_part = m.group(1)
                time_part = m.group(2) if m.lastindex and m.lastindex >= 2 else "00:00"
                try:
                    dt = datetime.fromisoformat(f"{date_part} {time_part}")
                    return dt.isoformat()
                except Exception:
                    continue

        date_offset = 0
        target_date = now.date()

        ru_expr = TIME_EXPRESSIONS["ru"]
        en_expr = TIME_EXPRESSIONS["en"]

        if any(word in text_lower for word in ru_expr["tomorrow"]):
            date_offset = 1
        elif any(word in text_lower for word in ru_expr["today"]):
            date_offset = 0
        elif any(word in text_lower for word in ru_expr["yesterday"]):
            date_offset = -1
        elif any(word in text_lower for word in en_expr["tomorrow"]):
            date_offset = 1
        elif any(word in text_lower for word in en_expr["today"]):
            date_offset = 0
        elif any(word in text_lower for word in en_expr["yesterday"]):
            date_offset = -1

        if date_offset != 0:
            target_date = (now + timedelta(days=date_offset)).date()

        time_value = self._extract_time_from_text(text)
        if time_value is None:
            if date_offset != 0:
                return None
            return None

        try:
            dt = datetime.combine(target_date, time_value)
            if dt < now and date_offset == 0:
                dt = datetime.combine(target_date + timedelta(days=1), time_value)
            return dt.isoformat()
        except Exception:
            return None

    def _extract_time_from_text(self, text: str) -> Optional[time]:
        """Extract time from natural language text (fallback).

        Args:
            text: Natural language text

        Returns:
            time object or None
        """
        text_lower = text.lower()

        time_patterns = [
            r"(?:в|at|время|time)\s*(\d{1,2})(?::(\d{2}))?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)?",
            r"^(\d{1,2})(?::(\d{2}))?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)",
            r"(\d{1,2})(?::(\d{2}))?\s*(?:утра|утром|am|morning|дня|днем|pm|afternoon|вечера|вечером|evening|ночи|ночью|night)",
            r"(?:в|at)\s*(\d{1,2})(?::(\d{2}))?",
            r"(\d{1,2}):(\d{2})",
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                hour_str = match.group(1)
                minute_str = match.group(2) if match.lastindex and match.lastindex >= 2 else "00"

                try:
                    hour = int(hour_str)
                    minute = int(minute_str) if minute_str else 0

                    is_pm = False
                    text_after_match = text_lower[match.end():]

                    pm_indicators = ["pm", "вечера", "вечером", "дня", "днем", "ночи", "ночью", "night", "evening", "afternoon"]
                    am_indicators = ["am", "утра", "утром", "morning"]

                    if any(indicator in text_after_match[:20] for indicator in pm_indicators):
                        is_pm = True
                    elif any(indicator in text_after_match[:20] for indicator in am_indicators):
                        is_pm = False
                    elif hour < 12 and any(indicator in text_lower for indicator in pm_indicators):
                        is_pm = True

                    if hour < 12 and is_pm:
                        hour += 12
                    elif hour == 12 and not is_pm:
                        hour = 0

                    if 0 <= hour < 24 and 0 <= minute < 60:
                        return time(hour, minute)
                except (ValueError, IndexError):
                    continue

        return None

    def _infer_priority(self, text: str) -> str:
        """Infer priority from text keywords (fallback).

        Args:
            text: Natural language text

        Returns:
            Priority level: "low", "medium", or "high"
        """
        lowered = text.lower()
        for level, keywords in PRIORITY_KEYWORDS.items():
            if any(k in lowered for k in keywords):
                return level
        return "medium"
