"""Concierge skill adapter for God Agent."""

import uuid
from typing import Any, Dict

from src.application.personalization.dtos import (
    PersonalizedReplyInput,
    PersonalizedReplyOutput,
)
from src.application.personalization.use_cases.personalized_reply import (
    PersonalizedReplyUseCase,
)
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.logging import get_logger

logger = get_logger("concierge_skill_adapter")


class ConciergeSkillAdapter:
    """Concierge skill adapter.

    Purpose:
        Wraps PersonalizedReplyUseCase to provide concierge skill
        interface for God Agent.

    Attributes:
        personalized_reply_use_case: Use case for personalized replies.

    Example:
        >>> adapter = ConciergeSkillAdapter(personalized_reply_use_case)
        >>> result = await adapter.execute(
        ...     {"message": "Hello", "user_id": "123"},
        ...     memory_snapshot
        ... )
    """

    def __init__(self, personalized_reply_use_case: PersonalizedReplyUseCase) -> None:
        """Initialize concierge skill adapter.

        Args:
            personalized_reply_use_case: Use case for personalized replies.
        """
        self.personalized_reply_use_case = personalized_reply_use_case
        logger.info("ConciergeSkillAdapter initialized")

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute concierge skill.

        Purpose:
            Execute personalized reply generation using PersonalizedReplyUseCase
            and convert result to SkillResult.

        Args:
            input_data: Input dictionary with 'message', 'user_id', 'source'.
            memory_snapshot: Memory snapshot for context (not used directly,
                but available for future enhancements).

        Returns:
            SkillResult with reply and metadata.

        Example:
            >>> result = await adapter.execute(
            ...     {"message": "Hello", "user_id": "123"},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        try:
            # Extract input data
            message = input_data.get("message", "")
            user_id = input_data.get("user_id", memory_snapshot.user_id)
            source = input_data.get("source", "text")

            if not message:
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.FAILURE,
                    error="Missing 'message' in input_data",
                )

            # Create PersonalizedReplyInput
            reply_input = PersonalizedReplyInput(
                user_id=user_id, text=message, source=source
            )

            # Execute use case
            reply_output: PersonalizedReplyOutput = (
                await self.personalized_reply_use_case.execute(reply_input)
            )

            # Convert to SkillResult
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.SUCCESS,
                output={
                    "reply": reply_output.reply,
                    "used_persona": reply_output.used_persona,
                    "memory_events_used": reply_output.memory_events_used,
                    "compressed": reply_output.compressed,
                },
                metadata={
                    "skill_type": SkillType.CONCIERGE.value,
                    "source": source,
                },
            )

        except Exception as e:
            logger.error(
                "Concierge skill execution failed",
                extra={"error": str(e), "input_data": input_data},
                exc_info=True,
            )
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"Concierge skill error: {str(e)}",
            )

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for concierge skill.

        Returns:
            Skill type as string ('concierge').

        Example:
            >>> adapter.get_skill_id()
            'concierge'
        """
        return SkillType.CONCIERGE.value
