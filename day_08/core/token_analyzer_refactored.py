"""
Refactored Token Analysis System following SOLID principles.

This module separates concerns into focused classes:
- TokenCalculator: Calculates token counts
- LimitChecker: Checks model limits
- ModelConfigProvider: Provides model configuration
- TokenCounterFacade: Coordinates the components
"""

from enum import Enum
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

from core.accurate_token_counter import AccurateTokenCounter
from core.interfaces.protocols import TokenCounterProtocol, ConfigurationProtocol
from models.data_models import ModelLimits, TokenInfo
from utils.logging import LoggerFactory


class LimitProfile(Enum):
    """Limit profile types for model token limits."""
    THEORETICAL = "theoretical"  # Max architecture supports
    PRACTICAL = "practical"  # Real hardware limits


class TokenCalculator(ABC):
    """
    Abstract base class for token calculation.
    
    Single Responsibility: Calculate token counts.
    """
    
    @abstractmethod
    def calculate_tokens(self, text: str) -> int:
        """
        Calculate token count for text.
        
        Args:
            text: Text to analyze
            
        Returns:
            int: Token count
        """
        pass


class SimpleTokenCalculator(TokenCalculator):
    """
    Simple token calculator using word-based estimation.
    
    Single Responsibility: Calculate tokens using simple estimation.
    """
    
    def __init__(self, tokens_per_word: float = 1.3):
        """
        Initialize simple token calculator.
        
        Args:
            tokens_per_word: Tokens per word ratio
        """
        self.tokens_per_word = tokens_per_word
        self.logger = LoggerFactory.create_logger(__name__)
    
    def calculate_tokens(self, text: str) -> int:
        """
        Calculate token count using word-based estimation.
        
        Args:
            text: Text to analyze
            
        Returns:
            int: Estimated token count
        """
        if not text.strip():
            return 0
        
        # Simple word-based estimation
        word_count = len(text.split())
        estimated_tokens = int(word_count * self.tokens_per_word)
        
        self.logger.debug(f"Estimated {estimated_tokens} tokens for {word_count} words")
        return estimated_tokens


class AccurateTokenCalculator(TokenCalculator):
    """
    Accurate token calculator using HuggingFace tokenizers.
    
    Single Responsibility: Calculate tokens using accurate tokenizers.
    """
    
    def __init__(self):
        """Initialize accurate token calculator."""
        self.logger = LoggerFactory.create_logger(__name__)
        self._tokenizer_cache: Dict[str, AccurateTokenCounter] = {}
    
    def calculate_tokens(self, text: str, model_name: str = "starcoder") -> int:
        """
        Calculate accurate token count using model-specific tokenizer.
        
        Args:
            text: Text to analyze
            model_name: Name of the model
            
        Returns:
            int: Accurate token count
        """
        if not text.strip():
            return 0
        
        try:
            # Get or create tokenizer for model
            if model_name not in self._tokenizer_cache:
                self._tokenizer_cache[model_name] = AccurateTokenCounter()
            
            tokenizer = self._tokenizer_cache[model_name]
            token_count = tokenizer.count_tokens(text, model_name)
            
            self.logger.debug(f"Calculated {token_count} tokens for model {model_name}")
            return token_count
            
        except Exception as e:
            self.logger.error(f"Error calculating tokens: {e}")
            # Fallback to simple estimation
            simple_calc = SimpleTokenCalculator()
            return simple_calc.calculate_tokens(text)


class ModelConfigProvider(ABC):
    """
    Abstract base class for model configuration provider.
    
    Single Responsibility: Provide model configuration.
    """
    
    @abstractmethod
    def get_model_limits(self, model_name: str, profile: LimitProfile) -> ModelLimits:
        """
        Get model limits for a specific profile.
        
        Args:
            model_name: Name of the model
            profile: Limit profile
            
        Returns:
            ModelLimits: Model limits
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List[str]: Available model names
        """
        pass


class DefaultModelConfigProvider(ModelConfigProvider):
    """
    Default model configuration provider.
    
    Single Responsibility: Provide default model configuration.
    """
    
    def __init__(self):
        """Initialize default model config provider."""
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Default model limits
        self._model_limits = {
            "starcoder": {
                LimitProfile.THEORETICAL: ModelLimits(
                    model_name="starcoder",
                    max_tokens=8192,
                    context_window=8192,
                    profile="theoretical"
                ),
                LimitProfile.PRACTICAL: ModelLimits(
                    model_name="starcoder",
                    max_tokens=2048,
                    context_window=2048,
                    profile="practical"
                )
            },
            "mistral": {
                LimitProfile.THEORETICAL: ModelLimits(
                    model_name="mistral",
                    max_tokens=4096,
                    context_window=4096,
                    profile="theoretical"
                ),
                LimitProfile.PRACTICAL: ModelLimits(
                    model_name="mistral",
                    max_tokens=1024,
                    context_window=1024,
                    profile="practical"
                )
            },
            "qwen": {
                LimitProfile.THEORETICAL: ModelLimits(
                    model_name="qwen",
                    max_tokens=4096,
                    context_window=4096,
                    profile="theoretical"
                ),
                LimitProfile.PRACTICAL: ModelLimits(
                    model_name="qwen",
                    max_tokens=1024,
                    context_window=1024,
                    profile="practical"
                )
            }
        }
    
    def get_model_limits(self, model_name: str, profile: LimitProfile) -> ModelLimits:
        """
        Get model limits for a specific profile.
        
        Args:
            model_name: Name of the model
            profile: Limit profile
            
        Returns:
            ModelLimits: Model limits
        """
        if model_name not in self._model_limits:
            self.logger.warning(f"Unknown model: {model_name}, using starcoder defaults")
            model_name = "starcoder"
        
        if profile not in self._model_limits[model_name]:
            self.logger.warning(f"Unknown profile: {profile}, using practical")
            profile = LimitProfile.PRACTICAL
        
        return self._model_limits[model_name][profile]
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return list(self._model_limits.keys())


class LimitChecker:
    """
    Checks if text exceeds model limits.
    
    Single Responsibility: Check model limits.
    """
    
    def __init__(self, config_provider: ModelConfigProvider):
        """
        Initialize limit checker.
        
        Args:
            config_provider: Model configuration provider
        """
        self.config_provider = config_provider
        self.logger = LoggerFactory.create_logger(__name__)
    
    def check_limit_exceeded(
        self, 
        text: str, 
        model_name: str, 
        profile: LimitProfile = LimitProfile.PRACTICAL,
        token_calculator: Optional[TokenCalculator] = None
    ) -> bool:
        """
        Check if text exceeds model limits.
        
        Args:
            text: Text to check
            model_name: Name of the model
            profile: Limit profile to use
            token_calculator: Token calculator to use
            
        Returns:
            bool: True if limit exceeded
        """
        if not token_calculator:
            token_calculator = SimpleTokenCalculator()
        
        try:
            # Calculate token count
            if isinstance(token_calculator, AccurateTokenCalculator):
                token_count = token_calculator.calculate_tokens(text, model_name)
            else:
                token_count = token_calculator.calculate_tokens(text)
            
            # Get model limits
            limits = self.config_provider.get_model_limits(model_name, profile)
            
            # Check if exceeded
            exceeded = token_count > limits.max_tokens
            
            self.logger.debug(f"Token count {token_count} vs limit {limits.max_tokens}: {'exceeded' if exceeded else 'ok'}")
            return exceeded
            
        except Exception as e:
            self.logger.error(f"Error checking limits: {e}")
            return False
    
    def get_limit_info(
        self, 
        model_name: str, 
        profile: LimitProfile = LimitProfile.PRACTICAL
    ) -> ModelLimits:
        """
        Get limit information for a model.
        
        Args:
            model_name: Name of the model
            profile: Limit profile to use
            
        Returns:
            ModelLimits: Model limits
        """
        return self.config_provider.get_model_limits(model_name, profile)


class TokenCounterFacade:
    """
    Facade for token counting operations.
    
    Coordinates the separate components while maintaining single responsibility.
    """
    
    def __init__(
        self,
        limit_profile: LimitProfile = LimitProfile.PRACTICAL,
        config_provider: Optional[ModelConfigProvider] = None,
        token_calculator: Optional[TokenCalculator] = None
    ):
        """
        Initialize token counter facade.
        
        Args:
            limit_profile: Limit profile to use
            config_provider: Model configuration provider
            token_calculator: Token calculator to use
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.limit_profile = limit_profile
        
        # Initialize components
        self.config_provider = config_provider or DefaultModelConfigProvider()
        self.token_calculator = token_calculator or SimpleTokenCalculator()
        self.limit_checker = LimitChecker(self.config_provider)
    
    def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """
        Count tokens in text for specified model.
        
        Args:
            text: Text to analyze
            model_name: Name of the model
            
        Returns:
            TokenInfo: Token information
        """
        try:
            # Calculate token count
            if isinstance(self.token_calculator, AccurateTokenCalculator):
                token_count = self.token_calculator.calculate_tokens(text, model_name)
            else:
                token_count = self.token_calculator.calculate_tokens(text)
            
            # Get model limits
            limits = self.config_provider.get_model_limits(model_name, self.limit_profile)
            
            # Check if limit exceeded
            exceeds_limit = token_count > limits.max_tokens
            
            # Calculate compression target
            compression_target = self._estimate_compression_target(text, model_name)
            
            return TokenInfo(
                count=token_count,
                model_name=model_name,
                exceeds_limit=exceeds_limit,
                limit_info=limits,
                compression_target=compression_target
            )
            
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            # Return fallback info
            return TokenInfo(
                count=0,
                model_name=model_name,
                exceeds_limit=False,
                limit_info=self.config_provider.get_model_limits(model_name, self.limit_profile),
                compression_target=0
            )
    
    def check_limit_exceeded(self, text: str, model_name: str) -> bool:
        """
        Check if text exceeds model limits.
        
        Args:
            text: Text to check
            model_name: Name of the model
            
        Returns:
            bool: True if limit exceeded
        """
        return self.limit_checker.check_limit_exceeded(
            text, model_name, self.limit_profile, self.token_calculator
        )
    
    def get_model_limits(self, model_name: str) -> ModelLimits:
        """
        Get limits for specified model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelLimits: Model limits
        """
        return self.config_provider.get_model_limits(model_name, self.limit_profile)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available model names.
        
        Returns:
            List[str]: Available model names
        """
        return self.config_provider.get_available_models()
    
    def estimate_compression_target(
        self, 
        text: str, 
        model_name: str, 
        safety_margin: float = 0.1
    ) -> int:
        """
        Estimate target token count for compression.
        
        Args:
            text: Text to compress
            model_name: Name of the model
            safety_margin: Safety margin (0-1)
            
        Returns:
            int: Target token count
        """
        return self._estimate_compression_target(text, model_name, safety_margin)
    
    def _estimate_compression_target(
        self, 
        text: str, 
        model_name: str, 
        safety_margin: float = 0.1
    ) -> int:
        """Internal method to estimate compression target."""
        try:
            limits = self.config_provider.get_model_limits(model_name, self.limit_profile)
            target_tokens = int(limits.max_tokens * (1 - safety_margin))
            
            self.logger.debug(f"Compression target for {model_name}: {target_tokens} tokens")
            return target_tokens
            
        except Exception as e:
            self.logger.error(f"Error estimating compression target: {e}")
            return 1000  # Fallback value


# Backward compatibility classes
class SimpleTokenCounter(TokenCounterFacade):
    """
    Simple token counter for backward compatibility.
    
    Uses simple token calculation with practical limits.
    """
    
    def __init__(self, limit_profile: LimitProfile = LimitProfile.PRACTICAL):
        """Initialize simple token counter."""
        super().__init__(
            limit_profile=limit_profile,
            token_calculator=SimpleTokenCalculator()
        )


class TokenCounter(TokenCounterFacade):
    """
    Accurate token counter for backward compatibility.
    
    Uses accurate token calculation with specified limit profile.
    """
    
    def __init__(self, mode: str = "accurate", limit_profile: LimitProfile = LimitProfile.PRACTICAL):
        """
        Initialize token counter.
        
        Args:
            mode: Counter mode ("accurate" or "simple")
            limit_profile: Limit profile to use
        """
        if mode == "accurate":
            token_calculator = AccurateTokenCalculator()
        else:
            token_calculator = SimpleTokenCalculator()
        
        super().__init__(
            limit_profile=limit_profile,
            token_calculator=token_calculator
        )
