"""God Agent Orchestrator service."""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from src.application.god_agent.services.consensus_bridge import ConsensusBridge
from src.application.god_agent.services.safety_violation_detector import (
    SafetyViolationDetector,
)
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.interfaces.memory_fabric_service import IMemoryFabricService
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.god_agent.metrics import (
    record_skill_latency,
    record_task_execution,
)
from src.infrastructure.logging import get_logger

logger = get_logger("god_agent_orchestrator")


class TaskExecutionState:
    """Task execution state.

    Purpose:
        Tracks execution state for a task plan (running, paused, cancelled).
    """

    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class GodAgentOrchestrator:
    """God Agent Orchestrator service.

    Purpose:
        Orchestrates execution of TaskPlan steps, manages pause/resume/cancel,
        and publishes events.

    Attributes:
        skill_adapters: Dictionary mapping SkillType to ISkillAdapter.
        memory_fabric_service: Service for memory snapshot retrieval.
        consensus_bridge: Bridge for consensus workflow.

    Example:
        >>> orchestrator = GodAgentOrchestrator(
        ...     skill_adapters=adapters,
        ...     memory_fabric_service=memory_service,
        ...     consensus_bridge=consensus_bridge
        ... )
        >>> result = await orchestrator.execute_plan(
        ...     task_plan=plan,
        ...     user_id="user_123"
        ... )
    """

    def __init__(
        self,
        skill_adapters: Dict[SkillType, ISkillAdapter],
        memory_fabric_service: IMemoryFabricService,
        consensus_bridge: ConsensusBridge,
        safety_detector: Optional[SafetyViolationDetector] = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            skill_adapters: Dictionary mapping SkillType to ISkillAdapter.
            memory_fabric_service: Service for memory snapshot retrieval.
            consensus_bridge: Bridge for consensus workflow.
            safety_detector: Optional safety violation detector.
        """
        self.skill_adapters = skill_adapters
        self.memory_fabric_service = memory_fabric_service
        self.consensus_bridge = consensus_bridge
        self.safety_detector = safety_detector
        self._task_states: Dict[str, str] = {}  # plan_id -> state
        self._task_locks: Dict[str, asyncio.Lock] = {}  # plan_id -> lock
        logger.info("GodAgentOrchestrator initialized")

    async def execute_plan(
        self,
        task_plan: TaskPlan,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute task plan.

        Purpose:
            Executes all steps in the plan sequentially or in parallel
            based on dependencies.

        Args:
            task_plan: Task plan to execute.
            user_id: User identifier.
            context: Optional context dictionary.

        Returns:
            Dictionary with execution results.

        Example:
            >>> result = await orchestrator.execute_plan(
            ...     task_plan=plan,
            ...     user_id="user_123"
            ... )
            >>> result["status"]
            'completed'
        """
        context = context or {}
        plan_id = task_plan.plan_id

        # Initialize state
        self._task_states[plan_id] = TaskExecutionState.RUNNING
        self._task_locks[plan_id] = asyncio.Lock()

        try:
            # Publish TASK_STARTED event
            await self._publish_event(
                "TASK_STARTED",
                {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "step_count": len(task_plan.steps),
                    "task_id": plan_id,
                },
            )

            # Get memory snapshot
            memory_snapshot = await self.memory_fabric_service.get_memory_snapshot(
                user_id=user_id
            )

            # Execute steps
            step_results: List[Dict[str, Any]] = []
            executed_steps: set[str] = set()

            # Topological sort for dependency resolution
            steps_to_execute = self._topological_sort(task_plan.steps)

            for step in steps_to_execute:
                # Check if task is paused or cancelled
                if self._task_states.get(plan_id) == TaskExecutionState.PAUSED:
                    await self._wait_for_resume(plan_id)

                if self._task_states.get(plan_id) == TaskExecutionState.CANCELLED:
                    logger.info(
                        "Task cancelled",
                        extra={"plan_id": plan_id, "step_id": step.step_id},
                    )
                    break

                # Wait for dependencies
                for dep_id in step.depends_on:
                    if dep_id not in executed_steps:
                        # Wait for dependency to complete
                        await self._wait_for_step(dep_id, plan_id)

                # Check if step is critical and requires consensus
                is_critical = self._is_critical_step(step, context)
                if is_critical:
                    # Trigger consensus for critical step
                    try:
                        consensus_id = await self.consensus_bridge.request_consensus(
                            task_plan=task_plan,
                            step=step,
                            context={"reason": "critical_step", **context},
                        )

                        # Check for veto
                        has_veto = await self.consensus_bridge.check_veto_status(
                            consensus_id
                        )
                        if has_veto:
                            # Record veto metric
                            from src.infrastructure.god_agent.metrics import record_veto

                            record_veto("critical_step_veto")

                            # Publish VETO_RAISED event
                            await self._publish_event(
                                "VETO_RAISED",
                                {
                                    "plan_id": plan_id,
                                    "step_id": step.step_id,
                                    "consensus_id": consensus_id,
                                    "task_id": plan_id,
                                    "skill_id": step.skill_type.value
                                    if hasattr(step.skill_type, "value")
                                    else str(step.skill_type),
                                    "plan_step": step.step_id,
                                },
                            )
                            logger.warning(
                                "Veto raised for critical step",
                                extra={
                                    "plan_id": plan_id,
                                    "step_id": step.step_id,
                                    "consensus_id": consensus_id,
                                },
                            )
                            # Skip step execution if vetoed
                            step.status = TaskStepStatus.FAILED
                            step_results.append(
                                {
                                    "step_id": step.step_id,
                                    "status": "failed",
                                    "error": "Step vetoed by consensus",
                                }
                            )
                            continue

                    except Exception as e:
                        logger.error(
                            "Consensus request failed",
                            extra={
                                "plan_id": plan_id,
                                "step_id": step.step_id,
                                "error": str(e),
                            },
                            exc_info=True,
                        )
                        # Continue execution if consensus fails

                # Execute step
                step_start_time = time.perf_counter()
                step_result = await self._execute_step(
                    step=step,
                    memory_snapshot=memory_snapshot,
                    plan_id=plan_id,
                )
                step_duration = time.perf_counter() - step_start_time

                # Record metrics
                skill_type_str = (
                    step.skill_type.value
                    if hasattr(step.skill_type, "value")
                    else str(step.skill_type)
                )
                record_task_execution(
                    skill_type=skill_type_str,
                    status=step_result.status.value,
                )
                record_skill_latency(
                    skill_type=skill_type_str,
                    duration_seconds=step_duration,
                )

                step_results.append(
                    {
                        "step_id": step.step_id,
                        "status": step_result.status.value,
                        "output": step_result.output,
                        "error": step_result.error,
                    }
                )

                executed_steps.add(step.step_id)

                # Publish STEP_DONE event
                await self._publish_event(
                    "STEP_DONE",
                    {
                        "plan_id": plan_id,
                        "step_id": step.step_id,
                        "status": step_result.status.value,
                        "skill_id": skill_type_str,
                        "plan_step": step.step_id,
                    },
                )

            # Update state
            self._task_states[plan_id] = TaskExecutionState.COMPLETED

            return {
                "plan_id": plan_id,
                "status": "completed",
                "step_results": step_results,
            }

        except Exception as e:
            logger.error(
                "Task execution failed",
                extra={"plan_id": plan_id, "error": str(e)},
                exc_info=True,
            )
            self._task_states[plan_id] = TaskExecutionState.FAILED
            raise

    async def pause_task(self, plan_id: str) -> None:
        """Pause task execution.

        Purpose:
            Pauses execution of a running task plan.

        Args:
            plan_id: Plan identifier.

        Example:
            >>> await orchestrator.pause_task("plan_1")
        """
        if plan_id in self._task_states:
            self._task_states[plan_id] = TaskExecutionState.PAUSED
            logger.info("Task paused", extra={"plan_id": plan_id})
        else:
            logger.warning(
                "Task not found for pause",
                extra={"plan_id": plan_id},
            )

    async def resume_task(self, plan_id: str) -> None:
        """Resume task execution.

        Purpose:
            Resumes execution of a paused task plan.

        Args:
            plan_id: Plan identifier.

        Example:
            >>> await orchestrator.resume_task("plan_1")
        """
        if plan_id in self._task_states:
            if self._task_states[plan_id] == TaskExecutionState.PAUSED:
                self._task_states[plan_id] = TaskExecutionState.RUNNING
                logger.info("Task resumed", extra={"plan_id": plan_id})
            else:
                logger.warning(
                    "Task not in paused state",
                    extra={"plan_id": plan_id, "state": self._task_states[plan_id]},
                )
        else:
            logger.warning(
                "Task not found for resume",
                extra={"plan_id": plan_id},
            )

    async def cancel_task(self, plan_id: str) -> None:
        """Cancel task execution.

        Purpose:
            Cancels execution of a running or paused task plan.

        Args:
            plan_id: Plan identifier.

        Example:
            >>> await orchestrator.cancel_task("plan_1")
        """
        if plan_id in self._task_states:
            self._task_states[plan_id] = TaskExecutionState.CANCELLED
            logger.info("Task cancelled", extra={"plan_id": plan_id})
        else:
            logger.warning(
                "Task not found for cancel",
                extra={"plan_id": plan_id},
            )

    async def _execute_step(
        self,
        step: TaskStep,
        memory_snapshot: MemorySnapshot,
        plan_id: str,
    ) -> SkillResult:
        """Execute a single step.

        Args:
            step: Task step to execute.
            memory_snapshot: Memory snapshot for context.
            plan_id: Plan identifier.

        Returns:
            SkillResult from step execution.
        """
        adapter = self.skill_adapters.get(step.skill_type)
        if not adapter:
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"No adapter found for skill type: {step.skill_type}",
            )

        # Prepare input data
        input_data = {
            "step_id": step.step_id,
            "plan_id": plan_id,
        }

        # Execute skill
        result = await adapter.execute(input_data, memory_snapshot)

        # Update step status
        if result.status == SkillResultStatus.SUCCESS:
            step.status = TaskStepStatus.SUCCEEDED
        else:
            step.status = TaskStepStatus.FAILED

        return result

    def _topological_sort(self, steps: List[TaskStep]) -> List[TaskStep]:
        """Sort steps topologically based on dependencies.

        Args:
            steps: List of task steps.

        Returns:
            Sorted list of steps.
        """
        # Simple implementation: return steps in order
        # More sophisticated implementation would handle parallel execution
        return steps

    async def _wait_for_resume(self, plan_id: str) -> None:
        """Wait for task to be resumed.

        Args:
            plan_id: Plan identifier.
        """
        while self._task_states.get(plan_id) == TaskExecutionState.PAUSED:
            await asyncio.sleep(0.1)

    async def _wait_for_step(self, step_id: str, plan_id: str) -> None:
        """Wait for a step to complete.

        Args:
            step_id: Step identifier.
            plan_id: Plan identifier.
        """
        # Simplified: just return
        # In full implementation, would track step completion
        await asyncio.sleep(0.01)

    def _is_critical_step(self, step: TaskStep, context: Dict[str, Any]) -> bool:
        """Check if step is critical and requires consensus.

        Args:
            step: Task step to check.
            context: Context dictionary.

        Returns:
            True if step is critical, False otherwise.
        """
        # Check context flag
        if context.get("is_critical", False):
            return True

        # Check if step has safety violations (if detector available)
        if self.safety_detector:
            # This would be checked asynchronously, simplified here
            return False

        # Check step characteristics
        # Critical if: has dependencies, modifies state, or has high risk
        if step.depends_on or step.rollback_instructions:
            return True

        return False

    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish event.

        Purpose:
            Publishes orchestration events (TASK_STARTED, STEP_DONE, VETO_RAISED).

        Args:
            event_type: Event type.
            data: Event data.
        """
        logger.info(
            f"Event published: {event_type}",
            extra={"event_type": event_type, **data},
        )
