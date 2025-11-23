"""SafetyViolation domain entity."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class VetoRuleType(str, Enum):
    """Veto rule type enumeration.

    Purpose:
        Maps to veto rules from consensus_architecture.json.

    Values:
        UNTESTABLE_REQUIREMENT: Requirement cannot be tested
        IMPOSSIBLE_STAGING: Staging environment not available
        MISSING_ROLLBACK_PLAN: No rollback plan defined
        TASK_OVER_4H: Task estimated over 4 hours
        UNDEFINED_DEPENDENCIES: Dependencies are not defined
    """

    UNTESTABLE_REQUIREMENT = "untestable_requirement"
    IMPOSSIBLE_STAGING = "impossible_staging"
    MISSING_ROLLBACK_PLAN = "missing_rollback_plan"
    TASK_OVER_4H = "task_over_4h"
    UNDEFINED_DEPENDENCIES = "undefined_dependencies"


@dataclass
class SafetyViolation:
    """Safety violation domain entity.

    Purpose:
        Represents a safety/guardrail violation tied to veto rules
        from consensus_architecture.json.

    Attributes:
        violation_id: Unique identifier for the violation.
        veto_rule: Type of veto rule violated.
        message: Human-readable violation message.
        context: Optional context dictionary with additional details.

    Example:
        >>> violation = SafetyViolation(
        ...     violation_id="violation1",
        ...     veto_rule=VetoRuleType.TASK_OVER_4H,
        ...     message="Task estimated at 5 hours",
        ... )
        >>> violation.veto_rule
        <VetoRuleType.TASK_OVER_4H: 'task_over_4h'>
    """

    violation_id: str
    veto_rule: VetoRuleType
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate SafetyViolation attributes."""
        if not self.violation_id:
            raise ValueError("violation_id cannot be empty")
        if not self.message:
            raise ValueError("message cannot be empty")
