"""Audit logging helpers for privileged operations."""

from __future__ import annotations

from typing import Dict

from src.domain.value_objects.audit_event import AuditEvent
from src.infrastructure.logging import get_logger, log_context

_AUDIT_LOGGER = get_logger("audit", enable_json=True)


def log_audit_event(event: AuditEvent) -> None:
    """Emit an audit event to the structured logging pipeline.

    Purpose:
        Persist privileged actions such as MCP tool invocations with dedicated
        metadata under the ``stream=audit`` label so they can be routed to
        retention-compliant storage.

    Args:
        event: Audit event value object describing the operation.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> event = AuditEvent.create(
        ...     actor="mcp-http",
        ...     action="mcp_tool_call",
        ...     resource="digest.generate",
        ...     outcome="success",
        ... )
        >>> log_audit_event(event)
    """

    payload: Dict[str, object] = event.to_log_payload()
    with log_context(stream="audit"):
        _AUDIT_LOGGER.info("audit_event", **payload)
