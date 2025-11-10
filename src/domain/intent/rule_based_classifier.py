"""Rule-based intent classifier.

Uses regex patterns to classify user messages with confidence scores.
Following Python Zen: Simple is better than complex.
"""

import time
from typing import Optional

from src.domain.intent.intent_classifier import IntentResult, IntentType
from src.domain.intent.rules import ALL_RULES
from src.infrastructure.logging import get_logger

logger = get_logger("rule_based_classifier")


class RuleBasedClassifier:
    """Rule-based intent classifier using regex patterns.

    Classifies messages using pre-defined regex patterns with confidence scores.
    Extracts entities using provided extractor functions.

    Attributes:
        rules: List of rule tuples (pattern, intent_type, confidence, entity_extractors)
    """

    def __init__(self, rules: Optional[list] = None):
        """Initialize rule-based classifier.

        Args:
            rules: List of rule tuples. If None, uses default rules from rules module.
        """
        self.rules = rules or ALL_RULES
        logger.info(f"RuleBasedClassifier initialized with {len(self.rules)} rules")

    def classify(self, message: str) -> IntentResult:
        """Classify message using rule patterns.

        Args:
            message: User message text

        Returns:
            IntentResult with highest confidence match, or IDLE if no match

        Example:
            >>> classifier = RuleBasedClassifier()
            >>> result = classifier.classify("Create a task")
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
                source="rule",
                entities={},
                latency_ms=latency_ms,
            )

        best_match: Optional[IntentResult] = None
        best_confidence = 0.0

        # Try all rules and find best match
        for pattern, intent_type, confidence, entity_extractors in self.rules:
            match = pattern.search(message)
            if match:
                # Extract entities using provided extractor functions
                entities = {}
                for entity_name, extractor in entity_extractors.items():
                    try:
                        entity_value = extractor(match)
                        if entity_value:
                            entities[entity_name] = entity_value
                    except Exception as e:
                        logger.debug(f"Failed to extract entity {entity_name}: {e}")

                # Update best match if this has higher confidence
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = IntentResult(
                        intent=intent_type,
                        confidence=confidence,
                        source="rule",
                        entities=entities,
                        latency_ms=0.0,  # Will be set after timing
                    )
                    logger.debug(
                        f"Rule match: intent={intent_type.value}, confidence={confidence:.2f}, "
                        f"pattern={pattern.pattern[:50]}"
                    )

        latency_ms = (time.time() - start_time) * 1000

        # Return best match or default to IDLE
        if best_match:
            best_match.latency_ms = latency_ms
            logger.info(
                f"Rule-based classification: intent={best_match.intent.value}, "
                f"confidence={best_match.confidence:.2f}, entities={len(best_match.entities)}, "
                f"latency={latency_ms:.2f}ms"
            )
            return best_match

        # No match found - return IDLE with low confidence
        logger.debug(f"No rule match for message: {message[:100]}")
        return IntentResult(
            intent=IntentType.IDLE,
            confidence=0.3,
            source="rule",
            entities={},
            latency_ms=latency_ms,
        )
