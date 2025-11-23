"""Skill value object for God Agent."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class SkillType(str, Enum):
    """Skill type enumeration.

    Purpose:
        Represents different skill capabilities available to God Agent.

    Values:
        CONCIERGE: Personalized Butler/concierge interactions
        RESEARCH: RAG-based research and QA with citations
        BUILDER: Code generation and implementation
        REVIEWER: Multi-pass code review
        OPS: Operations, deployment, and infrastructure management
    """

    CONCIERGE = "concierge"
    RESEARCH = "research"
    BUILDER = "builder"
    REVIEWER = "reviewer"
    OPS = "ops"


@dataclass(frozen=True)
class SkillContract:
    """Skill contract value object.

    Purpose:
        Defines input/output contracts for a skill, specifying what data
        the skill expects and what it produces.

    Attributes:
        input_schema: Dictionary describing input contract (must contain
            'input' key).
        output_schema: Dictionary describing output contract (must contain
            'output' key).

    Example:
        >>> contract = SkillContract(
        ...     input_schema={"input": "dict", "query": "string"},
        ...     output_schema={"output": "dict", "result": "string"}
        ... )
    """

    input_schema: Dict[str, str] = field(default_factory=dict)
    output_schema: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate SkillContract attributes."""
        if not self.input_schema:
            raise ValueError("input_schema cannot be empty")
        if not self.output_schema:
            raise ValueError("output_schema cannot be empty")
        if "input" not in self.input_schema:
            raise ValueError("input_schema must contain 'input' key")
        if "output" not in self.output_schema:
            raise ValueError("output_schema must contain 'output' key")


@dataclass(frozen=True)
class Skill:
    """Skill value object.

    Purpose:
        Immutable value object representing a skill capability with its
        input/output contract.

    Attributes:
        skill_type: Type of skill (concierge, research, builder, reviewer, ops).
        contract: SkillContract defining input/output contracts.

    Example:
        >>> contract = SkillContract(
        ...     input_schema={"input": "dict"},
        ...     output_schema={"output": "dict"}
        ... )
        >>> skill = Skill(
        ...     skill_type=SkillType.RESEARCH,
        ...     contract=contract
        ... )
        >>> skill.skill_type
        <SkillType.RESEARCH: 'research'>
    """

    skill_type: SkillType
    contract: SkillContract
