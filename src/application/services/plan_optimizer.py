"""Plan optimization service for execution plans.

Following Python Zen: "Simple is better than complex."
"""

import logging
from typing import Any, Dict, List

from src.domain.entities.conversation import ExecutionPlan, ExecutionStep

logger = logging.getLogger(__name__)


class ExecutionOptimizer:
    """Optimizes execution plans by removing redundant calls and detecting parallel opportunities."""

    def __init__(self) -> None:
        """Initialize optimizer."""
        self.tool_dependencies: Dict[str, List[str]] = {
            "generate_code": [],
            "generate_tests": ["generate_code"],
            "review_code": ["generate_code"],
            "format_code": [],
            "analyze_complexity": [],
            "formalize_task": [],
        }

    def optimize(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Optimize execution plan.

        Args:
            plan: Original execution plan

        Returns:
            Optimized execution plan
        """
        steps = plan.steps.copy()
        optimized_steps = self._remove_redundant_steps(steps)
        optimized_steps = self._reorder_for_parallelization(optimized_steps)
        
        # Detect circular dependencies
        has_cycles = self._detect_circular_dependencies(optimized_steps)
        if has_cycles:
            logger.warning("Circular dependencies detected in plan")

        return ExecutionPlan(
            steps=optimized_steps,
            estimated_time=self._estimate_time(optimized_steps),
        )

    def _remove_redundant_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """Remove redundant tool calls.

        Args:
            steps: Execution steps

        Returns:
            Steps without redundant calls
        """
        seen_tool_calls: Dict[str, Dict[str, Any]] = {}
        unique_steps = []

        for step in steps:
            tool_sig = self._make_tool_signature(step)
            if tool_sig not in seen_tool_calls:
                seen_tool_calls[tool_sig] = step.args
                unique_steps.append(step)
            else:
                logger.debug(f"Removed redundant call to {step.tool}")

        return unique_steps

    def _reorder_for_parallelization(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """Reorder steps to enable parallel execution where possible.

        Args:
            steps: Execution steps

        Returns:
            Reordered steps
        """
        # For now, return original order
        # Can be enhanced with dependency graph analysis
        return steps

    def _detect_circular_dependencies(self, steps: List[ExecutionStep]) -> bool:
        """Detect circular dependencies in plan.

        Args:
            steps: Execution steps

        Returns:
            True if cycles detected
        """
        # Simple check: if format_code appears after generate_code with same args
        # and format_code output is used as input to generate_code
        code_related = {"generate_code", "review_code", "format_code", "generate_tests"}
        
        code_args = {}
        for step in steps:
            if step.tool in code_related:
                if "code" in step.args:
                    code_hash = hash(step.args.get("code", ""))
                    if code_hash in code_args:
                        # Potential cycle
                        return True
                    code_args[code_hash] = True

        return False

    def _estimate_time(self, steps: List[ExecutionStep]) -> float:
        """Estimate execution time.

        Args:
            steps: Execution steps

        Returns:
            Estimated time in seconds
        """
        # Rough estimates: generation 10s, review 5s, format 2s, etc.
        tool_times = {
            "generate_code": 10.0,
            "review_code": 5.0,
            "format_code": 2.0,
            "generate_tests": 8.0,
            "analyze_complexity": 1.0,
            "formalize_task": 3.0,
        }

        total_time = sum(tool_times.get(step.tool, 5.0) for step in steps)
        return total_time

    def _make_tool_signature(self, step: ExecutionStep) -> str:
        """Create tool signature from step.

        Args:
            step: Execution step

        Returns:
            Tool signature string
        """
        # Create signature from tool name and key arguments
        args_str = str(sorted(step.args.items()))[:100]
        return f"{step.tool}:{args_str}"

    def suggest_parallel_groups(self, plan: ExecutionPlan) -> List[List[ExecutionStep]]:
        """Suggest groups of steps that can run in parallel.

        Args:
            plan: Execution plan

        Returns:
            List of step groups (steps in same group can run in parallel)
        """
        groups = []
        current_group = []
        
        for step in plan.steps:
            # Check if step has dependencies on previous rends
            deps = self.tool_dependencies.get(step.tool, [])
            
            # If no dependencies on current group, add to group
            if not any(prev.tool in deps for prev in current_group):
                current_group.append(step)
            else:
                # Start new group
                if current_group:
                    groups.append(current_group)
                current_group = [step]

        if current_group:
            groups.append(current_group)

        return groups

