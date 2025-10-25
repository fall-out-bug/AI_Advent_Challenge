"""
Request validation utilities for ML client.

Provides validation for text, model names, and other parameters
to ensure data integrity before making API calls.
"""

from typing import List, Optional
from core.compressors import CompressionStrategy


class RequestValidator:
    """Validator for ML client requests."""
    
    @staticmethod
    def validate_text(text: str, max_length: int = 1000000) -> None:
        """
        Validate text input.
        
        Args:
            text: Text to validate
            max_length: Maximum allowed length
            
        Raises:
            ValueError: If text is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        
        if not text.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        
        if len(text) > max_length:
            raise ValueError(f"Text too long: {len(text)} > {max_length}")
    
    @staticmethod
    def validate_model_name(model_name: str, allowed: Optional[List[str]] = None) -> None:
        """
        Validate model name.
        
        Args:
            model_name: Model name to validate
            allowed: List of allowed model names (optional)
            
        Raises:
            ValueError: If model name is invalid
        """
        if not isinstance(model_name, str):
            raise ValueError("Model name must be a string")
        
        if not model_name.strip():
            raise ValueError("Model name cannot be empty")
        
        if allowed and model_name not in allowed:
            raise ValueError(f"Model '{model_name}' not in allowed list: {allowed}")
    
    @staticmethod
    def validate_strategy(strategy: str) -> CompressionStrategy:
        """
        Validate compression strategy.
        
        Args:
            strategy: Strategy name to validate
            
        Returns:
            CompressionStrategy: Validated strategy enum
            
        Raises:
            ValueError: If strategy is invalid
        """
        try:
            return CompressionStrategy(strategy)
        except ValueError:
            available = [s.value for s in CompressionStrategy]
            raise ValueError(f"Invalid strategy '{strategy}'. Available: {available}")
    
    @staticmethod
    def validate_max_tokens(max_tokens: int, min_tokens: int = 1) -> None:
        """
        Validate max tokens parameter.
        
        Args:
            max_tokens: Maximum tokens to validate
            min_tokens: Minimum allowed tokens
            
        Raises:
            ValueError: If max_tokens is invalid
        """
        if not isinstance(max_tokens, int):
            raise ValueError("Max tokens must be an integer")
        
        if max_tokens < min_tokens:
            raise ValueError(f"Max tokens must be >= {min_tokens}, got {max_tokens}")
    
    @staticmethod
    def validate_texts_list(texts: List[str], max_count: int = 100) -> None:
        """
        Validate list of texts for batch operations.
        
        Args:
            texts: List of texts to validate
            max_count: Maximum number of texts allowed
            
        Raises:
            ValueError: If texts list is invalid
        """
        if not isinstance(texts, list):
            raise ValueError("Texts must be a list")
        
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if len(texts) > max_count:
            raise ValueError(f"Too many texts: {len(texts)} > {max_count}")
        
        for i, text in enumerate(texts):
            try:
                RequestValidator.validate_text(text)
            except ValueError as e:
                raise ValueError(f"Invalid text at index {i}: {e}")
