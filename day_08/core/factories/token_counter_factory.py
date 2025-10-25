"""
Factory for creating token counter instances.

Provides factory methods for creating different types of token counters
with proper configuration injection.
"""

from typing import Optional
from core.interfaces.protocols import ConfigurationProtocol, TokenCounterProtocol
from core.token_analyzer import SimpleTokenCounter, TokenCounter, LimitProfile
from core.accurate_token_counter import AccurateTokenCounter


class TokenCounterFactory:
    """Factory for creating token counter instances."""
    
    @staticmethod
    def create_simple(
        config: Optional[ConfigurationProtocol] = None,
        limit_profile: LimitProfile = LimitProfile.PRACTICAL
    ) -> SimpleTokenCounter:
        """
        Create a simple token counter instance.
        
        Args:
            config: Configuration provider for model limits
            limit_profile: Limit profile to use
            
        Returns:
            SimpleTokenCounter: Configured simple token counter
        """
        return SimpleTokenCounter(limit_profile=limit_profile, config=config)
    
    @staticmethod
    def create_accurate() -> AccurateTokenCounter:
        """
        Create an accurate token counter instance.
        
        Returns:
            AccurateTokenCounter: Configured accurate token counter
        """
        return AccurateTokenCounter()
    
    @staticmethod
    def create_hybrid(
        mode: str = "simple",
        config: Optional[ConfigurationProtocol] = None,
        limit_profile: LimitProfile = LimitProfile.PRACTICAL
    ) -> TokenCounter:
        """
        Create a hybrid token counter instance.
        
        Args:
            mode: Counting mode ("simple" or "accurate")
            config: Configuration provider for model limits
            limit_profile: Limit profile to use
            
        Returns:
            TokenCounter: Configured hybrid token counter
            
        Raises:
            ValueError: If mode is not supported
        """
        return TokenCounter(
            mode=mode,
            limit_profile=limit_profile,
            config=config
        )
    
    @staticmethod
    def create_from_config(
        config: ConfigurationProtocol,
        mode: str = "simple",
        limit_profile: LimitProfile = LimitProfile.PRACTICAL
    ) -> TokenCounterProtocol:
        """
        Create token counter from configuration.
        
        Args:
            config: Configuration provider
            mode: Counting mode ("simple", "accurate", or "hybrid")
            limit_profile: Limit profile to use
            
        Returns:
            TokenCounterProtocol: Configured token counter
            
        Raises:
            ValueError: If mode is not supported
        """
        if mode == "simple":
            return TokenCounterFactory.create_simple(config, limit_profile)
        elif mode == "accurate":
            return TokenCounterFactory.create_accurate()
        elif mode == "hybrid":
            return TokenCounterFactory.create_hybrid("simple", config, limit_profile)
        else:
            raise ValueError(f"Unsupported mode: {mode}")
