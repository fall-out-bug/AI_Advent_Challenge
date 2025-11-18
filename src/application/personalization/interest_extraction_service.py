"""Interest extraction service for user profile enrichment."""

import json
import re
import time
from typing import TYPE_CHECKING, List, Protocol, Tuple

from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    interest_extraction_duration_seconds,
    interest_extraction_total,
)

logger = get_logger("interest_extraction_service")


class LLMClient(Protocol):
    """Protocol for LLM client.

    Purpose:
        Defines interface for LLM text generation.
    """

    async def generate(
        self, prompt: str, temperature: float = 0.2, max_tokens: int = 256
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text response.
        """
        ...


class InterestExtractionService:
    """Service for extracting user interests from conversation history.

    Purpose:
        Analyzes conversation history to extract recurring topics,
        technologies, or domains the user cares about.
        Filters sensitive data and merges with existing interests.

    Attributes:
        llm_client: Client for LLM generation.
        max_topics: Maximum number of topics to extract (default: 7).

    Example:
        >>> service = InterestExtractionService(llm_client, max_topics=7)
        >>> summary, interests = await service.extract_interests(events, [])
        >>> len(interests) <= 7
        True
    """

    # Patterns for detecting sensitive data
    SENSITIVE_PATTERNS = [
        r"(api[_-]?key|token|password|secret|bearer)\s*[=:]\s*['\"]?[\w-]+",
        r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
        r"/home/[\w/]+|/var/[\w/]+|C:\\Users\\[\w\\]+",  # File paths
        r"\d{13,19}",  # User IDs (Telegram)
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Emails
    ]

    def __init__(self, llm_client: LLMClient, max_topics: int = 7) -> None:
        """Initialize service with LLM client.

        Args:
            llm_client: Client for LLM generation.
            max_topics: Maximum topics to extract (default: 7).
        """
        self.llm_client = llm_client
        self.max_topics = max_topics
        logger.info(
            "InterestExtractionService initialized",
            extra={"max_topics": max_topics},
        )

    async def extract_interests(
        self, events: List[UserMemoryEvent], existing_topics: List[str]
    ) -> Tuple[str, List[str]]:
        """Extract summary and interests from conversation.

        Purpose:
            Analyze conversation history to extract recurring topics
            and generate summary. Filters sensitive data and merges
            with existing interests for stability.

        Args:
            events: List of memory events to analyze.
            existing_topics: Current preferred_topics from profile.

        Returns:
            Tuple of (summary_text, interests_list).
            interests_list is stable (3-7 items), no sensitive data.

        Example:
            >>> events = [UserMemoryEvent.create_user_event("123", "Python")]
            >>> summary, interests = await service.extract_interests(events, [])
            >>> "Python" in interests
            True
        """
        start_time = time.time()

        if not events:
            logger.warning("No events provided for interest extraction")
            return "", existing_topics

        try:
            prompt = self._build_prompt(events, existing_topics)

            response = await self.llm_client.generate(
                prompt=prompt, temperature=0.3, max_tokens=512
            )

            # Parse JSON: {"summary": "...", "interests": [...]}
            data = json.loads(response.strip())
            summary = data.get("summary", "")
            new_topics = data.get("interests", [])

            # Filter sensitive data
            clean_topics = [
                t for t in new_topics if not self._contains_sensitive_data(t)
            ]

            # Merge with existing topics
            merged = self._merge_interests(existing_topics, clean_topics)

            duration = time.time() - start_time
            interest_extraction_duration_seconds.observe(duration)
            interest_extraction_total.labels(status="success").inc()

            logger.info(
                "Interests extracted successfully",
                extra={
                    "events_count": len(events),
                    "new_topics": new_topics,
                    "clean_topics": clean_topics,
                    "merged_topics": merged,
                    "existing_topics": existing_topics,
                    "duration_seconds": round(duration, 2),
                },
            )

            return summary, merged

        except json.JSONDecodeError as e:
            duration = time.time() - start_time
            interest_extraction_duration_seconds.observe(duration)
            interest_extraction_total.labels(status="parse_error").inc()

            logger.warning(
                "Failed to parse interests JSON",
                extra={"error": str(e), "response_preview": response[:200]},
            )
            # Fallback: return basic summary, keep existing topics
            return self._fallback_summary(events), existing_topics

        except KeyError as e:
            duration = time.time() - start_time
            interest_extraction_duration_seconds.observe(duration)
            interest_extraction_total.labels(status="parse_error").inc()

            logger.warning(
                "Missing key in interests JSON",
                extra={"error": str(e), "response_preview": response[:200]},
            )
            return self._fallback_summary(events), existing_topics

        except Exception as e:
            duration = time.time() - start_time
            interest_extraction_duration_seconds.observe(duration)
            interest_extraction_total.labels(status="llm_error").inc()

            logger.error(
                "Interest extraction failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            # Fallback: return basic summary, keep existing topics
            return self._fallback_summary(events), existing_topics

    def _build_prompt(
        self, events: List[UserMemoryEvent], existing_topics: List[str]
    ) -> str:
        """Build LLM prompt for interest extraction.

        Purpose:
            Construct prompt for analyzing conversation and extracting
            topics. Uses template from config if available.

        Args:
            events: List of memory events.
            existing_topics: Current preferred_topics.

        Returns:
            Formatted prompt string.
        """
        # Load prompt template from config
        try:
            from src.application.personalization.templates import (
                get_interest_extraction_prompt,
            )

            events_text = "\n".join([
                f"- {event.role}: {event.content[:200]}"
                for event in events[-50:]  # Last 50 events for context
            ])

            existing_str = (
                ", ".join(existing_topics) if existing_topics else "none"
            )

            template = get_interest_extraction_prompt()
            return template.format(events=events_text, existing_topics=existing_str)

        except (ImportError, AttributeError, KeyError):
            # Fallback to inline prompt if template not available
            events_text = "\n".join([
                f"- {event.role}: {event.content[:200]}"
                for event in events[-50:]
            ])

            existing_str = (
                ", ".join(existing_topics) if existing_topics else "none"
            )

            return f"""Analyze conversation and extract user interests.

Rules:
- Identify 3-7 recurring topics, technologies, or domains
- Use canonical names (Python, Docker, Clean Architecture)
- EXCLUDE: API keys, passwords, file paths, personal info
- Prefer stability: keep existing topics if still relevant

Conversation:
{events_text}

Existing interests: {existing_str}

Output JSON:
{{"summary": "Brief overview (max 300 tokens)", "interests": ["Topic1", "Topic2", ...]}}

JSON:"""

    def _contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive patterns.

        Purpose:
            Validate that extracted topic doesn't contain sensitive data
            like API keys, passwords, file paths, etc.

        Args:
            text: Topic candidate string.

        Returns:
            True if sensitive data detected.

        Example:
            >>> service._contains_sensitive_data("sk-1234567890abcdef")
            True
            >>> service._contains_sensitive_data("Python")
            False
        """
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _merge_interests(
        self, existing: List[str], new: List[str]
    ) -> List[str]:
        """Merge existing + new topics, keeping stable top-N.

        Purpose:
            Combine new interests with existing, preserving stability.
            Prioritizes topics that appear in both lists.

        Args:
            existing: Current preferred_topics from profile.
            new: Newly extracted topics.

        Returns:
            Merged list of topics (max max_topics length).

        Example:
            >>> existing = ["Python", "Docker"]
            >>> new = ["Python", "Clean Architecture"]
            >>> service._merge_interests(existing, new)
            ['Python', 'Docker', 'Clean Architecture']
        """
        # Normalize for comparison (case-insensitive)
        existing_norm = {t.lower(): t for t in existing}
        new_norm = {t.lower(): t for t in new}

        # Priority: topics in both lists (confirmed interests)
        confirmed = [
            existing_norm[key] for key in existing_norm if key in new_norm
        ]

        # Add remaining existing topics
        for topic in existing:
            if topic not in confirmed:
                confirmed.append(topic)

        # Add new topics (if space remains)
        for topic in new:
            if topic not in confirmed and len(confirmed) < self.max_topics:
                confirmed.append(topic)

        return confirmed[: self.max_topics]

    def _fallback_summary(self, events: List[UserMemoryEvent]) -> str:
        """Generate basic summary without LLM.

        Purpose:
            Fallback summary when LLM extraction fails.
            Simple text-based summary.

        Args:
            events: List of memory events.

        Returns:
            Basic summary string.
        """
        return f"User discussed various topics in {len(events)} messages."

