"""Audit event value objects used for privileged operation logging."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    """Immutable representation of an audit log entry.

    Purpose:
        Capture the essential metadata for privileged user actions so logs can
        be persisted, queried, and analysed for compliance.

    Attributes:
        event_id: Unique identifier for the audit event.
        timestamp: UTC timestamp indicating when the event occurred.
        actor: Identifier for the actor performing the action.
        action: Canonical action name (for example, ``mcp_tool_call``).
        resource: Resource or object acted upon.
        outcome: Result of the action (for example, ``success`` or ``error``).
        metadata: Additional structured metadata describing the event.
        trace_id: Optional correlation identifier for cross-service tracing.

    Example:
        >>> AuditEvent.create(
        ...     actor="mcp-http",
        ...     action="mcp_tool_call",
        ...     resource="digest.generate",
        ...     outcome="success",
        ...     metadata={"duration_ms": 1200},
        ... )
    """

    actor: str
    action: str
    resource: str
    outcome: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(
        cls,
        *,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> "AuditEvent":
        """Convenience constructor for audit events."""

        return cls(
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            metadata=metadata or {},
            trace_id=trace_id,
            event_id=event_id or uuid4().hex,
            timestamp=datetime.now(timezone.utc),
        )

    def to_log_payload(self) -> Dict[str, Any]:
        """Convert the event to a JSON-serialisable dictionary."""

        payload: Dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "metadata": self.metadata,
        }
        if self.trace_id:
            payload["trace_id"] = self.trace_id
        return payload
