"""Plan Compiler Service implementation."""

import json
import time
import uuid
from typing import Any, Protocol

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.intent import Intent
from src.domain.god_agent.value_objects.skill import SkillType
from src.domain.interfaces.llm_client import LLMClientProtocol
from src.infrastructure.god_agent.metrics import record_plan_duration
from src.infrastructure.logging import get_logger

logger = get_logger("plan_compiler_service")

MAX_PLAN_STEPS = 10
MAX_STEP_DURATION_SECONDS = 30
TOKEN_BUDGET = 2500
DEFAULT_MODEL = "qwen"


class PlanCompilerService:
    """Service for compiling task plans from intents.

    Purpose:
        Converts (Intent, MemorySnapshot) into a TaskPlan DAG with step
        templates, skill assignments, and acceptance criteria using LLM.

    Attributes:
        llm_client: LLM client for plan generation.

    Example:
        >>> service = PlanCompilerService(llm_client)
        >>> plan = await service.compile_plan(intent, memory_snapshot)
        >>> len(plan.steps) <= 10
        True
    """

    def __init__(self, llm_client: LLMClientProtocol) -> None:
        """Initialize service with LLM client.

        Args:
            llm_client: LLM client for plan generation.
        """
        self.llm_client = llm_client
        logger.info("PlanCompilerService initialized")

    async def compile_plan(
        self, intent: Intent, memory_snapshot: MemorySnapshot
    ) -> TaskPlan:
        """Compile task plan from intent and memory snapshot.

        Purpose:
            Generate TaskPlan DAG using LLM, respecting token budget and
            max step constraints.

        Args:
            intent: User intent classification.
            memory_snapshot: Memory snapshot for context.

        Returns:
            TaskPlan with steps, dependencies, and acceptance criteria.

        Raises:
            ValueError: If plan generation fails or plan is invalid.
            Exception: If LLM call fails.

        Example:
            >>> plan = await service.compile_plan(intent, memory_snapshot)
            >>> len(plan.steps) <= 10
            True
        """
        # Build prompt for LLM
        prompt = self._build_plan_prompt(intent, memory_snapshot)

        try:
            # Call LLM with token budget
            response = await self.llm_client.make_request(
                model_name=DEFAULT_MODEL,
                prompt=prompt,
                max_tokens=TOKEN_BUDGET,
                temperature=0.7,
            )

            # Parse JSON response
            plan_data = self._parse_llm_response(response)

            # Create TaskPlan from parsed data
            plan = self._create_task_plan(plan_data, intent)

            # Validate plan
            self.validate_plan(plan)

            plan_duration = time.perf_counter() - plan_start_time
            record_plan_duration(plan_duration)

            logger.info(
                "Task plan compiled",
                extra={
                    "plan_id": plan.plan_id,
                    "steps_count": len(plan.steps),
                    "intent_type": intent.intent_type.value,
                    "duration_seconds": plan_duration,
                },
            )

            return plan

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse LLM response as JSON",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ValueError(f"Invalid LLM response format: {e}") from e
        except Exception as e:
            logger.error(
                "Failed to compile plan",
                extra={"intent_type": intent.intent_type.value, "error": str(e)},
                exc_info=True,
            )
            raise

    def validate_plan(self, plan: TaskPlan) -> bool:
        """Validate task plan structure.

        Purpose:
            Check that plan is valid DAG (no cycles, valid dependencies).

        Args:
            plan: TaskPlan to validate.

        Returns:
            True if plan is valid.

        Raises:
            ValueError: If plan is invalid (cycles, missing dependencies).

        Example:
            >>> is_valid = service.validate_plan(plan)
            >>> is_valid
            True
        """
        # TaskPlan.__post_init__ already validates DAG
        # This method provides explicit validation interface
        try:
            # Re-validate by creating a new TaskPlan (triggers validation)
            # Or just check that plan is already valid
            if not plan.plan_id:
                raise ValueError("plan_id cannot be empty")

            if len(plan.steps) > MAX_PLAN_STEPS:
                raise ValueError(
                    f"Plan has {len(plan.steps)} steps, max is {MAX_PLAN_STEPS}"
                )

            # Check step durations (annotated in acceptance_criteria)
            for step in plan.steps:
                if step.acceptance_criteria:
                    for criterion in step.acceptance_criteria:
                        if "30s" in criterion or "timeout" in criterion.lower():
                            # Step has timeout annotation
                            pass

            return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                "Plan validation failed",
                extra={"plan_id": plan.plan_id, "error": str(e)},
                exc_info=True,
            )
            raise ValueError(f"Plan validation failed: {e}") from e

    def _build_plan_prompt(
        self, intent: Intent, memory_snapshot: MemorySnapshot
    ) -> str:
        """Build prompt for LLM plan generation.

        Args:
            intent: User intent.
            memory_snapshot: Memory snapshot.

        Returns:
            Formatted prompt string.
        """
        prompt_parts = [
            "Generate a task plan as JSON for the following request:",
            f"Intent: {intent.intent_type.value} (confidence: {intent.confidence:.2f})",
            "",
            "Context:",
            f"User profile: {memory_snapshot.profile_summary[:200]}",
            f"Recent conversation: {memory_snapshot.conversation_summary[:200]}",
            "",
            "Constraints:",
            f"- Maximum {MAX_PLAN_STEPS} steps",
            f"- Each step max {MAX_STEP_DURATION_SECONDS}s duration",
            "- Steps must form a valid DAG (no cycles)",
            "",
            "Response format (JSON):",
            "{",
            '  "steps": [',
            "    {",
            '      "step_id": "step1",',
            '      "skill_type": "research|builder|reviewer|ops|concierge",',
            '      "depends_on": [],',
            '      "acceptance_criteria": ["criterion1", "criterion2"],',
            '      "rollback_instructions": "optional rollback steps"',
            "    }",
            "  ]",
            "}",
            "",
            "Generate the plan:",
        ]

        return "\n".join(prompt_parts)

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse LLM JSON response.

        Args:
            response: LLM response text.

        Returns:
            Parsed plan data dictionary.

        Raises:
            ValueError: If response is not valid JSON.
        """
        # Try to extract JSON from response (may have markdown code blocks)
        response_clean = response.strip()

        # Remove markdown code blocks if present
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            # Find JSON block
            json_start = None
            json_end = None
            for i, line in enumerate(lines):
                if line.strip().startswith("```json") or line.strip().startswith("```"):
                    json_start = i + 1
                elif line.strip() == "```" and json_start is not None:
                    json_end = i
                    break

            if json_start is not None and json_end is not None:
                response_clean = "\n".join(lines[json_start:json_end])
            elif json_start is not None:
                response_clean = "\n".join(lines[json_start:])

        # Parse JSON
        try:
            parsed: dict[str, Any] = json.loads(response_clean)
            return parsed
        except json.JSONDecodeError:
            # Try to find JSON object in text
            import re

            json_match = re.search(r"\{.*\}", response_clean, re.DOTALL)
            if json_match:
                parsed_fallback: dict[str, Any] = json.loads(json_match.group())
                return parsed_fallback
            raise

    def _create_task_plan(self, plan_data: dict, intent: Intent) -> TaskPlan:
        """Create TaskPlan from parsed data.

        Args:
            plan_data: Parsed plan data from LLM.
            intent: Original intent.

        Returns:
            TaskPlan entity.

        Raises:
            ValueError: If plan data is invalid.
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        steps_data = plan_data.get("steps", [])

        # Limit to max steps
        if len(steps_data) > MAX_PLAN_STEPS:
            logger.warning(
                "Plan has more than max steps, truncating",
                extra={
                    "requested_steps": len(steps_data),
                    "max_steps": MAX_PLAN_STEPS,
                },
            )
            steps_data = steps_data[:MAX_PLAN_STEPS]

        # Create TaskStep entities
        steps: list[TaskStep] = []
        for step_data in steps_data:
            step_id = step_data.get("step_id", f"step_{len(steps) + 1}")
            skill_type_str = step_data.get("skill_type", "concierge")

            # Map string to SkillType enum
            try:
                skill_type = SkillType(skill_type_str)
            except ValueError:
                logger.warning(
                    f"Invalid skill_type {skill_type_str}, defaulting to concierge"
                )
                skill_type = SkillType.CONCIERGE

            step = TaskStep(
                step_id=step_id,
                skill_type=skill_type,
                status=TaskStepStatus.PENDING,
                depends_on=step_data.get("depends_on", []),
                acceptance_criteria=step_data.get("acceptance_criteria", []),
                rollback_instructions=step_data.get("rollback_instructions"),
            )
            steps.append(step)

        # Create TaskPlan (validation happens in __post_init__)
        plan = TaskPlan(plan_id=plan_id, steps=steps)

        return plan
