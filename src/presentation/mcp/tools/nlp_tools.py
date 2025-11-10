"""MCP NLP tools for intent parsing including digest intent recognition."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.presentation.mcp.server import mcp

logger = logging.getLogger(__name__)

# Digest keywords with variations and typos tolerance
DIGEST_KEYWORDS_RU = {
    "дайджест",
    "дайджест",
    "дайдж",
    "дайдже",
    "дайдж",
    "дайджтест",
    "digest",
    "дigest",
    "дигест",
    "диджест",
    "дайт",
    "дайтт",
    "сводка",
    "сводку",
    "сводки",
    "выжимка",
    "выжимку",
    "краткое",
    "краткую",
    "краткое содержание",
    "что нового",
    "что было",
    "новости",
    "посты",
    "отчет",
    "отчет",
    "отчет за",
    "отчеты",
}

DIGEST_KEYWORDS_EN = {
    "digest",
    "summary",
    "summaries",
    "summary of",
    "summary for",
    "what's new",
    "what was",
    "news",
    "posts",
    "report",
    "reports",
}

# Action keywords
ACTION_KEYWORDS_RU = {
    "дай",
    "дайт",
    "дай",
    "дайте",
    "дайтт",
    "дайтe",
    "дай",
    "покажи",
    "покажи",
    "покаж",
    "показать",
    "где",
    "где",
    "где",
    "где",
    "где",
    "где",
    "пришли",
    "пришли",
    "пришли",
    "отправь",
    "отправь",
    "сгенерируй",
    "создай",
    "сделай",
    "подготовь",
}

ACTION_KEYWORDS_EN = {
    "give",
    "show",
    "where",
    "send",
    "generate",
    "create",
    "make",
    "prepare",
    "get",
    "fetch",
    "bring",
    "deliver",
}


# Tolerance for typos using Levenshtein-like matching
def _fuzzy_match(word: str, pattern: str, max_distance: int = 1) -> bool:
    """Simple fuzzy matching for typos.

    Args:
        word: Word to check
        pattern: Pattern to match against
        max_distance: Maximum allowed character differences

    Returns:
        True if word matches pattern with tolerance
    """
    word_lower = word.lower()
    pattern_lower = pattern.lower()

    # Exact match
    if word_lower == pattern_lower:
        return True

    # Check if pattern is substring (allows typos like "дайт" -> "дайджест")
    if pattern_lower in word_lower or word_lower in pattern_lower:
        return True

    # Simple Levenshtein distance check
    if len(word_lower) <= len(pattern_lower) + max_distance:
        if len(pattern_lower) <= len(word_lower) + max_distance:
            # Count differences
            min_len = min(len(word_lower), len(pattern_lower))
            matches = sum(
                1 for i in range(min_len) if word_lower[i] == pattern_lower[i]
            )
            if matches >= min_len - max_distance:
                return True

    return False


def _contains_digest_keyword(text: str) -> bool:
    """Check if text contains digest-related keywords (with typo tolerance).

    Args:
        text: Input text

    Returns:
        True if digest intent detected
    """
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)

    # Check Russian keywords
    for keyword in DIGEST_KEYWORDS_RU:
        if keyword in text_lower:
            return True
        # Check fuzzy match for each word
        for word in words:
            if _fuzzy_match(word, keyword):
                return True

    # Check English keywords
    for keyword in DIGEST_KEYWORDS_EN:
        if keyword in text_lower:
            return True
        for word in words:
            if _fuzzy_match(word, keyword):
                return True

    return False


def _contains_action_keyword(text: str) -> bool:
    """Check if text contains action keywords for digest request.

    Args:
        text: Input text

    Returns:
        True if action keyword found
    """
    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)

    # Check Russian actions
    for keyword in ACTION_KEYWORDS_RU:
        if keyword in text_lower:
            return True
        for word in words:
            if _fuzzy_match(word, keyword):
                return True

    # Check English actions
    for keyword in ACTION_KEYWORDS_EN:
        if keyword in text_lower:
            return True
        for word in words:
            if _fuzzy_match(word, keyword):
                return True

    return False


@mcp.tool()
async def parse_digest_intent(
    text: str, user_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Parse natural language request for digest generation.

    Purpose:
        Recognize user requests for PDF digest generation from Telegram channels.
        Handles variations, typos, and different phrasings in Russian and English.

    Args:
        text: User's natural language request
        user_context: Optional additional context (user_id, timezone, etc.)

    Returns:
        Dict with:
        - intent_type: "digest" if digest request detected, "unknown" otherwise
        - confidence: Float (0.0-1.0) indicating confidence level
        - hours: Number of hours to look back (default 24)
        - mcp_tools: List of MCP tool names to call in sequence
        - needs_clarification: Whether clarification is needed
        - questions: List of clarifying questions if needed

    Examples:
        >>> await parse_digest_intent("дайджест")
        {
            "intent_type": "digest",
            "confidence": 0.9,
            "hours": 24,
            "mcp_tools": ["get_posts_from_db", "summarize_posts", "format_digest_markdown", "combine_markdown_sections", "convert_markdown_to_pdf"],
            "needs_clarification": False
        }

        >>> await parse_digest_intent("дайт сюда дайджест")
        {
            "intent_type": "digest",
            "confidence": 0.95,
            "hours": 24,
            "mcp_tools": [...],
            "needs_clarification": False
        }

        >>> await parse_digest_intent("где digest")
        {
            "intent_type": "digest",
            "confidence": 0.85,
            "hours": 24,
            "mcp_tools": [...],
            "needs_clarification": False
        }
    """
    user_context = user_context or {}
    text_lower = text.lower().strip()

    # Check if this is a digest request
    has_digest_keyword = _contains_digest_keyword(text_lower)
    has_action_keyword = _contains_action_keyword(text_lower)

    # Calculate confidence
    confidence = 0.0
    if has_digest_keyword and has_action_keyword:
        confidence = 0.95  # High confidence: both action and digest keywords
    elif has_digest_keyword:
        confidence = 0.85  # Medium-high: digest keyword present
    elif has_action_keyword and any(
        word in text_lower
        for word in ["пост", "post", "канал", "channel", "новости", "news"]
    ):
        confidence = 0.80  # Medium: action + post/channel context
    else:
        # Not a digest request
        return {
            "intent_type": "unknown",
            "confidence": 0.0,
            "hours": 24,
            "mcp_tools": [],
            "needs_clarification": False,
            "questions": [],
        }

    # Extract hours if specified (e.g., "за последние 7 дней", "last 7 days")
    hours = 24  # Default
    hours_patterns = [
        (
            r"за\s+последние\s+(\d+)\s+(?:час|часа|часов|hour|hours)",
            lambda m: int(m.group(1)),
        ),
        (r"за\s+(\d+)\s+(?:час|часа|часов|hour|hours)", lambda m: int(m.group(1))),
        (r"last\s+(\d+)\s+(?:hour|hours)", lambda m: int(m.group(1))),
        (r"(\d+)\s+(?:час|часа|часов|hour|hours)", lambda m: int(m.group(1))),
        (
            r"за\s+последние\s+(\d+)\s+(?:день|дня|дней|day|days)",
            lambda m: int(m.group(1)) * 24,
        ),
        (r"за\s+(\d+)\s+(?:день|дня|дней|day|days)", lambda m: int(m.group(1)) * 24),
        (r"last\s+(\d+)\s+(?:day|days)", lambda m: int(m.group(1)) * 24),
        (r"(\d+)\s+(?:день|дня|дней|day|days)", lambda m: int(m.group(1)) * 24),
    ]

    for pattern, extractor in hours_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                hours = extractor(match)
                # Limit to reasonable range (1 hour to 7 days)
                hours = max(1, min(hours, 168))  # 168 hours = 7 days
                break
            except (ValueError, IndexError):
                continue

    # Define MCP tools needed for digest generation
    mcp_tools = [
        "get_posts_from_db",  # Step 1: Get posts from MongoDB
        "summarize_posts",  # Step 2: Summarize posts for each channel
        "format_digest_markdown",  # Step 3: Format as markdown
        "combine_markdown_sections",  # Step 4: Combine sections
        "convert_markdown_to_pdf",  # Step 5: Convert to PDF
    ]

    # Check if clarification needed (e.g., time period not specified and confidence is low)
    needs_clarification = confidence < 0.7

    questions = []
    if needs_clarification:
        questions.append(
            "За какой период времени нужен дайджест? (по умолчанию 24 часа)"
        )

    return {
        "intent_type": "digest",
        "confidence": confidence,
        "hours": hours,
        "mcp_tools": mcp_tools,
        "needs_clarification": needs_clarification,
        "questions": questions,
    }


@mcp.tool()
async def parse_task_intent(
    text: str, user_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Parse free-form text into a structured task intent.

    Args:
        text: User-provided natural language request
        user_context: Optional additional context (timezone, locale, user prefs)

    Returns:
        Parsed intent as a dictionary
    """
    try:
        # IntentOrchestrator will use ResilientLLMClient internally
        orchestrator = IntentOrchestrator()
        result = await orchestrator.parse_task_intent(text, context=user_context or {})
        return result.model_dump()
    except Exception as e:
        logger.error(f"Failed to parse intent: {e}", exc_info=True)
        # Return minimal valid intent on failure
        return {
            "title": text[:100] if text else "Task",
            "description": "",
            "deadline": None,
            "priority": "medium",
            "tags": [],
            "needs_clarification": False,
            "questions": [],
        }
