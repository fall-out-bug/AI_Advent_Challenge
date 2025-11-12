"""RAG (Retrieval-Augmented Generation) domain layer.

Purpose:
    Provide domain entities and interfaces for the RAG vs non-RAG
    comparison system (Epic 20).
"""

from .interfaces import (
    LLMService,
    RelevanceFilterService,
    RerankerService,
    VectorSearchService,
)
from .value_objects import (
    Answer,
    ComparisonResult,
    FilterConfig,
    Query,
    RerankResult,
    RetrievedChunk,
)

__all__ = [
    "Answer",
    "ComparisonResult",
    "FilterConfig",
    "LLMService",
    "Query",
    "RelevanceFilterService",
    "RerankerService",
    "RerankResult",
    "RetrievedChunk",
    "VectorSearchService",
]
