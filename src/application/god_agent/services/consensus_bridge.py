"""Consensus Bridge service for God Agent."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep
from src.infrastructure.logging import get_logger

logger = get_logger("consensus_bridge")


class ConsensusBridge:
    """Consensus Bridge service.

    Purpose:
        Implements file-based multi-agent consensus workflow following
        consensus_architecture.json schema.

    Attributes:
        epic_id: Epic identifier.
        consensus_base_path: Base path for consensus files.
        timeout_seconds: Timeout for consensus requests (default: 300s).

    Example:
        >>> bridge = ConsensusBridge(
        ...     epic_id="epic_28",
        ...     consensus_base_path=Path("docs/specs/epic_28/consensus"),
        ...     timeout_seconds=300
        ... )
        >>> consensus_id = await bridge.request_consensus(
        ...     task_plan=plan,
        ...     step=step,
        ...     context={"reason": "critical_step"}
        ... )
    """

    def __init__(
        self,
        epic_id: str,
        consensus_base_path: Path,
        timeout_seconds: int = 300,
    ) -> None:
        """Initialize consensus bridge.

        Args:
            epic_id: Epic identifier.
            consensus_base_path: Base path for consensus files.
            timeout_seconds: Timeout for consensus requests (default: 300s).
        """
        self.epic_id = epic_id
        self.consensus_base_path = Path(consensus_base_path)
        self.timeout_seconds = timeout_seconds
        self.artifacts_dir = self.consensus_base_path / "artifacts"
        self.messages_dir = self.consensus_base_path / "messages" / "inbox"
        self.decision_log_path = self.consensus_base_path / "decision_log.jsonl"

        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        self.decision_log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "ConsensusBridge initialized",
            extra={
                "epic_id": epic_id,
                "consensus_base_path": str(consensus_base_path),
                "timeout_seconds": timeout_seconds,
            },
        )

    async def request_consensus(
        self,
        task_plan: TaskPlan,
        step: TaskStep,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Request consensus for a task step.

        Purpose:
            Creates consensus files following consensus_architecture.json schema
            and waits for decision (with timeout).

        Args:
            task_plan: Task plan containing the step.
            step: Task step requiring consensus.
            context: Optional context dictionary.

        Returns:
            Consensus request ID.

        Raises:
            asyncio.TimeoutError: If consensus timeout is reached.

        Example:
            >>> consensus_id = await bridge.request_consensus(
            ...     task_plan=plan,
            ...     step=step,
            ...     context={"reason": "critical_step"}
            ... )
        """
        consensus_id = str(uuid.uuid4())
        context = context or {}

        try:
            # Create consensus request file
            await self._create_consensus_request(
                consensus_id=consensus_id,
                task_plan=task_plan,
                step=step,
                context=context,
            )

            # Log decision entry
            await self._log_decision(
                decision="propose",
                agent="developer",
                details={
                    "status": f"consensus_request_{consensus_id}",
                    "changes_from_previous": context.get(
                        "reason", "step_requires_consensus"
                    ),
                },
            )

            # Wait for consensus (with timeout)
            await asyncio.wait_for(
                self._wait_for_consensus(consensus_id),
                timeout=self.timeout_seconds,
            )

            logger.info(
                "Consensus request completed",
                extra={
                    "consensus_id": consensus_id,
                    "step_id": step.step_id,
                },
            )

            return consensus_id

        except asyncio.TimeoutError:
            logger.warning(
                "Consensus request timed out",
                extra={
                    "consensus_id": consensus_id,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
            raise

    async def check_veto_status(self, consensus_id: str) -> bool:
        """Check if consensus has veto status.

        Purpose:
            Reads decision_log.jsonl to check for veto decisions.

        Args:
            consensus_id: Consensus request ID.

        Returns:
            True if veto detected, False otherwise.

        Example:
            >>> has_veto = await bridge.check_veto_status("consensus_1")
            >>> if has_veto:
            ...     # Handle veto
        """
        if not self.decision_log_path.exists():
            return False

        try:
            with open(self.decision_log_path, "r") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    if entry.get("decision") == "veto":
                        # Check if this veto is related to our consensus
                        details = entry.get("details", {})
                        if consensus_id in str(details):
                            return True
                        # Also check if it's the most recent veto for this epic
                        if entry.get("epic_id") == self.epic_id:
                            return True

            return False

        except Exception as e:
            logger.error(
                "Failed to check veto status",
                extra={"consensus_id": consensus_id, "error": str(e)},
                exc_info=True,
            )
            return False

    async def _create_consensus_request(
        self,
        consensus_id: str,
        task_plan: TaskPlan,
        step: TaskStep,
        context: Dict[str, Any],
    ) -> None:
        """Create consensus request file.

        Args:
            consensus_id: Consensus request ID.
            task_plan: Task plan.
            step: Task step.
            context: Context dictionary.
        """
        request_file = self.artifacts_dir / f"consensus_request_{consensus_id}.json"

        request_data = {
            "consensus_id": consensus_id,
            "epic_id": self.epic_id,
            "iteration": 1,
            "task_plan_id": task_plan.plan_id,
            "step_id": step.step_id,
            "skill_type": step.skill_type.value
            if hasattr(step.skill_type, "value")
            else str(step.skill_type),
            "context": context,
            "timestamp": datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
        }

        with open(request_file, "w") as f:
            json.dump(request_data, f, indent=2)

        logger.debug(
            "Consensus request file created",
            extra={"consensus_id": consensus_id, "file": str(request_file)},
        )

    async def _log_decision(
        self,
        decision: str,
        agent: str,
        details: Dict[str, Any],
    ) -> None:
        """Log decision to decision_log.jsonl.

        Args:
            decision: Decision type (propose, approve, veto, escalate).
            agent: Agent name.
            details: Decision details.
        """
        entry = {
            "timestamp": datetime.now().strftime("%Y_%m_%d_%H_%M_%S"),
            "agent": agent,
            "decision": decision,
            "epic_id": self.epic_id,
            "iteration": 1,
            "previous_artifacts": [],
            "details": details,
        }

        with open(self.decision_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.debug(
            "Decision logged",
            extra={"decision": decision, "agent": agent},
        )

    async def _wait_for_consensus(self, consensus_id: str) -> None:
        """Wait for consensus decision.

        Args:
            consensus_id: Consensus request ID.

        Raises:
            asyncio.TimeoutError: If timeout is reached.
        """
        # Poll decision log for consensus decision
        max_iterations = self.timeout_seconds // 5  # Check every 5 seconds
        iteration = 0

        while iteration < max_iterations:
            # Check for veto
            if await self.check_veto_status(consensus_id):
                logger.info(
                    "Veto detected in consensus",
                    extra={"consensus_id": consensus_id},
                )
                return

            # Check for approval (simplified: check if decision log has approve)
            if self.decision_log_path.exists():
                with open(self.decision_log_path, "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        if last_entry.get("decision") == "approve":
                            logger.info(
                                "Consensus approved",
                                extra={"consensus_id": consensus_id},
                            )
                            return

            await asyncio.sleep(5)  # Wait 5 seconds before next check
            iteration += 1

        raise asyncio.TimeoutError(
            f"Consensus timeout after {self.timeout_seconds} seconds"
        )
