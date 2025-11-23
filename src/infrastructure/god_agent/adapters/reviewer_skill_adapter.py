"""Reviewer skill adapter for God Agent."""

import uuid
from typing import Any, Dict

from src.application.use_cases.review_homework_use_case import ReviewHomeworkUseCase
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.logging import get_logger

logger = get_logger("reviewer_skill_adapter")


class ReviewerSkillAdapter:
    """Reviewer skill adapter.

    Purpose:
        Wraps ReviewHomeworkUseCase to provide reviewer skill
        interface for God Agent.

    Attributes:
        review_homework_use_case: Use case for homework review.

    Example:
        >>> adapter = ReviewerSkillAdapter(review_homework_use_case)
        >>> result = await adapter.execute(
        ...     {"commit_hash": "abc123"},
        ...     memory_snapshot
        ... )
    """

    def __init__(self, review_homework_use_case: ReviewHomeworkUseCase) -> None:
        """Initialize reviewer skill adapter.

        Args:
            review_homework_use_case: Use case for homework review.
        """
        self.review_homework_use_case = review_homework_use_case
        logger.info("ReviewerSkillAdapter initialized")

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute reviewer skill.

        Purpose:
            Execute code review using ReviewHomeworkUseCase
            and convert result to SkillResult.

        Args:
            input_data: Input dictionary with 'commit_hash', optional 'user_id'.
            memory_snapshot: Memory snapshot for context (not used directly,
                but available for future enhancements).

        Returns:
            SkillResult with review report, findings, and metadata.

        Example:
            >>> result = await adapter.execute(
            ...     {"commit_hash": "abc123"},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        try:
            # Extract input data
            commit_hash = input_data.get("commit_hash", "")
            user_id = input_data.get("user_id", memory_snapshot.user_id)

            if not commit_hash:
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.FAILURE,
                    error="Missing 'commit_hash' in input_data",
                )

            # Execute use case
            review_result = await self.review_homework_use_case.execute(commit_hash)

            # Convert to SkillResult
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.SUCCESS,
                output={
                    "report": review_result.markdown_report,
                    "total_findings": review_result.total_findings,
                    "detected_components": review_result.detected_components,
                    "pass_2_components": review_result.pass_2_components,
                    "execution_time_seconds": review_result.execution_time_seconds,
                    "success": review_result.success,
                },
                metadata={
                    "skill_type": SkillType.REVIEWER.value,
                    "commit_hash": commit_hash,
                    "user_id": user_id,
                },
            )

        except Exception as e:
            logger.error(
                "Reviewer skill execution failed",
                extra={"error": str(e), "input_data": input_data},
                exc_info=True,
            )
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"Reviewer skill error: {str(e)}",
            )

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for reviewer skill.

        Returns:
            Skill type as string ('reviewer').

        Example:
            >>> adapter.get_skill_id()
            'reviewer'
        """
        return SkillType.REVIEWER.value
