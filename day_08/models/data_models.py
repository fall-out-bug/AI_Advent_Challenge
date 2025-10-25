"""
Data models for token analysis system.

This module contains all dataclasses used throughout the system
for representing token information, model limits, compression results,
and experiment results.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TokenInfo:
    """
    Information about token count and cost estimation.
    
    Attributes:
        count: Number of tokens
        estimated_cost: Estimated cost in dollars (0.0 for local models)
        model_name: Name of the model
    """
    count: int
    estimated_cost: float = 0.0
    model_name: str = ""


@dataclass
class ModelLimits:
    """
    Token limits for a specific model.
    
    Attributes:
        max_input_tokens: Maximum input tokens allowed
        max_output_tokens: Maximum output tokens allowed
        max_total_tokens: Maximum total tokens allowed
        sliding_window: Sliding window size for attention (optional)
        recommended_input: Recommended input token count (optional)
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
    
    Attributes:
        original_text: Original text before compression
        compressed_text: Text after compression
        original_tokens: Number of tokens in original text
        compressed_tokens: Number of tokens in compressed text
        compression_ratio: Ratio of compressed to original tokens
        strategy_used: Name of compression strategy used
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
    
    Attributes:
        experiment_name: Name of the experiment
        model_name: Name of the model used
        original_query: Original query text
        processed_query: Query text after processing (may be compressed)
        response: Model response text
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total tokens used
        response_time: Time taken for response in seconds
        compression_applied: Whether compression was applied
        compression_result: Compression result if applied
        timestamp: When the experiment was run
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
