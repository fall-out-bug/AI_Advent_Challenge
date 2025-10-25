"""
Compression strategies module.

Provides various text compression strategies using
Strategy pattern and Template Method pattern.
"""

from .base import BaseCompressor
from .truncation import TruncationCompressor
from .keywords import KeywordsCompressor
from .strategy import CompressionStrategy, CompressionStrategyFactory

__all__ = [
    "BaseCompressor",
    "TruncationCompressor", 
    "KeywordsCompressor",
    "CompressionStrategy",
    "CompressionStrategyFactory",
]
