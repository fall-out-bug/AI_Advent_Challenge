"""Prometheus metrics for God Agent.

Purpose:
    Exports Prometheus metrics for God Agent observability:
    - god_agent_tasks_total: Total number of tasks processed
    - god_agent_plan_duration_seconds: Plan compilation duration
    - god_agent_veto_total: Total number of vetoes raised
    - god_agent_skill_latency_seconds: Skill execution latency
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except ImportError:  # pragma: no cover - fallback
    # Fallback for environments without prometheus_client
    class _DummyMetric:
        """Fallback metric used when prometheus_client is unavailable."""

        def labels(self, *args: object, **kwargs: object) -> "_DummyMetric":  # type: ignore[no-untyped-def]
            """Mirror the prometheus metric interface by returning self."""
            return self

        def inc(self, *args: object, **kwargs: object) -> None:
            """No-op increment method."""

        def observe(self, *args: object, **kwargs: object) -> None:
            """No-op observation method."""

    Counter = Histogram = _DummyMetric  # type: ignore


# Metrics definitions
GOD_AGENT_TASKS_TOTAL = Counter(  # type: ignore[arg-type]
    "god_agent_tasks_total",
    "Total number of tasks processed by God Agent.",
    labelnames=("skill_type", "status"),
)

GOD_AGENT_PLAN_DURATION_SECONDS = Histogram(  # type: ignore[arg-type]
    "god_agent_plan_duration_seconds",
    "Plan compilation duration in seconds.",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

GOD_AGENT_VETO_TOTAL = Counter(  # type: ignore[arg-type]
    "god_agent_veto_total",
    "Total number of vetoes raised.",
    labelnames=("veto_rule",),
)

GOD_AGENT_SKILL_LATENCY_SECONDS = Histogram(  # type: ignore[arg-type]
    "god_agent_skill_latency_seconds",
    "Skill execution latency in seconds.",
    labelnames=("skill_type",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)


class GodAgentMetrics:
    """God Agent metrics exporter.

    Purpose:
        Provides access to Prometheus metrics for God Agent observability.

    Attributes:
        tasks_total: Counter for task executions.
        plan_duration_seconds: Histogram for plan compilation duration.
        veto_total: Counter for vetoes raised.
        skill_latency_seconds: Histogram for skill execution latency.

    Example:
        >>> metrics = GodAgentMetrics()
        >>> record_task_execution("concierge", "success")
    """

    def __init__(self) -> None:
        """Initialize metrics."""
        self.tasks_total = GOD_AGENT_TASKS_TOTAL
        self.plan_duration_seconds = GOD_AGENT_PLAN_DURATION_SECONDS
        self.veto_total = GOD_AGENT_VETO_TOTAL
        self.skill_latency_seconds = GOD_AGENT_SKILL_LATENCY_SECONDS


def record_task_execution(skill_type: str, status: str) -> None:
    """Record a task execution.

    Purpose:
        Increment the god_agent_tasks_total counter.

    Args:
        skill_type: Type of skill executed (concierge, research, etc.).
        status: Execution status (success, failure).

    Example:
        >>> record_task_execution("concierge", "success")
    """
    GOD_AGENT_TASKS_TOTAL.labels(skill_type=skill_type, status=status).inc()


def record_plan_duration(duration_seconds: float) -> None:
    """Record plan compilation duration.

    Purpose:
        Observe the plan compilation duration in the histogram.

    Args:
        duration_seconds: Duration in seconds.

    Example:
        >>> record_plan_duration(2.5)
    """
    GOD_AGENT_PLAN_DURATION_SECONDS.observe(duration_seconds)


def record_veto(veto_rule: str) -> None:
    """Record a veto.

    Purpose:
        Increment the god_agent_veto_total counter.

    Args:
        veto_rule: Type of veto rule (untestable_requirement, etc.).

    Example:
        >>> record_veto("untestable_requirement")
    """
    GOD_AGENT_VETO_TOTAL.labels(veto_rule=veto_rule).inc()


def record_skill_latency(skill_type: str, duration_seconds: float) -> None:
    """Record skill execution latency.

    Purpose:
        Observe the skill execution latency in the histogram.

    Args:
        skill_type: Type of skill executed.
        duration_seconds: Duration in seconds.

    Example:
        >>> record_skill_latency("concierge", 0.5)
    """
    GOD_AGENT_SKILL_LATENCY_SECONDS.labels(skill_type=skill_type).observe(
        duration_seconds
    )
