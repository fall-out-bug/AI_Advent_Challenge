"""
Zen Python Experiments - Refactored following Python Zen principles.

Key improvements:
1. Simple is better than complex - split into smaller, focused classes
2. Single Responsibility Principle - each class has one clear purpose
3. Explicit is better than implicit - clear interfaces and error handling
4. Readability counts - better naming and documentation
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol

from models.data_models import CompressionResult, ExperimentResult


class ModelClient(Protocol):
    """Protocol for model client - explicit interface."""

    async def make_request(self, model_name: str, prompt: str, max_tokens: int) -> dict:
        """Make request to model."""
        ...


class TokenCounter(Protocol):
    """Protocol for token counter - explicit interface."""

    def count_tokens(self, text: str, model_name: str) -> dict:
        """Count tokens in text."""
        ...


class TextCompressor(Protocol):
    """Protocol for text compressor - explicit interface."""

    def compress(
        self, text: str, max_tokens: int, model_name: str, strategy: str
    ) -> CompressionResult:
        """Compress text using specified strategy."""
        ...


class ExperimentError(Exception):
    """Custom exception for experiment errors."""

    pass


@dataclass
class ExperimentConfig:
    """Configuration for experiments - explicit and immutable."""

    model_name: str
    max_retries: int = 3
    timeout_seconds: int = 30
    compression_strategies: List[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_retries < 1:
            raise ExperimentError("max_retries must be >= 1")
        if self.timeout_seconds < 1:
            raise ExperimentError("timeout_seconds must be >= 1")
        if self.compression_strategies is None:
            self.compression_strategies = ["truncation", "keywords"]


class QueryGenerator:
    """
    Generates queries for experiments.

    Following "Single Responsibility Principle" - only generates queries.
    """

    BASE_QUERY = (
        "Детально объясни архитектуру трансформеров в машинном обучении. "
        "Включи в ответ следующую информацию: "
        "1. Механизм внимания (attention mechanism): "
        "- Как работает scaled dot-product attention "
        "- Что такое multi-head attention "
        "- Почему attention лучше RNN/LSTM "
        "2. Архитектура трансформера: "
        "- Encoder-decoder структура "
        "- Positional encoding "
        "- Layer normalization и residual connections "
        "3. Обучение трансформеров: "
        "- Self-supervised learning "
        "- Masked language modeling "
        "- Transfer learning "
        "4. Современные варианты: "
        "- BERT, GPT, T5 архитектуры "
        "- Efficient attention mechanisms "
        "- Scaling laws "
        "Приведи конкретные примеры и формулы где это уместно."
    )

    @classmethod
    def create_long_query(cls, multiplier: int = 20) -> str:
        """
        Create a long query that exceeds token limits.

        Args:
            multiplier: How many times to repeat the base query

        Returns:
            Long query string
        """
        if multiplier < 1:
            raise ExperimentError("Multiplier must be >= 1")

        return cls.BASE_QUERY * multiplier

    @classmethod
    def create_short_query(cls) -> str:
        """
        Create a short query within limits.

        Returns:
            Short query string
        """
        return "Объясни что такое машинное обучение в одном предложении."


class ExperimentRunner:
    """
    Runs individual experiments.

    Following "Single Responsibility Principle" - only runs experiments.
    """

    def __init__(
        self,
        model_client: ModelClient,
        token_counter: TokenCounter,
        text_compressor: TextCompressor,
    ):
        """
        Initialize experiment runner.

        Args:
            model_client: Client for model communication
            token_counter: Token counting utility
            text_compressor: Text compression utility
        """
        self.model_client = model_client
        self.token_counter = token_counter
        self.text_compressor = text_compressor

    async def run_single_experiment(
        self,
        config: ExperimentConfig,
        query: str,
        experiment_name: str,
        compress: bool = False,
        compression_strategy: str = "truncation",
    ) -> ExperimentResult:
        """
        Run a single experiment.

        Args:
            config: Experiment configuration
            query: Query to test
            experiment_name: Name of the experiment
            compress: Whether to compress the query
            compression_strategy: Strategy to use for compression

        Returns:
            ExperimentResult with results

        Raises:
            ExperimentError: If experiment fails
        """
        start_time = time.time()

        try:
            # Count original tokens
            original_tokens = self.token_counter.count_tokens(query, config.model_name)
            model_limits = self.token_counter.get_model_limits(config.model_name)

            # Process query if compression needed
            processed_query = query
            compression_result = None

            if compress and original_tokens.count > model_limits.max_input_tokens:
                compression_result = self.text_compressor.compress(
                    text=query,
                    max_tokens=model_limits.max_input_tokens,
                    model_name=config.model_name,
                    strategy=compression_strategy,
                )
                processed_query = compression_result.compressed_text

            # Make request to model
            response = await self.model_client.make_request(
                model_name=config.model_name,
                prompt=processed_query,
                max_tokens=model_limits.max_output_tokens,
            )

            end_time = time.time()
            response_time = end_time - start_time

            # Count response tokens
            response_tokens = self.token_counter.count_tokens(
                response.get("response", ""), config.model_name
            )

            return ExperimentResult(
                experiment_name=experiment_name,
                model_name=config.model_name,
                original_query=query,
                processed_query=processed_query,
                response=response.get("response", ""),
                original_tokens=original_tokens.count,
                processed_tokens=self.token_counter.count_tokens(
                    processed_query, config.model_name
                ).count,
                response_tokens=response_tokens.count,
                total_tokens=original_tokens.count + response_tokens.count,
                response_time=response_time,
                success=True,
                compression_result=compression_result,
                timestamp=datetime.now(),
            )

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            return ExperimentResult(
                experiment_name=experiment_name,
                model_name=config.model_name,
                original_query=query,
                processed_query=query,
                response="",
                original_tokens=0,
                processed_tokens=0,
                response_tokens=0,
                total_tokens=0,
                response_time=response_time,
                success=False,
                error_message=str(e),
                timestamp=datetime.now(),
            )


class TokenLimitExperiments:
    """
    Main experiments class - orchestrates different experiment types.

    Following "Simple is better than complex" - delegates to specialized classes.
    """

    def __init__(
        self,
        model_client: ModelClient,
        token_counter: TokenCounter,
        text_compressor: TextCompressor,
    ):
        """
        Initialize experiments.

        Args:
            model_client: Client for model communication
            token_counter: Token counting utility
            text_compressor: Text compression utility
        """
        self.model_client = model_client
        self.token_counter = token_counter
        self.text_compressor = text_compressor
        self.runner = ExperimentRunner(model_client, token_counter, text_compressor)

    async def run_limit_exceeded_experiment(
        self, model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with limit-exceeding queries.

        Args:
            model_name: Name of the model to test

        Returns:
            List of experiment results
        """
        config = ExperimentConfig(model_name=model_name)
        long_query = QueryGenerator.create_long_query()

        experiments = [
            ("no_compression", False, "truncation"),
            ("truncation_compression", True, "truncation"),
            ("keyword_compression", True, "keywords"),
        ]

        results = []
        for exp_name, compress, strategy in experiments:
            result = await self.runner.run_single_experiment(
                config=config,
                query=long_query,
                experiment_name=f"limit_exceeded_{exp_name}",
                compress=compress,
                compression_strategy=strategy,
            )
            results.append(result)

        return results

    async def run_short_query_experiment(
        self, model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with short queries.

        Args:
            model_name: Name of the model to test

        Returns:
            List of experiment results
        """
        config = ExperimentConfig(model_name=model_name)
        short_query = QueryGenerator.create_short_query()

        result = await self.runner.run_single_experiment(
            config=config,
            query=short_query,
            experiment_name="short_query",
            compress=False,
        )

        return [result]

    def get_experiment_summary(self, results: List[ExperimentResult]) -> dict:
        """
        Get summary of experiment results.

        Args:
            results: List of experiment results

        Returns:
            Summary dictionary
        """
        if not results:
            return {"total_experiments": 0, "successful": 0, "failed": 0}

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        avg_response_time = sum(r.response_time for r in results) / len(results)
        avg_tokens = sum(r.total_tokens for r in results) / len(results)

        return {
            "total_experiments": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(results),
            "average_response_time": avg_response_time,
            "average_total_tokens": avg_tokens,
        }
