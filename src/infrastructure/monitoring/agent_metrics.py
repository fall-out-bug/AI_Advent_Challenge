"""Prometheus metrics for MCP-aware agent.

Following Python Zen: "Explicit is better than implicit".
"""

import logging

from prometheus_client import REGISTRY, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Track if metrics are already registered to avoid duplicate registration
_metrics_initialized = False
_metrics_cache: dict[str, Counter | Histogram | Gauge] = {}


def _get_or_create_metric(
    metric_type: type[Counter | Histogram | Gauge],
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
    **kwargs,
) -> Counter | Histogram | Gauge:
    """Get existing metric or create new one to avoid duplicates.

    Args:
        metric_type: Type of metric (Counter, Histogram, or Gauge)
        name: Metric name
        documentation: Metric documentation
        labelnames: Label names for the metric
        **kwargs: Additional arguments for metric creation

    Returns:
        Existing or newly created metric
    """
    global _metrics_cache

    if name in _metrics_cache:
        return _metrics_cache[name]

    # Check if metric already exists in registry
    try:
        existing = REGISTRY._names_to_collectors.get(name)
        if existing:
            _metrics_cache[name] = existing
            return existing
    except Exception:
        pass

    # Create new metric
    if labelnames:
        metric = metric_type(name, documentation, labelnames, **kwargs)
    else:
        metric = metric_type(name, documentation, **kwargs)

    _metrics_cache[name] = metric
    return metric


# Agent metrics
agent_requests_total = _get_or_create_metric(
    Counter,
    "agent_requests_total",
    "Total number of agent requests",
    ["user_id", "status"],
)

agent_tokens_used = _get_or_create_metric(
    Counter, "agent_tokens_used_total", "Total tokens used by agent", ["user_id"]
)

agent_request_duration = _get_or_create_metric(
    Histogram,
    "agent_request_duration_seconds",
    "Agent request duration in seconds",
    ["user_id"],
)

agent_tools_used = _get_or_create_metric(
    Counter,
    "agent_tools_used_total",
    "Total number of tools used",
    ["tool_name", "status"],
)

agent_dialog_messages = _get_or_create_metric(
    Counter,
    "agent_dialog_messages_total",
    "Total dialog messages",
    ["session_id", "role"],
)

agent_dialog_tokens = _get_or_create_metric(
    Gauge, "agent_dialog_tokens", "Current dialog token count", ["session_id"]
)

<<<<<<< HEAD
# MCP Client metrics
=======
# MCP Client metrics (aligned with mcp_metrics.py: use "tool" label for consistency)
>>>>>>> origin/master
mcp_client_requests_total = _get_or_create_metric(
    Counter,
    "mcp_client_requests_total",
    "Total MCP client requests",
<<<<<<< HEAD
    ["tool_name", "status"],
=======
    ["tool", "status"],  # Changed from "tool_name" to "tool" for consistency
>>>>>>> origin/master
)

mcp_client_retries_total = _get_or_create_metric(
    Counter,
    "mcp_client_retries_total",
    "Total MCP client retries",
<<<<<<< HEAD
    ["tool_name", "reason"],
=======
    ["tool", "reason"],  # Changed from "tool_name" to "tool" for consistency
>>>>>>> origin/master
)

mcp_client_request_duration = _get_or_create_metric(
    Histogram,
    "mcp_client_request_duration_seconds",
    "MCP client request duration",
<<<<<<< HEAD
    ["tool_name"],
=======
    ["tool"],  # Changed from "tool_name" to "tool" for consistency
>>>>>>> origin/master
)

# LLM metrics
llm_requests_total = _get_or_create_metric(
    Counter, "llm_requests_total", "Total LLM requests", ["model_name", "status"]
)

llm_tokens = _get_or_create_metric(
    Counter, "llm_tokens_total", "Total LLM tokens", ["model_name", "type"]
)

llm_request_duration = _get_or_create_metric(
    Histogram, "llm_request_duration_seconds", "LLM request duration", ["model_name"]
)

# Long tasks metrics
long_tasks_total = _get_or_create_metric(
    Counter, "long_tasks_total", "Total long summarization tasks", ["status"]
)

long_tasks_duration = _get_or_create_metric(
    Histogram,
    "long_tasks_duration_seconds",
    "Long task processing duration in seconds",
    ["status"],
)

long_tasks_queue_size = _get_or_create_metric(
    Gauge, "long_tasks_queue_size", "Current number of queued long tasks"
)


class AgentMetrics:
    """Metrics collector for agent operations."""

    @staticmethod
    def record_request(
        user_id: int, success: bool, duration: float, tokens: int = 0
    ) -> None:
        """Record agent request.

        Args:
            user_id: User ID
            success: Whether request succeeded
            duration: Request duration in seconds
            tokens: Tokens used
        """
        status = "success" if success else "error"
        agent_requests_total.labels(user_id=str(user_id), status=status).inc()
        agent_request_duration.labels(user_id=str(user_id)).observe(duration)

        if tokens > 0:
            agent_tokens_used.labels(user_id=str(user_id)).inc(tokens)

    @staticmethod
    def record_tool_use(tool_name: str, success: bool) -> None:
        """Record tool usage.

        Args:
            tool_name: Tool name
            success: Whether tool call succeeded
        """
        status = "success" if success else "error"
        agent_tools_used.labels(tool_name=tool_name, status=status).inc()

    @staticmethod
    def record_dialog_message(session_id: str, role: str, tokens: int) -> None:
        """Record dialog message.

        Args:
            session_id: Session ID
            role: Message role
            tokens: Token count
        """
        agent_dialog_messages.labels(session_id=session_id, role=role).inc()
        agent_dialog_tokens.labels(session_id=session_id).set(tokens)


class MCPClientMetrics:
    """Metrics collector for MCP client operations."""

    @staticmethod
    def record_request(
        tool_name: str, success: bool, duration: float, retries: int = 0
    ) -> None:
        """Record MCP client request.

        Args:
<<<<<<< HEAD
            tool_name: Tool name
=======
            tool_name: Tool name (used as "tool" label for consistency)
>>>>>>> origin/master
            success: Whether request succeeded
            duration: Request duration in seconds
            retries: Number of retries
        """
        status = "success" if success else "error"
<<<<<<< HEAD
        mcp_client_requests_total.labels(tool_name=tool_name, status=status).inc()
        mcp_client_request_duration.labels(tool_name=tool_name).observe(duration)

        if retries > 0:
            mcp_client_retries_total.labels(tool_name=tool_name, reason="timeout").inc(
=======
        # Use "tool" label (not "tool_name") for consistency with mcp_metrics.py
        mcp_client_requests_total.labels(tool=tool_name, status=status).inc()
        mcp_client_request_duration.labels(tool=tool_name).observe(duration)

        if retries > 0:
            mcp_client_retries_total.labels(tool=tool_name, reason="timeout").inc(
>>>>>>> origin/master
                retries
            )

    @staticmethod
    def record_retry(tool_name: str, reason: str) -> None:
        """Record retry.

        Args:
<<<<<<< HEAD
            tool_name: Tool name
            reason: Retry reason
        """
        mcp_client_retries_total.labels(tool_name=tool_name, reason=reason).inc()
=======
            tool_name: Tool name (used as "tool" label for consistency)
            reason: Retry reason
        """
        # Use "tool" label (not "tool_name") for consistency with mcp_metrics.py
        mcp_client_retries_total.labels(tool=tool_name, reason=reason).inc()
>>>>>>> origin/master


class LLMMetrics:
    """Metrics collector for LLM operations."""

    @staticmethod
    def record_request(
        model_name: str,
        success: bool,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record LLM request.

        Args:
            model_name: Model name
            success: Whether request succeeded
            duration: Request duration in seconds
            input_tokens: Input tokens
            output_tokens: Output tokens
        """
        status = "success" if success else "error"
        llm_requests_total.labels(model_name=model_name, status=status).inc()
        llm_request_duration.labels(model_name=model_name).observe(duration)

        if input_tokens > 0:
            llm_tokens.labels(model_name=model_name, type="input").inc(input_tokens)

        if output_tokens > 0:
            llm_tokens.labels(model_name=model_name, type="output").inc(output_tokens)
