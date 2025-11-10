"""
Orchestration module for agent coordination patterns.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

from .adapters import (
    AdapterConfig,
    AdapterFactory,
    AdapterType,
    CommunicationAdapter,
    DirectAdapter,
    RestAdapter,
)
from .base_orchestrator import (
    BaseOrchestrator,
    OrchestrationConfig,
    OrchestrationResult,
    OrchestrationStatus,
)
from .parallel import ParallelOrchestrator
from .sequential import SequentialOrchestrator

__all__ = [
    # Adapters
    "CommunicationAdapter",
    "DirectAdapter",
    "RestAdapter",
    "AdapterFactory",
    "AdapterType",
    "AdapterConfig",
    # Orchestrators
    "BaseOrchestrator",
    "SequentialOrchestrator",
    "ParallelOrchestrator",
    # Schemas
    "OrchestrationResult",
    "OrchestrationStatus",
    "OrchestrationConfig",
]
