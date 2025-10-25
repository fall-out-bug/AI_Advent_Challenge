"""
Experiment data models for intermediate processing.

Provides dataclasses for structuring experiment data
and intermediate processing steps.

Example:
    Using experiment models for structured data handling:
    
    ```python
    from models.experiment_models import QueryInfo, ResponseInfo, ExperimentContext, ExperimentMetrics
    from models.data_models import CompressionResult
    
    # Create query information
    query_info = QueryInfo(
        original_text="Very long query...",
        processed_text="Compressed query...",
        original_tokens=1000,
        processed_tokens=200,
        compression_applied=True,
        compression_result=compression_result
    )
    
    # Create response information
    response_info = ResponseInfo(
        response_text="Model response...",
        tokens_used=50,
        response_time=1.5,
        success=True
    )
    
    # Create experiment context
    context = ExperimentContext(
        model_name="starcoder",
        query_info=query_info,
        max_tokens=1000
    )
    
    # Create experiment metrics
    metrics = ExperimentMetrics(
        total_tokens=250,
        compression_ratio=0.2,
        response_time=1.5,
        success=True
    )
    ```
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
