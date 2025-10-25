"""
Experiment data models for intermediate processing.

Provides dataclasses for structuring experiment data
and intermediate processing steps.
"""

from dataclasses import dataclass
from typing import Optional
from models.data_models import CompressionResult


@dataclass
class QueryInfo:
    """
    Information about query processing.
    
    Attributes:
        original_text: Original query text
        processed_text: Processed query text (after compression if applied)
        original_tokens: Token count of original text
        processed_tokens: Token count of processed text
        compression_applied: Whether compression was applied
        compression_result: Compression result if applied
    """
    original_text: str
    processed_text: str
    original_tokens: int
    processed_tokens: int
    compression_applied: bool
    compression_result: Optional[CompressionResult] = None


@dataclass
class ResponseInfo:
    """
    Information about model response.
    
    Attributes:
        text: Response text from model
        tokens: Number of tokens in response
        duration: Response duration in seconds
        success: Whether request was successful
        error: Error message if request failed
    """
    text: str
    tokens: int
    duration: float
    success: bool
    error: Optional[str] = None


@dataclass
class ExperimentContext:
    """
    Context for experiment execution.
    
    Attributes:
        model_name: Name of the model to test
        query: Query text to process
        experiment_name: Name of the experiment
        compress: Whether to apply compression
        compression_strategy: Strategy to use for compression
    """
    model_name: str
    query: str
    experiment_name: str
    compress: bool = False
    compression_strategy: str = "truncation"


@dataclass
class ExperimentMetrics:
    """
    Metrics for experiment analysis.
    
    Attributes:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total tokens used
        response_time: Response time in seconds
        compression_ratio: Compression ratio if applied
    """
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    compression_ratio: Optional[float] = None
