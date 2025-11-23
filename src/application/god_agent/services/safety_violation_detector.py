"""Safety Violation Detector service for God Agent."""

import uuid
from typing import Any, Dict, List, Optional

from src.application.god_agent.services.consensus_bridge import ConsensusBridge
from src.domain.god_agent.entities.safety_violation import SafetyViolation, VetoRuleType
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep
from src.infrastructure.god_agent.metrics import record_veto
from src.infrastructure.logging import get_logger

logger = get_logger("safety_violation_detector")

# Thresholds for safety checks
MAX_TASK_HOURS = 4.0


class SafetyViolationDetector:
    """Safety Violation Detector service.

    Purpose:
        Detects safety violations based on veto rules from
        consensus_architecture.json and triggers ConsensusBridge.

    Attributes:
        consensus_bridge: ConsensusBridge for triggering consensus workflow.

    Example:
        >>> detector = SafetyViolationDetector(consensus_bridge)
        >>> violations = await detector.detect(
        ...     task_plan=plan,
        ...     step=step,
        ...     context={"estimated_hours": 5.0}
        ... )
    """

    def __init__(self, consensus_bridge: ConsensusBridge) -> None:
        """Initialize safety violation detector.

        Args:
            consensus_bridge: ConsensusBridge for triggering consensus.
        """
        self.consensus_bridge = consensus_bridge
        logger.info("SafetyViolationDetector initialized")

    async def detect(
        self,
        task_plan: TaskPlan,
        step: TaskStep,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SafetyViolation]:
        """Detect safety violations for a task step.

        Purpose:
            Checks step against veto rules and returns violations.
            Triggers ConsensusBridge if violations are detected.

        Args:
            task_plan: Task plan containing the step.
            step: Task step to check.
            context: Optional context dictionary with metadata.

        Returns:
            List of SafetyViolation entities.

        Example:
            >>> violations = await detector.detect(
            ...     task_plan=plan,
            ...     step=step,
            ...     context={"estimated_hours": 5.0}
            ... )
            >>> len(violations)
            1
        """
        context = context or {}
        violations = await self._check_violations(
            task_plan=task_plan,
            step=step,
            context=context,
        )

        if violations:
            # Record veto metrics
            for violation in violations:
                record_veto(violation.veto_rule.value)

            logger.warning(
                "Safety violations detected",
                extra={
                    "step_id": step.step_id,
                    "violation_count": len(violations),
                    "violation_types": [v.veto_rule.value for v in violations],
                },
            )

            # Trigger ConsensusBridge for violations
            try:
                await self.consensus_bridge.request_consensus(
                    task_plan=task_plan,
                    step=step,
                    context={
                        "reason": "safety_violations",
                        "violations": [v.veto_rule.value for v in violations],
                    },
                )
            except Exception as e:
                logger.error(
                    "Failed to trigger consensus bridge",
                    extra={"error": str(e), "step_id": step.step_id},
                    exc_info=True,
                )

        return violations

    async def _check_violations(
        self,
        task_plan: TaskPlan,
        step: TaskStep,
        context: Dict[str, Any],
    ) -> List[SafetyViolation]:
        """Check step against veto rules.

        Args:
            task_plan: Task plan.
            step: Task step.
            context: Context dictionary.

        Returns:
            List of detected violations.
        """
        violations: List[SafetyViolation] = []

        # Check: task_over_4h
        estimated_hours = context.get("estimated_hours", 0.0)
        if estimated_hours > MAX_TASK_HOURS:
            violations.append(
                SafetyViolation(
                    violation_id=str(uuid.uuid4()),
                    veto_rule=VetoRuleType.TASK_OVER_4H,
                    message=f"Task estimated at {estimated_hours} hours (max: {MAX_TASK_HOURS}h)",
                    context={"estimated_hours": estimated_hours},
                )
            )

        # Check: missing_rollback_plan
        # Only check if step is critical (has dependencies or modifies state)
        if step.depends_on and not step.rollback_instructions:
            violations.append(
                SafetyViolation(
                    violation_id=str(uuid.uuid4()),
                    veto_rule=VetoRuleType.MISSING_ROLLBACK_PLAN,
                    message="Step has dependencies but no rollback instructions",
                    context={"step_id": step.step_id},
                )
            )

        # Check: undefined_dependencies
        step_ids = {s.step_id for s in task_plan.steps}
        for dep_id in step.depends_on:
            if dep_id not in step_ids:
                violations.append(
                    SafetyViolation(
                        violation_id=str(uuid.uuid4()),
                        veto_rule=VetoRuleType.UNDEFINED_DEPENDENCIES,
                        message=f"Step depends on undefined step: {dep_id}",
                        context={"step_id": step.step_id, "missing_dep": dep_id},
                    )
                )

        # Check: untestable_requirement
        # Simplified: if acceptance_criteria are empty or vague
        if not step.acceptance_criteria:
            violations.append(
                SafetyViolation(
                    violation_id=str(uuid.uuid4()),
                    veto_rule=VetoRuleType.UNTESTABLE_REQUIREMENT,
                    message="Step has no acceptance criteria (untestable)",
                    context={"step_id": step.step_id},
                )
            )

        # Check: impossible_staging
        # Simplified: check if context indicates staging issues
        if context.get("staging_unavailable", False):
            violations.append(
                SafetyViolation(
                    violation_id=str(uuid.uuid4()),
                    veto_rule=VetoRuleType.IMPOSSIBLE_STAGING,
                    message="Staging environment not available",
                    context={"step_id": step.step_id},
                )
            )

        return violations
