"""
Compression strategy pattern implementation.

Defines available compression strategies and provides
factory for creating compressor instances.
"""

from enum import Enum
from typing import Dict, Type
from core.interfaces.protocols import TokenCounterProtocol, CompressorProtocol
from core.compressors.base import BaseCompressor
from core.compressors.truncation import TruncationCompressor
from core.compressors.keywords import KeywordsCompressor


class CompressionStrategy(Enum):
    """Available compression strategies."""
    
    TRUNCATION = "truncation"
    KEYWORDS = "keywords"
    # Future strategies can be added here
    # EXTRACTIVE = "extractive"
    # SEMANTIC = "semantic"
    # SUMMARIZATION = "summarization"


class CompressionStrategyFactory:
    """Factory for creating compression strategy instances."""
    
    _strategies: Dict[CompressionStrategy, Type[BaseCompressor]] = {
        CompressionStrategy.TRUNCATION: TruncationCompressor,
        CompressionStrategy.KEYWORDS: KeywordsCompressor,
    }
    
    @classmethod
    def create(
        cls, 
        strategy: CompressionStrategy, 
        token_counter: TokenCounterProtocol
    ) -> CompressorProtocol:
        """
        Create compressor instance for specified strategy.
        
        Args:
            strategy: Compression strategy to use
            token_counter: Token counter instance
            
        Returns:
            CompressorProtocol: Configured compressor instance
            
        Raises:
            ValueError: If strategy is not supported
        """
        if strategy not in cls._strategies:
            available = [s.value for s in cls._strategies.keys()]
            raise ValueError(f"Unsupported strategy: {strategy.value}. Available: {available}")
        
        compressor_class = cls._strategies[strategy]
        return compressor_class(token_counter)
    
    @classmethod
    def get_available_strategies(cls) -> list[str]:
        """
        Get list of available strategy names.
        
        Returns:
            list[str]: List of strategy names
        """
        return [strategy.value for strategy in cls._strategies.keys()]
    
    @classmethod
    def is_strategy_supported(cls, strategy_name: str) -> bool:
        """
        Check if strategy is supported.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            bool: True if strategy is supported
        """
        try:
            strategy = CompressionStrategy(strategy_name)
            return strategy in cls._strategies
        except ValueError:
            return False
