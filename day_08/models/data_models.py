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
from datetime import datetime
from typing import Optional, List, Dict, Any


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
class ModelResponse:
    """
    Response from a model inference request.
    
    Contains the model's response text, token usage, and timing information.
    
    Attributes:
        response (str): Model response text
        total_tokens (int): Total tokens used (input + output)
        response_time (float): Time taken for response in seconds
        model_name (str): Name of the model that generated the response
        
    Example:
        ```python
        from models.data_models import ModelResponse
        
        # Create model response
        response = ModelResponse(
            response="Here's a simple function...",
            total_tokens=150,
            response_time=1.5,
            model_name="starcoder"
        )
        
        print(f"Response: {response.response}")
        print(f"Tokens: {response.total_tokens}")
        print(f"Time: {response.response_time:.2f}s")
        ```
    """
    
    response: str
    total_tokens: int
    response_time: float
    model_name: str


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


@dataclass
class ModelWorkflowResult:
    """
    Result of a complete workflow execution with a model.
    
    Contains comprehensive information about workflow execution including
    task results, statistics, and performance metrics.
    
    Attributes:
        model_name (str): Name of the model used
        tasks_executed (int): Total number of tasks executed
        successful_tasks (int): Number of successfully completed tasks
        failed_tasks (int): Number of failed tasks
        total_time (float): Total workflow execution time in seconds
        task_results (List[Dict[str, Any]]): Results of individual tasks
        model_statistics (Dict[str, Any]): Model-specific statistics
        error_message (Optional[str]): Error message if workflow failed
        timestamp (datetime): When the workflow was executed
        
    Example:
        ```python
        from models.data_models import ModelWorkflowResult
        from datetime import datetime
        
        # Create workflow result
        result = ModelWorkflowResult(
            model_name="starcoder",
            tasks_executed=5,
            successful_tasks=4,
            failed_tasks=1,
            total_time=12.5,
            task_results=[{"success": True, "response": "..."}],
            model_statistics={"total_requests": 5, "successful_requests": 4},
            timestamp=datetime.now()
        )
        
        print(f"Success rate: {result.success_rate:.2%}")
        print(f"Average task time: {result.average_task_time:.2f}s")
        ```
    """
    
    model_name: str
    tasks_executed: int
    successful_tasks: int
    failed_tasks: int
    total_time: float
    task_results: List[Dict[str, Any]]
    model_statistics: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Success rate of the workflow."""
        if self.tasks_executed == 0:
            return 0.0
        return self.successful_tasks / self.tasks_executed
    
    @property
    def average_task_time(self) -> float:
        """Average time per task."""
        if self.tasks_executed == 0:
            return 0.0
        return self.total_time / self.tasks_executed


@dataclass
class ThreeStageResult:
    """
    Result of three-stage token limit testing.
    
    Contains information about queries at three different complexity levels
    and their token usage relative to model limits.
    
    Attributes:
        model_name (str): Name of the model tested
        short_query (str): Short complexity query
        medium_query (str): Medium complexity query
        long_query (str): Long complexity query
        short_query_tokens (int): Token count for short query
        medium_query_tokens (int): Token count for medium query
        long_query_tokens (int): Token count for long query
        model_limits (ModelLimits): Model token limits
        short_exceeds_limit (bool): Whether short query exceeds limit
        medium_exceeds_limit (bool): Whether medium query exceeds limit
        long_exceeds_limit (bool): Whether long query exceeds limit
        success (bool): Whether the test completed successfully
        error_message (Optional[str]): Error message if test failed
        timestamp (datetime): When the test was run
        
    Example:
        ```python
        from models.data_models import ThreeStageResult
        from datetime import datetime
        
        # Create three-stage result
        result = ThreeStageResult(
            model_name="starcoder",
            short_query="Write a simple function",
            medium_query="Implement a class with methods",
            long_query="Build a complete application",
            short_query_tokens=50,
            medium_query_tokens=300,
            long_query_tokens=1500,
            model_limits=ModelLimits(max_input_tokens=8192, ...),
            short_exceeds_limit=False,
            medium_exceeds_limit=False,
            long_exceeds_limit=False,
            success=True,
            timestamp=datetime.now()
        )
        
        print(f"Long query exceeds limit: {result.long_exceeds_limit}")
        print(f"Test success: {result.success}")
        ```
    """
    
    model_name: str
    short_query: str
    medium_query: str
    long_query: str
    short_query_tokens: int
    medium_query_tokens: int
    long_query_tokens: int
    model_limits: ModelLimits
    short_exceeds_limit: bool
    medium_exceeds_limit: bool
    long_exceeds_limit: bool
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    @property
    def total_queries_tested(self) -> int:
        """Total number of queries tested."""
        return 3
    
    @property
    def queries_exceeding_limit(self) -> int:
        """Number of queries that exceed the model limit."""
        count = 0
        if self.short_exceeds_limit:
            count += 1
        if self.medium_exceeds_limit:
            count += 1
        if self.long_exceeds_limit:
            count += 1
        return count
    
    @property
    def compression_needed(self) -> bool:
        """Whether compression is needed for any query."""
        return self.queries_exceeding_limit > 0


@dataclass
class CompressionTestResult:
    """
    Result of testing a single compression strategy.
    
    Contains comprehensive information about compression testing including
    the compression results, model response, and performance metrics.
    
    Attributes:
        strategy (str): Name of the compression strategy used
        original_query (str): Original query text
        compressed_query (str): Compressed query text
        original_tokens (int): Token count in original query
        compressed_tokens (int): Token count in compressed query
        compression_ratio (float): Ratio of compressed to original tokens
        response (str): Model response text
        response_tokens (int): Token count in response
        response_time (float): Time taken for response in seconds
        success (bool): Whether the test was successful
        error_message (Optional[str]): Error message if test failed
        timestamp (datetime): When the test was run
        
    Example:
        ```python
        from models.data_models import CompressionTestResult
        from datetime import datetime
        
        # Create compression test result
        result = CompressionTestResult(
            strategy="truncation",
            original_query="Very long query...",
            compressed_query="Short query...",
            original_tokens=1500,
            compressed_tokens=300,
            compression_ratio=0.2,
            response="Model response...",
            response_tokens=200,
            response_time=2.5,
            success=True,
            timestamp=datetime.now()
        )
        
        print(f"Compression ratio: {result.compression_ratio:.2f}")
        print(f"Response time: {result.response_time:.2f}s")
        ```
    """
    
    strategy: str
    original_query: str
    compressed_query: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    response: str
    response_tokens: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    @property
    def total_tokens_used(self) -> int:
        """Total tokens used (compressed input + response)."""
        return self.compressed_tokens + self.response_tokens
    
    @property
    def tokens_saved(self) -> int:
        """Number of tokens saved through compression."""
        return self.original_tokens - self.compressed_tokens
    
    @property
    def compression_efficiency(self) -> float:
        """Efficiency of compression (tokens saved / original tokens)."""
        if self.original_tokens == 0:
            return 0.0
        return self.tokens_saved / self.original_tokens


@dataclass
class QualityMetrics:
    """
    Quality metrics for compression and response evaluation.
    
    Contains various quality scores and metrics for evaluating
    the effectiveness of compression and response quality.
    
    Attributes:
        compression_ratio (float): Ratio of compressed to original text length
        completeness_score (float): Score for completeness preservation (0-1)
        relevance_score (float): Score for response relevance (0-1)
        semantic_score (float): Score for semantic preservation (0-1)
        overall_score (float): Overall quality score (0-1)
        response_length (int): Length of the response text
        information_preservation (float): Information preservation score (0-1)
        
    Example:
        ```python
        from models.data_models import QualityMetrics
        
        # Create quality metrics
        metrics = QualityMetrics(
            compression_ratio=0.3,
            completeness_score=0.8,
            relevance_score=0.9,
            semantic_score=0.7,
            overall_score=0.8,
            response_length=500,
            information_preservation=0.75
        )
        
        print(f"Overall quality: {metrics.overall_score:.2f}")
        print(f"Completeness: {metrics.completeness_score:.2f}")
        ```
    """
    
    compression_ratio: float
    completeness_score: float
    relevance_score: float
    semantic_score: float
    overall_score: float
    response_length: int
    information_preservation: float
    
    @property
    def is_high_quality(self) -> bool:
        """Whether the quality is considered high (overall score > 0.7)."""
        return self.overall_score > 0.7
    
    @property
    def is_acceptable_quality(self) -> bool:
        """Whether the quality is acceptable (overall score > 0.5)."""
        return self.overall_score > 0.5


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for experiment evaluation.
    
    Contains comprehensive performance information including timing,
    token usage, and efficiency metrics.
    
    Attributes:
        response_time (float): Time taken for response in seconds
        total_tokens (int): Total tokens used
        input_tokens (int): Input tokens used
        output_tokens (int): Output tokens generated
        tokens_per_second (float): Tokens processed per second
        performance_rating (str): Performance rating (excellent/good/acceptable/poor)
        efficiency_score (float): Efficiency score (0-1)
        compression_beneficial (bool): Whether compression was beneficial
        compression_ratio (float): Compression ratio applied
        success (bool): Whether the operation was successful
        
    Example:
        ```python
        from models.data_models import PerformanceMetrics
        
        # Create performance metrics
        metrics = PerformanceMetrics(
            response_time=2.5,
            total_tokens=500,
            input_tokens=300,
            output_tokens=200,
            tokens_per_second=200.0,
            performance_rating="good",
            efficiency_score=0.8,
            compression_beneficial=True,
            compression_ratio=0.3,
            success=True
        )
        
        print(f"Performance: {metrics.performance_rating}")
        print(f"Efficiency: {metrics.efficiency_score:.2f}")
        ```
    """
    
    response_time: float
    total_tokens: int
    input_tokens: int
    output_tokens: int
    tokens_per_second: float
    performance_rating: str
    efficiency_score: float
    compression_beneficial: bool
    compression_ratio: float
    success: bool
    
    @property
    def is_fast(self) -> bool:
        """Whether the response was fast (< 2 seconds)."""
        return self.response_time < 2.0
    
    @property
    def is_efficient(self) -> bool:
        """Whether the operation was efficient (score > 0.7)."""
        return self.efficiency_score > 0.7


@dataclass
class CodeQualityMetrics:
    """
    Code quality metrics for generated code evaluation.
    
    Contains comprehensive code quality assessment including
    PEP8 compliance, documentation, and complexity metrics.
    
    Attributes:
        code_quality_score (float): Overall code quality score (0-10)
        pep8_compliance (bool): Whether code follows PEP8
        pep8_score (float): PEP8 compliance score (0-10)
        has_docstrings (bool): Whether code has docstrings
        has_type_hints (bool): Whether code has type hints
        test_coverage (str): Test coverage level (none/basic/good)
        complexity_score (float): Code complexity score (0-10)
        requirements_coverage (float): Requirements coverage (0-1)
        completeness_score (float): Code completeness score (0-1)
        code_length (int): Length of generated code
        function_count (int): Number of functions in code
        class_count (int): Number of classes in code
        
    Example:
        ```python
        from models.data_models import CodeQualityMetrics
        
        # Create code quality metrics
        metrics = CodeQualityMetrics(
            code_quality_score=8.5,
            pep8_compliance=True,
            pep8_score=8.0,
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="good",
            complexity_score=3.0,
            requirements_coverage=0.9,
            completeness_score=0.85,
            code_length=500,
            function_count=3,
            class_count=1
        )
        
        print(f"Quality score: {metrics.code_quality_score:.2f}")
        print(f"PEP8 compliant: {metrics.pep8_compliance}")
        ```
    """
    
    code_quality_score: float
    pep8_compliance: bool
    pep8_score: float
    has_docstrings: bool
    has_type_hints: bool
    test_coverage: str
    complexity_score: float
    requirements_coverage: float
    completeness_score: float
    code_length: int
    function_count: int
    class_count: int
    
    @property
    def is_high_quality(self) -> bool:
        """Whether code is high quality (score > 8.0)."""
        return self.code_quality_score > 8.0
    
    @property
    def is_acceptable_quality(self) -> bool:
        """Whether code quality is acceptable (score > 6.0)."""
        return self.code_quality_score > 6.0
    
    @property
    def has_good_practices(self) -> bool:
        """Whether code follows good practices."""
        return (self.pep8_compliance and self.has_docstrings and 
                self.has_type_hints and self.complexity_score < 5.0)


@dataclass
class CompletenessScore:
    """
    Completeness score for response evaluation.
    
    Contains assessment of how completely the response addresses
    the original query requirements.
    
    Attributes:
        completeness_score (float): Overall completeness score (0-1)
        requirements_met (List[str]): List of requirements that were met
        missing_elements (List[str]): List of missing requirements
        has_code (bool): Whether response contains code
        has_examples (bool): Whether response contains examples
        has_documentation (bool): Whether response contains documentation
        response_length (int): Length of response text
        query_length (int): Length of original query
        coverage_ratio (float): Ratio of response to query length
        
    Example:
        ```python
        from models.data_models import CompletenessScore
        
        # Create completeness score
        score = CompletenessScore(
            completeness_score=0.85,
            requirements_met=["function", "class", "documentation"],
            missing_elements=["tests"],
            has_code=True,
            has_examples=True,
            has_documentation=True,
            response_length=800,
            query_length=200,
            coverage_ratio=4.0
        )
        
        print(f"Completeness: {score.completeness_score:.2f}")
        print(f"Requirements met: {len(score.requirements_met)}")
        ```
    """
    
    completeness_score: float
    requirements_met: List[str]
    missing_elements: List[str]
    has_code: bool
    has_examples: bool
    has_documentation: bool
    response_length: int
    query_length: int
    coverage_ratio: float
    
    @property
    def is_complete(self) -> bool:
        """Whether response is complete (score > 0.8)."""
        return self.completeness_score > 0.8
    
    @property
    def is_acceptable(self) -> bool:
        """Whether response is acceptable (score > 0.6)."""
        return self.completeness_score > 0.6
    
    @property
    def has_all_elements(self) -> bool:
        """Whether response has all expected elements."""
        return self.has_code and self.has_examples and self.has_documentation
