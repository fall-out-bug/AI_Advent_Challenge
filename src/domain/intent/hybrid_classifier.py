"""Hybrid intent classifier orchestrating rules, cache, and LLM.

Two-layer architecture:
1. Fast rule-based classification (synchronous, <100ms)
2. LLM fallback with caching (async, <5s with cache, ~3s without)

Following Python Zen: Simple is better than complex.
"""

import time

from src.domain.intent.intent_classifier import IntentResult, IntentType
from src.domain.intent.llm_classifier import LLMClassifier
from src.domain.intent.rule_based_classifier import RuleBasedClassifier
from src.infrastructure.cache.intent_cache import IntentCache
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.intent_metrics import IntentMetrics

logger = get_logger("hybrid_classifier")


class HybridIntentClassifier:
    """Hybrid intent classifier orchestrating rules and LLM.

    Classification flow:
    1. Try rule-based classifier (fast, synchronous)
    2. If confidence >= threshold → return rule result
    3. Else → check cache for LLM result
    4. If cache hit → return cached result
    5. Else → call LLM classifier
    6. Cache LLM result
    7. Return LLM result

    Attributes:
        rule_classifier: Rule-based classifier
        llm_classifier: LLM classifier
        cache: Intent result cache
        confidence_threshold: Minimum confidence for rule-based results (default: 0.7)
    """

    def __init__(
        self,
        rule_classifier: RuleBasedClassifier,
        llm_classifier: LLMClassifier,
        cache: IntentCache,
        confidence_threshold: float = 0.7,
    ):
        """Initialize hybrid classifier.

        Args:
            rule_classifier: Rule-based classifier instance
            llm_classifier: LLM classifier instance
            cache: Intent cache instance
            confidence_threshold: Confidence threshold for rule-based results (default: 0.7)
        """
        self.rule_classifier = rule_classifier
        self.llm_classifier = llm_classifier
        self.cache = cache
        self.confidence_threshold = confidence_threshold
        logger.info(
            f"HybridIntentClassifier initialized with confidence_threshold={confidence_threshold}"
        )

    async def classify(self, message: str) -> IntentResult:
        """Classify message using hybrid approach.

        Args:
            message: User message text

        Returns:
            IntentResult from rules (if high confidence), cache, or LLM

        Example:
            >>> classifier = HybridIntentClassifier(...)
            >>> result = await classifier.classify("Create a task")
            >>> result.intent == IntentType.TASK_CREATE
            True
            >>> result.source in ["rule", "cached", "llm"]
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

        # Layer 1: Try rule-based classification FIRST (fast, synchronous)
        # Rules should always be checked before cache, as they are more reliable
        rule_result = self.rule_classifier.classify(message)
        rule_result.latency_ms

        # Check if rule-based result meets confidence threshold
        if rule_result.confidence >= self.confidence_threshold:
            # Rule matched with high confidence - use it and clear cache if different
            cached_result = await self.cache.get(message)
            if cached_result and cached_result.intent != rule_result.intent:
                await self.cache.delete(message)
                logger.info(
                    f"Cleared cache due to high-confidence rule match: "
                    f"rule={rule_result.intent.value} (confidence={rule_result.confidence:.2f}) "
                    f"vs cached={cached_result.intent.value}"
                )
            total_latency_ms = (time.time() - start_time) * 1000
            rule_result.latency_ms = total_latency_ms
            logger.info(
                f"Intent recognized by rules: {rule_result.intent.value} "
                f"(confidence: {rule_result.confidence:.2f}, latency: {total_latency_ms:.2f}ms)"
            )
            # Record metrics
            IntentMetrics.record_classification(
                intent_type=rule_result.intent.value,
                source=rule_result.source,
                latency_seconds=total_latency_ms / 1000.0,
            )
            return rule_result

        # Layer 2: Rule confidence too low, fallback to cache or LLM
        logger.debug(
            f"Rule confidence too low ({rule_result.confidence:.2f} < {self.confidence_threshold}). "
            f"Falling back to cache or LLM..."
        )

        # Check cache
        cached_result = await self.cache.get(message)
        if cached_result:
            IntentMetrics.record_cache_hit()
            total_latency_ms = (time.time() - start_time) * 1000
            cached_result.latency_ms = total_latency_ms
            logger.info(
                f"Intent from cache: {cached_result.intent.value} "
                f"(confidence: {cached_result.confidence:.2f}, latency: {total_latency_ms:.2f}ms)"
            )
            # Record metrics
            IntentMetrics.record_classification(
                intent_type=cached_result.intent.value,
                source=cached_result.source,
                latency_seconds=total_latency_ms / 1000.0,
            )
            return cached_result

        IntentMetrics.record_cache_miss()

        # Cache miss - call LLM
        logger.debug("Cache miss, calling LLM classifier")
        try:
            llm_result = await self.llm_classifier.classify(message)

            # Cache LLM result for future use
            if llm_result.intent != IntentType.IDLE or llm_result.confidence > 0.5:
                # Only cache if result is meaningful
                await self.cache.set(message, llm_result)
                logger.debug(f"Cached LLM result for future use")

            total_latency_ms = (time.time() - start_time) * 1000
            llm_result.latency_ms = total_latency_ms
            logger.info(
                f"Intent recognized by LLM: {llm_result.intent.value} "
                f"(confidence: {llm_result.confidence:.2f}, latency: {total_latency_ms:.2f}ms)"
            )
            # Record metrics
            IntentMetrics.record_classification(
                intent_type=llm_result.intent.value,
                source=llm_result.source,
                latency_seconds=total_latency_ms / 1000.0,
            )
            return llm_result
        except Exception as e:
            IntentMetrics.record_llm_failure(error_type=type(e).__name__)
            # Fallback to rule result (even if low confidence)
            logger.warning(f"LLM classification failed, using rule result: {e}")
            total_latency_ms = (time.time() - start_time) * 1000
            rule_result.latency_ms = total_latency_ms
            IntentMetrics.record_classification(
                intent_type=rule_result.intent.value,
                source="rule",
                latency_seconds=total_latency_ms / 1000.0,
            )
            return rule_result
