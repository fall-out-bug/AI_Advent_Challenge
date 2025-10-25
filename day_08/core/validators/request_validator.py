"""
Request validation utilities for ML client.

Provides validation for text, model names, and other parameters
to ensure data integrity before making API calls.

Example:
    Validating requests before API calls:
    
    ```python
    from core.validators.request_validator import RequestValidator
    from core.compressors import CompressionStrategy
    
    # Validate text input
    try:
        RequestValidator.validate_text("Hello world!")
        print("Text is valid")
    except ValueError as e:
        print(f"Invalid text: {e}")
    
    # Validate model name
    try:
        RequestValidator.validate_model_name("starcoder")
        print("Model name is valid")
    except ValueError as e:
        print(f"Invalid model: {e}")
    
    # Validate compression parameters
    try:
        RequestValidator.validate_compression_params(
            text="Long text...",
            max_tokens=100,
            strategy="extractive"
        )
        print("Compression params are valid")
    except ValueError as e:
        print(f"Invalid params: {e}")
    ```
"""

from typing import List, Optional
from core.compressors import CompressionStrategy


class RequestValidator:
    """
    Validator for ML client requests.
    
    Provides static methods for validating various types of input
    parameters before making API calls to the ML service. Ensures
    data integrity and provides clear error messages for invalid inputs.

    Example:
        ```python
        from core.validators.request_validator import RequestValidator
        
        # Validate different types of inputs
        RequestValidator.validate_text("Hello world!")
        RequestValidator.validate_model_name("starcoder")
        RequestValidator.validate_max_tokens(100)
        RequestValidator.validate_compression_strategy("extractive")
        
        # Batch validation
        texts = ["Text 1", "Text 2", "Text 3"]
        RequestValidator.validate_texts_batch(texts)
        ```
    """
    
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
    
    @staticmethod
    def validate_token_count_request(text: str, model_name: str) -> None:
        """
        Validate token count request.
        
        Args:
            text: Text to count tokens for
            model_name: Model name to use
            
        Raises:
            ValueError: If request is invalid
        """
        RequestValidator.validate_text(text)
        RequestValidator.validate_model_name(model_name)
    
    @staticmethod
    def validate_batch_token_count_request(texts: List[str], model_name: str) -> None:
        """
        Validate batch token count request.
        
        Args:
            texts: List of texts to count tokens for
            model_name: Model name to use
            
        Raises:
            ValueError: If request is invalid
        """
        RequestValidator.validate_texts_list(texts)
        RequestValidator.validate_model_name(model_name)
    
    @staticmethod
    def validate_compression_request(text: str, max_tokens: int, model_name: str, strategy: str) -> None:
        """
        Validate compression request.
        
        Args:
            text: Text to compress
            max_tokens: Maximum tokens allowed
            model_name: Model name to use
            strategy: Compression strategy
            
        Raises:
            ValueError: If request is invalid
        """
        RequestValidator.validate_text(text)
        RequestValidator.validate_max_tokens(max_tokens)
        RequestValidator.validate_model_name(model_name)
        
        # For preview requests, strategy validation is bypassed
        if strategy != "preview":
            RequestValidator.validate_strategy(strategy)
