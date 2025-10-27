"""Messaging module for agent communication.

Provides message schemas for inter-agent communication
using Pydantic models for validation.
"""

from src.domain.messaging.message_schema import (
    AgentHealthResponse,
    AgentStatsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewRequest,
    CodeReviewResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    TaskMetadata,
)

__all__ = [
    "TaskMetadata",
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    "CodeQualityMetrics",
    "CodeReviewRequest",
    "CodeReviewResponse",
    "OrchestratorRequest",
    "OrchestratorResponse",
    "AgentHealthResponse",
    "AgentStatsResponse",
]
