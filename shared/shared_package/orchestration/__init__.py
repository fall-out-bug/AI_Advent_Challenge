"""
Orchestration module for agent coordination patterns.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

from .adapters import (
    CommunicationAdapter,
    DirectAdapter,
    RestAdapter,
    AdapterFactory,
    AdapterType,
    AdapterConfig
)
from .base_orchestrator import (
    BaseOrchestrator,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestrationConfig
)
from .sequential import SequentialOrchestrator
from .parallel import ParallelOrchestrator

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
    "OrchestrationConfig"
]
