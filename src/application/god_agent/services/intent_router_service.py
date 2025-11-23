"""Intent Router Service implementation."""

from src.domain.embedding_index.interfaces import EmbeddingGateway
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.interfaces.memory_fabric_service import IMemoryFabricService
from src.domain.god_agent.value_objects.intent import Intent, IntentType
from src.infrastructure.logging import get_logger

logger = get_logger("intent_router_service")

CONFIDENCE_THRESHOLD = 0.6


class IntentRouterService:
    """Service for classifying user requests into intents.

    Purpose:
        Classifies user messages into intents (concierge, research, build,
        review, ops) using hybrid approach (keywords + embeddings + memory).

    Attributes:
        memory_fabric_service: Service for retrieving memory snapshots.
        embedding_gateway: Gateway for embedding operations (optional).

    Example:
        >>> service = IntentRouterService(memory_fabric_service, embedding_gateway)
        >>> intent = await service.route_intent("user_1", "What is Python?")
        >>> intent.intent_type
        <IntentType.RESEARCH: 'research'>
    """

    def __init__(
        self,
        memory_fabric_service: IMemoryFabricService,
        embedding_gateway: EmbeddingGateway | None = None,
    ) -> None:
        """Initialize service with dependencies.

        Args:
            memory_fabric_service: Service for retrieving memory snapshots.
            embedding_gateway: Gateway for embedding operations (optional).
        """
        self.memory_fabric_service = memory_fabric_service
        self.embedding_gateway = embedding_gateway
        logger.info("IntentRouterService initialized")

    async def route_intent(self, user_id: str, user_message: str) -> Intent:
        """Route user message to intent classification.

        Purpose:
            Classify user message into one of 5 intent types using hybrid
            approach (keywords + memory context). Falls back to concierge
            if confidence < threshold.

        Args:
            user_id: User identifier.
            user_message: User message text.

        Returns:
            Intent with type and confidence score.

        Example:
            >>> intent = await service.route_intent("user_1", "What is Python?")
            >>> intent.intent_type
            <IntentType.RESEARCH: 'research'>
        """
        # Get memory snapshot for context
        memory_snapshot = await self.memory_fabric_service.get_memory_snapshot(user_id)

        # Normalize message
        message_lower = user_message.lower().strip()

        # Keyword-based classification with confidence scoring
        intent_type, confidence = self._classify_with_keywords(
            message_lower, memory_snapshot
        )

        # Fallback to concierge if confidence too low
        if confidence < CONFIDENCE_THRESHOLD:
            logger.debug(
                "Confidence below threshold, falling back to concierge",
                extra={
                    "user_id": user_id,
                    "detected_intent": intent_type.value,
                    "confidence": confidence,
                },
            )
            intent_type = IntentType.CONCIERGE
            confidence = 0.7  # Default confidence for concierge fallback

        intent = Intent(intent_type=intent_type, confidence=confidence)

        logger.info(
            "Intent routed",
            extra={
                "user_id": user_id,
                "intent_type": intent_type.value,
                "confidence": confidence,
            },
        )

        return intent

    def get_confidence(self, intent: Intent) -> float:
        """Get confidence score from intent.

        Purpose:
            Extract confidence value from Intent value object.

        Args:
            intent: Intent value object.

        Returns:
            Confidence score in range [0.0, 1.0].

        Example:
            >>> confidence = service.get_confidence(intent)
            >>> 0.0 <= confidence <= 1.0
            True
        """
        return intent.confidence

    def _classify_with_keywords(
        self, message: str, memory_snapshot: MemorySnapshot
    ) -> tuple[IntentType, float]:
        """Classify message using keyword matching.

        Purpose:
            Simple keyword-based classification with confidence scoring.
            Uses memory context to boost confidence for related intents.

        Args:
            message: Normalized message text.
            memory_snapshot: Memory snapshot for context.

        Returns:
            Tuple of (IntentType, confidence).
        """
        # Research keywords
        research_keywords = [
            "what is",
            "explain",
            "how does",
            "tell me about",
            "describe",
            "what are",
            "question",
            "?",
        ]
        research_score = float(sum(1 for kw in research_keywords if kw in message))

        # Build keywords
        build_keywords = [
            "create",
            "write",
            "implement",
            "generate",
            "build",
            "make",
            "code",
            "function",
            "class",
            "script",
        ]
        build_score = float(sum(1 for kw in build_keywords if kw in message))

        # Review keywords
        review_keywords = [
            "review",
            "check",
            "analyze",
            "examine",
            "inspect",
            "audit",
            "commit",
            "code review",
        ]
        review_score = float(sum(1 for kw in review_keywords if kw in message))

        # Ops keywords
        ops_keywords = [
            "status",
            "health",
            "metrics",
            "deploy",
            "deployment",
            "infrastructure",
            "system",
            "monitor",
            "ops",
        ]
        ops_score = float(sum(1 for kw in ops_keywords if kw in message))

        # Concierge keywords (greetings, casual)
        concierge_keywords = [
            "hello",
            "hi",
            "hey",
            "greetings",
            "how are you",
            "thanks",
            "thank you",
        ]
        concierge_score = float(sum(1 for kw in concierge_keywords if kw in message))

        # Boost scores based on memory context
        if memory_snapshot.conversation_summary:
            if "research" in memory_snapshot.conversation_summary.lower():
                research_score += 0.5
            if "code" in memory_snapshot.conversation_summary.lower():
                build_score += 0.5
            if "review" in memory_snapshot.conversation_summary.lower():
                review_score += 0.5

        # Calculate confidence scores
        scores = {
            IntentType.RESEARCH: min(research_score / 3.0, 1.0),
            IntentType.BUILD: min(build_score / 3.0, 1.0),
            IntentType.REVIEW: min(review_score / 2.0, 1.0),
            IntentType.OPS: min(ops_score / 2.0, 1.0),
            IntentType.CONCIERGE: min(concierge_score / 2.0, 1.0),
        }

        # Find best match
        best_intent = max(scores.items(), key=lambda x: x[1])[0]
        best_confidence = scores[best_intent]

        # If no clear match, default to concierge
        if best_confidence < 0.3:
            return (IntentType.CONCIERGE, 0.5)

        return (best_intent, best_confidence)
