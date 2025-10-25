"""
Compression strategies module.

Provides various text compression strategies using
Strategy pattern and Template Method pattern.
"""

from .base import BaseCompressor
from .keywords import KeywordsCompressor
from .strategy import CompressionStrategy, CompressionStrategyFactory
from .truncation import TruncationCompressor

__all__ = [
    "BaseCompressor",
    "TruncationCompressor",
    "KeywordsCompressor",
    "CompressionStrategy",
    "CompressionStrategyFactory",
]
