"""Ops skill adapter for God Agent."""

import uuid
from typing import Any, Dict

import aiohttp

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.interfaces.skill_adapter import ISkillAdapter
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.logging import get_logger

logger = get_logger("ops_skill_adapter")


class OpsSkillAdapter:
    """Ops skill adapter.

    Purpose:
        Provides ops skill interface for God Agent, fetching Prometheus
        metrics and executing infrastructure checks.

    Attributes:
        prometheus_url: Prometheus server URL.

    Example:
        >>> adapter = OpsSkillAdapter(prometheus_url="http://localhost:9090")
        >>> result = await adapter.execute(
        ...     {"action": "metrics", "query": "up"},
        ...     memory_snapshot
        ... )
    """

    def __init__(self, prometheus_url: str = "http://127.0.0.1:9090") -> None:
        """Initialize ops skill adapter.

        Args:
            prometheus_url: Prometheus server URL (default: http://127.0.0.1:9090).
        """
        self.prometheus_url = prometheus_url
        logger.info(
            "OpsSkillAdapter initialized",
            extra={"prometheus_url": prometheus_url},
        )

    async def execute(
        self, input_data: Dict[str, Any], memory_snapshot: MemorySnapshot
    ) -> SkillResult:
        """Execute ops skill.

        Purpose:
            Execute ops operations (fetch Prometheus metrics, health checks)
            and convert result to SkillResult.

        Args:
            input_data: Input dictionary with 'action' ('metrics', 'health'),
                optional 'query' for metrics.
            memory_snapshot: Memory snapshot for context (not used directly,
                but available for future enhancements).

        Returns:
            SkillResult with ops status, metrics, or error.

        Example:
            >>> result = await adapter.execute(
            ...     {"action": "metrics", "query": "up"},
            ...     memory_snapshot
            ... )
            >>> result.status
            <SkillResultStatus.SUCCESS: 'success'>
        """
        try:
            action = input_data.get("action", "health")

            if action == "metrics":
                return await self._fetch_metrics(input_data)
            elif action == "health":
                return await self._check_health()
            else:
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.FAILURE,
                    error=f"Unknown action: {action}",
                )

        except Exception as e:
            logger.error(
                "Ops skill execution failed",
                extra={"error": str(e), "input_data": input_data},
                exc_info=True,
            )
            return SkillResult(
                result_id=str(uuid.uuid4()),
                status=SkillResultStatus.FAILURE,
                error=f"Ops skill error: {str(e)}",
            )

    async def _fetch_metrics(self, input_data: Dict[str, Any]) -> SkillResult:
        """Fetch Prometheus metrics.

        Args:
            input_data: Input dictionary with 'query'.

        Returns:
            SkillResult with metrics data.
        """
        query = input_data.get("query", "up")
        query_url = f"{self.prometheus_url}/api/v1/query"

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, params={"query": query}) as response:
                if response.status != 200:
                    return SkillResult(
                        result_id=str(uuid.uuid4()),
                        status=SkillResultStatus.FAILURE,
                        error=f"Prometheus query failed: {response.status}",
                    )

                data = await response.json()
                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.SUCCESS,
                    output={
                        "metrics": data,
                        "query": query,
                    },
                    metadata={
                        "skill_type": SkillType.OPS.value,
                        "prometheus_url": self.prometheus_url,
                    },
                )

    async def _check_health(self) -> SkillResult:
        """Check Prometheus health.

        Returns:
            SkillResult with health status.
        """
        health_url = f"{self.prometheus_url}/-/ready"

        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                is_healthy = response.status == 200
                status_text = await response.text()

                return SkillResult(
                    result_id=str(uuid.uuid4()),
                    status=SkillResultStatus.SUCCESS,
                    output={
                        "status": "healthy" if is_healthy else "unhealthy",
                        "response": status_text,
                        "status_code": response.status,
                    },
                    metadata={
                        "skill_type": SkillType.OPS.value,
                        "prometheus_url": self.prometheus_url,
                    },
                )

    def get_skill_id(self) -> str:
        """Get skill identifier.

        Purpose:
            Return unique identifier for ops skill.

        Returns:
            Skill type as string ('ops').

        Example:
            >>> adapter.get_skill_id()
            'ops'
        """
        return SkillType.OPS.value
