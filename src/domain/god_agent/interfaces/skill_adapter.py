"""Skill Adapter interface."""

from typing import Any, Dict, Protocol

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult
from src.domain.god_agent.value_objects.skill import SkillType


class ISkillAdapter(Protocol):
    """Interface for skill adapters.

    Purpose:
        Defines contract for skill adapters that wrap existing use cases
        and convert them to God Agent skill interface.
    """

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute skill with input and memory context.

        Purpose:
            Execute the skill using input data and memory snapshot,
            returning SkillResult.

        Args:
            input_data: Input dictionary with skill-specific data.
            memory_snapshot: Memory snapshot for context.

        Returns:
            SkillResult with execution outcome.

        Example:
            >>> result = await adapter.execute(
            ...     {"message": "Hello"},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        ...

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for this skill.

        Returns:
            Skill type as string.

        Example:
            >>> adapter.get_skill_id()
            'concierge'
        """
        ...
