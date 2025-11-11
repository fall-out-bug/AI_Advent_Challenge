"""RAG (Retrieval-Augmented Generation) domain layer.

Purpose:
    Provide domain entities and interfaces for the RAG vs non-RAG
    comparison system (Epic 20).
"""

from .interfaces import LLMService, VectorSearchService
from .value_objects import Answer, ComparisonResult, Query, RetrievedChunk

__all__ = [
    "Answer",
    "ComparisonResult",
    "LLMService",
    "Query",
    "RetrievedChunk",
    "VectorSearchService",
]
