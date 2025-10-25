"""
Data models for token analysis system.

This module contains all dataclasses used throughout the system
for representing token information, model limits, compression results,
and experiment results.

Example:
    Creating and using data models:
    
    ```python
    from models.data_models import TokenInfo, ModelLimits, CompressionResult, ExperimentResult
    from datetime import datetime
    
    # Create token information
    token_info = TokenInfo(
        count=150,
        estimated_cost=0.001,
        model_name="starcoder"
    )
    print(f"Tokens: {token_info.count}, Cost: ${token_info.estimated_cost}")
    
    # Create model limits
    limits = ModelLimits(
        max_input_tokens=4096,
        max_output_tokens=1024,
        max_total_tokens=6000,
        recommended_input=3500
    )
    print(f"Max input: {limits.max_input_tokens}")
    
    # Create compression result
    compression_result = CompressionResult(
        original_text="Very long text...",
        compressed_text="Compressed text...",
        original_tokens=1000,
        compressed_tokens=200,
        compression_ratio=0.2,
        strategy="truncation"
    )
    print(f"Compression ratio: {compression_result.compression_ratio}")
    
    # Create experiment result
    experiment_result = ExperimentResult(
        experiment_name="compression_test",
        model_name="starcoder",
        original_query="Original query...",
        processed_query="Processed query...",
        response="Model response...",
        compression_result=compression_result,
        timestamp=datetime.now()
    )
    print(f"Experiment: {experiment_result.experiment_name}")
    ```
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TokenInfo:
    """
    Information about token count and cost estimation.
    
    Represents the result of token counting operation with metadata
    about the model used and estimated cost.

    Attributes:
        count (int): Number of tokens in the text
        estimated_cost (float): Estimated cost in dollars (0.0 for local models)
        model_name (str): Name of the model used for counting

    Example:
        ```python
        from models.data_models import TokenInfo
        
        # Create token info for local model
        token_info = TokenInfo(
            count=150,
            estimated_cost=0.0,  # Local models have no cost
            model_name="starcoder"
        )
        
        # Create token info for API model
        api_token_info = TokenInfo(
            count=150,
            estimated_cost=0.001,  # API models have cost
            model_name="gpt-3.5-turbo"
        )
        
        print(f"Tokens: {token_info.count}")
        print(f"Cost: ${token_info.estimated_cost}")
        ```
    """
    count: int
    estimated_cost: float = 0.0
    model_name: str = ""


@dataclass
class ModelLimits:
    """
    Token limits for a specific model.
    
    Defines the maximum token limits for input, output, and total tokens
    for a specific model configuration.

    Attributes:
        max_input_tokens (int): Maximum input tokens allowed
        max_output_tokens (int): Maximum output tokens allowed
        max_total_tokens (int): Maximum total tokens allowed
        sliding_window (Optional[int]): Sliding window size for attention (optional)
        recommended_input (Optional[int]): Recommended input token count (optional)

    Example:
        ```python
        from models.data_models import ModelLimits
        
        # Create limits for StarCoder model
        starcoder_limits = ModelLimits(
            max_input_tokens=8192,  # Theoretical limit
            max_output_tokens=1024,
            max_total_tokens=9216,
            recommended_input=7000  # Safe limit for good performance
        )
        
        # Create practical limits for RTX 3070 Ti
        practical_limits = ModelLimits(
            max_input_tokens=2048,  # Practical limit for 8GB VRAM
            max_output_tokens=512,
            max_total_tokens=2560,
            recommended_input=1500
        )
        
        print(f"Max input: {starcoder_limits.max_input_tokens}")
        print(f"Recommended: {starcoder_limits.recommended_input}")
        ```
    """
    max_input_tokens: int
    max_output_tokens: int
    max_total_tokens: int
    sliding_window: Optional[int] = None
    recommended_input: Optional[int] = None


@dataclass
class CompressionResult:
    """
    Result of text compression operation.
    
    Contains all information about a text compression operation including
    the original and compressed text, token counts, compression ratio,
    and the strategy used.

    Attributes:
        original_text (str): Original text before compression
        compressed_text (str): Text after compression
        original_tokens (int): Number of tokens in original text
        compressed_tokens (int): Number of tokens in compressed text
        compression_ratio (float): Ratio of compressed to original tokens
        strategy_used (str): Name of compression strategy used

    Example:
        ```python
        from models.data_models import CompressionResult
        
        # Create compression result
        result = CompressionResult(
            original_text="This is a very long text that needs compression...",
            compressed_text="This is a compressed text...",
            original_tokens=1000,
            compressed_tokens=200,
            compression_ratio=0.2,
            strategy_used="truncation"
        )
        
        print(f"Original: {result.original_tokens} tokens")
        print(f"Compressed: {result.compressed_tokens} tokens")
        print(f"Ratio: {result.compression_ratio}")
        print(f"Strategy: {result.strategy_used}")
        
        # Check if compression was effective
        if result.compression_ratio < 0.5:
            print("Compression was effective!")
        ```
    """
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str


@dataclass
class ExperimentResult:
    """
    Result of a single experiment.
    
    Contains comprehensive information about an experiment including
    the query, response, token usage, timing, and compression details.

    Attributes:
        experiment_name (str): Name of the experiment
        model_name (str): Name of the model used
        original_query (str): Original query text
        processed_query (str): Query text after processing (may be compressed)
        response (str): Model response text
        input_tokens (int): Number of input tokens
        output_tokens (int): Number of output tokens
        total_tokens (int): Total tokens used
        response_time (float): Time taken for response in seconds
        compression_applied (bool): Whether compression was applied
        compression_result (Optional[CompressionResult]): Compression result if applied
        timestamp (datetime): When the experiment was run

    Example:
        ```python
        from models.data_models import ExperimentResult, CompressionResult
        from datetime import datetime
        
        # Create compression result
        compression = CompressionResult(
            original_text="Long query...",
            compressed_text="Short query...",
            original_tokens=1000,
            compressed_tokens=200,
            compression_ratio=0.2,
            strategy_used="truncation"
        )
        
        # Create experiment result
        result = ExperimentResult(
            experiment_name="compression_test",
            model_name="starcoder",
            original_query="Very long query...",
            processed_query="Compressed query...",
            response="Model response...",
            input_tokens=200,
            output_tokens=50,
            total_tokens=250,
            response_time=1.5,
            compression_applied=True,
            compression_result=compression,
            timestamp=datetime.now()
        )
        
        print(f"Experiment: {result.experiment_name}")
        print(f"Success: {bool(result.response)}")
        print(f"Total tokens: {result.total_tokens}")
        print(f"Response time: {result.response_time}s")
        
        if result.compression_applied:
            print(f"Compression ratio: {result.compression_result.compression_ratio}")
        ```
    """
    experiment_name: str
    model_name: str
    original_query: str
    processed_query: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    compression_applied: bool
    compression_result: Optional[CompressionResult]
    timestamp: datetime
