"""Compression domain services.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

from src.domain.services.compression.compressor import CompressionService
from src.domain.services.compression.strategies.base_compressor import BaseCompressor
from src.domain.services.compression.strategies.keyword_compressor import (
    KeywordCompressor,
)
from src.domain.services.compression.strategies.truncation_compressor import (
    TruncationCompressor,
)

__all__ = [
    "CompressionService",
    "BaseCompressor",
    "TruncationCompressor",
    "KeywordCompressor",
]
