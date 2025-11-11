"""RAG (Retrieval-Augmented Generation) application layer.

Purpose:
    Provide use cases and services for RAG vs non-RAG comparison.
"""

from .prompt_assembler import PromptAssembler
from .retrieval_service import RetrievalService
from .use_case import CompareRagAnswersUseCase

__all__ = [
    "CompareRagAnswersUseCase",
    "PromptAssembler",
    "RetrievalService",
]
