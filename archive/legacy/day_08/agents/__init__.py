"""
Agent adapters for integrating SDK agents with day_08 system.

This module provides adapters that wrap SDK CodeGeneratorAgent and 
CodeReviewerAgent for seamless integration with the day_08 token analysis
and compression system.
"""

from .code_generator_adapter import CodeGeneratorAdapter
from .code_reviewer_adapter import CodeReviewerAdapter

__all__ = [
    "CodeGeneratorAdapter",
    "CodeReviewerAdapter"
]