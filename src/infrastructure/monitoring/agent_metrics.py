"""Prometheus metrics for MCP-aware agent.

Following Python Zen: "Explicit is better than implicit".
"""

import logging
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


# Agent metrics
agent_requests_total = Counter(
    "agent_requests_total",
    "Total number of agent requests",
    ["user_id", "status"]
)

agent_tokens_used = Counter(
    "agent_tokens_used_total",
    "Total tokens used by agent",
    ["user_id"]
)

agent_request_duration = Histogram(
    "agent_request_duration_seconds",
    "Agent request duration in seconds",
    ["user_id"]
)

agent_tools_used = Counter(
    "agent_tools_used_total",
    "Total number of tools used",
    ["tool_name", "status"]
)

agent_dialog_messages = Counter(
    "agent_dialog_messages_total",
    "Total dialog messages",
    ["session_id", "role"]
)

agent_dialog_tokens = Gauge(
    "agent_dialog_tokens",
    "Current dialog token count",
    ["session_id"]
)

# MCP Client metrics
mcp_client_requests_total = Counter(
    "mcp_client_requests_total",
    "Total MCP client requests",
    ["tool_name", "status"]
)

mcp_client_retries_total = Counter(
    "mcp_client_retries_total",
    "Total MCP client retries",
    ["tool_name", "reason"]
)

mcp_client_request_duration = Histogram(
    "mcp_client_request_duration_seconds",
    "MCP client request duration",
    ["tool_name"]
)

# LLM metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model_name", "status"]
)

llm_tokens = Counter(
    "llm_tokens_total",
    "Total LLM tokens",
    ["model_name", "type"]
)

llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration",
    ["model_name"]
)


class AgentMetrics:
    """Metrics collector for agent operations."""
    
    @staticmethod
    def record_request(
        user_id: int,
        success: bool,
        duration: float,
        tokens: int = 0
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
    def record_tool_use(
        tool_name: str,
        success: bool
    ) -> None:
        """Record tool usage.
        
        Args:
            tool_name: Tool name
            success: Whether tool call succeeded
        """
        status = "success" if success else "error"
        agent_tools_used.labels(tool_name=tool_name, status=status).inc()
    
    @staticmethod
    def record_dialog_message(
        session_id: str,
        role: str,
        tokens: int
    ) -> None:
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
        tool_name: str,
        success: bool,
        duration: float,
        retries: int = 0
    ) -> None:
        """Record MCP client request.
        
        Args:
            tool_name: Tool name
            success: Whether request succeeded
            duration: Request duration in seconds
            retries: Number of retries
        """
        status = "success" if success else "error"
        mcp_client_requests_total.labels(tool_name=tool_name, status=status).inc()
        mcp_client_request_duration.labels(tool_name=tool_name).observe(duration)
        
        if retries > 0:
            mcp_client_retries_total.labels(
                tool_name=tool_name,
                reason="timeout"
            ).inc(retries)
    
    @staticmethod
    def record_retry(
        tool_name: str,
        reason: str
    ) -> None:
        """Record retry.
        
        Args:
            tool_name: Tool name
            reason: Retry reason
        """
        mcp_client_retries_total.labels(tool_name=tool_name, reason=reason).inc()


class LLMMetrics:
    """Metrics collector for LLM operations."""
    
    @staticmethod
    def record_request(
        model_name: str,
        success: bool,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0
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

