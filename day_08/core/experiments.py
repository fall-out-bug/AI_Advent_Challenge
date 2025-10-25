"""
Experiments module for testing token limits and compression strategies.

This module provides experiments to demonstrate how models behave
with different token counts, including limit-exceeding queries
and various compression strategies.
"""

import time
from datetime import datetime
from typing import List, Optional

from models.data_models import CompressionResult, ExperimentResult
from models.experiment_models import QueryInfo, ResponseInfo, ExperimentContext, ExperimentMetrics
from core.builders import ExperimentResultBuilder
from utils.logging import LoggerFactory


class TokenLimitExperiments:
    """
    Experiments to test token limits and compression strategies.

    Provides methods to run experiments with different query lengths
    and compression strategies to demonstrate model behavior.
    """

    def __init__(self, model_client, token_counter, text_compressor):
        """
        Initialize experiments with required components.

        Args:
            model_client: Instance of UnifiedModelClient
            token_counter: Instance of SimpleTokenCounter
            text_compressor: Instance of SimpleTextCompressor
        """
        self.model_client = model_client
        self.token_counter = token_counter
        self.text_compressor = text_compressor
        self.logger = LoggerFactory.create_logger(__name__)

    def _create_long_query(self) -> str:
        """
        Create a very long query that exceeds StarCoder's token limit.

        Returns:
            str: Long technical query about transformers architecture
        """
        base_query = """
        Детально объясни архитектуру трансформеров в машинном обучении. 
        Включи в ответ следующую информацию:
        
        1. Механизм внимания (attention mechanism):
        - Как работает scaled dot-product attention
        - Формула вычисления attention weights
        - Почему используется масштабирование
        - Примеры применения в разных задачах
        
        2. Multi-head attention:
        - Зачем нужны несколько голов внимания
        - Как происходит объединение результатов
        - Преимущества перед single-head attention
        - Оптимальное количество голов
        
        3. Positional encoding:
        - Как модель понимает порядок слов
        - Sinusoidal и learned positional encoding
        - Проблемы с длинными последовательностями
        - Современные подходы к позиционному кодированию
        
        4. Feed-forward networks:
        - Структура и назначение FFN слоев
        - Размеры скрытых слоев
        - Функции активации
        - Оптимизация параметров
        
        5. Layer normalization:
        - Нормализация и её роль в обучении
        - Pre-norm vs Post-norm архитектуры
        - Влияние на стабильность обучения
        - Сравнение с batch normalization
        
        6. Residual connections:
        - Зачем нужны skip connections
        - Решение проблемы vanishing gradients
        - Архитектурные варианты residual connections
        - Влияние на глубину сети
        
        7. Практические применения:
        - Где используются трансформеры
        - Примеры успешных моделей (BERT, GPT, T5)
        - Области применения (NLP, Computer Vision, etc.)
        - Ограничения и недостатки
        
        8. Примеры кода на Python:
        - Реализация attention mechanism с нуля
        - Multi-head attention на PyTorch
        - Полная архитектура трансформера
        - Обучение и инференс
        
        9. Оптимизации:
        - Как ускорить работу трансформеров
        - Квантизация и сжатие моделей
        - Эффективные attention механизмы
        - Hardware оптимизации
        
        10. Современные варианты:
        - BERT и его особенности
        - GPT серия моделей
        - T5 и text-to-text подход
        - Vision Transformers (ViT)
        - Efficient Transformers
        
        Пожалуйста, дай максимально подробный и технический ответ с примерами кода и математическими формулами.
        """

        # Repeat query 20 times to create a very long query
        repeated_query = base_query * 20

        return repeated_query.strip()

    async def run_limit_exceeded_experiment(
        self, model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with limit-exceeding queries and compression strategies.

        Args:
            model_name: Name of the model to test

        Returns:
            List[ExperimentResult]: Results of all experiments
        """
        context = self._prepare_experiment_context(model_name)
        
        no_comp_result = await self._run_no_compression_test(context)
        trunc_result = await self._run_truncation_test(context)
        keywords_result = await self._run_keywords_test(context)
        
        return self._collect_results([no_comp_result, trunc_result, keywords_result])

    def _prepare_experiment_context(self, model_name: str) -> ExperimentContext:
        """Prepare experiment context with long query."""
        long_query = self._create_long_query()
        
        self.logger.info("experiment_prepared", 
                        model=model_name, 
                        query_length=len(long_query))
        
        return ExperimentContext(
            model_name=model_name,
            query=long_query,
            experiment_name="limit_exceeded",
            compress=False
        )

    async def _run_no_compression_test(self, context: ExperimentContext) -> ExperimentResult:
        """Run experiment without compression."""
        self.logger.info("experiment_started", 
                        experiment="no_compression", 
                        model=context.model_name)
        
        try:
            result = await self._run_single_experiment(
                model_name=context.model_name,
                query=context.query,
                experiment_name="no_compression",
                compress=False,
            )
            self.logger.info("experiment_completed", experiment="no_compression")
            return result
        except Exception as e:
            self.logger.error("experiment_failed", 
                            experiment="no_compression", 
                            error=str(e))
            raise

    async def _run_truncation_test(self, context: ExperimentContext) -> ExperimentResult:
        """Run experiment with truncation compression."""
        self.logger.info("experiment_started", 
                        experiment="truncation_compression", 
                        model=context.model_name)
        
        try:
            result = await self._run_single_experiment(
                model_name=context.model_name,
                query=context.query,
                experiment_name="truncation_compression",
                compress=True,
                compression_strategy="truncation",
            )
            self.logger.info("experiment_completed", experiment="truncation_compression")
            return result
        except Exception as e:
            self.logger.error("experiment_failed", 
                            experiment="truncation_compression", 
                            error=str(e))
            raise

    async def _run_keywords_test(self, context: ExperimentContext) -> ExperimentResult:
        """Run experiment with keywords compression."""
        self.logger.info("experiment_started", 
                        experiment="keywords_compression", 
                        model=context.model_name)
        
        try:
            result = await self._run_single_experiment(
                model_name=context.model_name,
                query=context.query,
                experiment_name="keywords_compression",
                compress=True,
                compression_strategy="keywords",
            )
            self.logger.info("experiment_completed", experiment="keywords_compression")
            return result
        except Exception as e:
            self.logger.error("experiment_failed", 
                            experiment="keywords_compression", 
                            error=str(e))
            raise

    def _collect_results(self, results: List[ExperimentResult]) -> List[ExperimentResult]:
        """Collect and validate experiment results."""
        valid_results = [r for r in results if r is not None]
        
        self.logger.info("experiments_summary", 
                        total_experiments=len(results),
                        successful_experiments=len(valid_results))
        
        return valid_results

    async def run_model_comparison_experiment(
        self, models: List[str], query: str, auto_swap: bool = True
    ) -> List[ExperimentResult]:
        """
        Compare multiple models with automatic container management.

        Args:
            models: List of model names to compare
            query: Query to test with all models
            auto_swap: Whether to automatically manage containers

        Returns:
            List[ExperimentResult]: Results from all models
        """
        results = []

        if auto_swap:
            try:
                from utils.docker_manager import ModelDockerManager

                docker_manager = ModelDockerManager()
            except ImportError:
                self.logger.warning("docker_manager_unavailable")
                auto_swap = False

        for i, model in enumerate(models):
            self.logger.info("model_testing", 
                            model=model, 
                            index=i+1, 
                            total=len(models))

            if auto_swap and i > 0:
                # Stop previous, start current
                previous_model = models[i - 1]
                await docker_manager.swap_models(previous_model, model)

                # Verify availability
                is_ready = await self.model_client.check_availability(model)
                if not is_ready:
                    self.logger.error("model_startup_failed", model=model)
                    continue

            # Run experiment
            try:
                result = await self._run_single_experiment(
                    model_name=model,
                    query=query,
                    experiment_name=f"{model}_comparison",
                    compress=False,  # No compression for comparison
                )
                results.append(result)
                self.logger.info("model_test_completed", model=model)
            except Exception as e:
                self.logger.error("model_test_failed", model=model, error=str(e))

        return results

    async def run_advanced_compression_experiment(
        self, model_name: str = "starcoder", strategies: List[str] = None
    ) -> List[ExperimentResult]:
        """
        Run experiments with advanced compression strategies.

        Args:
            model_name: Model to test with
            strategies: List of compression strategies to test

        Returns:
            List[ExperimentResult]: Results from all strategies
        """
        if strategies is None:
            strategies = ["truncation", "keywords", "extractive", "semantic"]

        # Create long query
        long_query = self._create_long_query()

        # Check if we need advanced compressor
        if any(s in ["extractive", "semantic", "summarization"] for s in strategies):
            try:
                from core.text_compressor import AdvancedTextCompressor

                if not isinstance(self.text_compressor, AdvancedTextCompressor):
                    self.text_compressor = AdvancedTextCompressor(
                        self.token_counter, self.model_client
                    )
            except ImportError:
                self.logger.warning("advanced_compressor_unavailable")
                strategies = [s for s in strategies if s in ["truncation", "keywords"]]

        results = []

        for strategy in strategies:
            self.logger.info("strategy_testing", strategy=strategy)

            try:
                result = await self._run_single_experiment(
                    model_name=model_name,
                    query=long_query,
                    experiment_name=f"{strategy}_compression",
                    compress=True,
                    compression_strategy=strategy,
                )
                results.append(result)
                self.logger.info("strategy_completed", strategy=strategy)
            except Exception as e:
                self.logger.error("strategy_failed", strategy=strategy, error=str(e))

        return results

    async def _run_single_experiment(
        self,
        model_name: str,
        query: str,
        experiment_name: str,
        compress: bool = False,
        compression_strategy: str = "truncation",
    ) -> ExperimentResult:
        """
        Run a single experiment.

        Args:
            model_name: Name of the model
            query: Query text
            experiment_name: Name of the experiment
            compress: Whether to apply compression
            compression_strategy: Strategy to use for compression

        Returns:
            ExperimentResult: Result of the experiment
        """
        start_time = time.time()
        
        query_info = self._prepare_query(model_name, query, compress, compression_strategy)
        response_info = await self._execute_model_request(model_name, query_info)
        
        return self._build_experiment_result(
            experiment_name, model_name, query_info, response_info, start_time
        )

    def _prepare_query(
        self, 
        model_name: str, 
        query: str, 
        compress: bool, 
        compression_strategy: str
    ) -> QueryInfo:
        """Prepare query with optional compression."""
        original_tokens = self._count_query_tokens(query, model_name)
        
        if self._should_compress(compress, original_tokens, model_name):
            return self._compress_query(query, model_name, compression_strategy, original_tokens)
        
        return self._no_compression_query_info(query, original_tokens)

    def _count_query_tokens(self, query: str, model_name: str) -> int:
        """Count tokens in query."""
        return self.token_counter.count_tokens(query, model_name).count

    def _should_compress(self, compress: bool, original_tokens: int, model_name: str) -> bool:
        """Check if compression should be applied."""
        if not compress:
            return False
        
        model_limits = self.token_counter.get_model_limits(model_name)
        return original_tokens > model_limits.max_input_tokens

    def _compress_query(
        self, 
        query: str, 
        model_name: str, 
        compression_strategy: str, 
        original_tokens: int
    ) -> QueryInfo:
        """Compress query using specified strategy."""
        model_limits = self.token_counter.get_model_limits(model_name)
        
        compression_result = self.text_compressor.compress_text(
            text=query,
            max_tokens=model_limits.max_input_tokens,
            model_name=model_name,
            strategy=compression_strategy,
        )
        
        processed_tokens = self._count_query_tokens(compression_result.compressed_text, model_name)
        
        return QueryInfo(
            original_text=query,
            processed_text=compression_result.compressed_text,
            original_tokens=original_tokens,
            processed_tokens=processed_tokens,
            compression_applied=True,
            compression_result=compression_result
        )

    def _no_compression_query_info(self, query: str, original_tokens: int) -> QueryInfo:
        """Create QueryInfo without compression."""
        return QueryInfo(
            original_text=query,
            processed_text=query,
            original_tokens=original_tokens,
            processed_tokens=original_tokens,
            compression_applied=False,
            compression_result=None
        )

    async def _execute_model_request(
        self, 
        model_name: str, 
        query_info: QueryInfo
    ) -> ResponseInfo:
        """Execute model request and return response info."""
        try:
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=query_info.processed_text,
                max_tokens=1000,
                temperature=0.7,
            )
            
            output_tokens = self._count_query_tokens(response.response, model_name)
            
            return ResponseInfo(
                text=response.response,
                tokens=output_tokens,
                duration=0.0,  # Will be set by caller
                success=True,
                error=None
            )
        except Exception as e:
            return ResponseInfo(
                text="",
                tokens=0,
                duration=0.0,
                success=False,
                error=str(e)
            )

    def _build_experiment_result(
        self,
        experiment_name: str,
        model_name: str,
        query_info: QueryInfo,
        response_info: ResponseInfo,
        start_time: float
    ) -> ExperimentResult:
        """Build ExperimentResult using builder pattern."""
        end_time = time.time()
        response_time = end_time - start_time
        
        # Update response info with actual duration
        response_info.duration = response_time
        
        builder = ExperimentResultBuilder()
        
        return (builder
                .with_experiment_name(experiment_name)
                .with_model(model_name)
                .with_query(query_info.original_text, query_info.processed_text)
                .with_response(response_info.text)
                .with_tokens(query_info.processed_tokens, response_info.tokens, 
                           query_info.processed_tokens + response_info.tokens)
                .with_timing(response_time)
                .with_compression(query_info.compression_applied, query_info.compression_result)
                .with_timestamp()
                .build())

    async def run_short_query_experiment(
        self, model_name: str = "starcoder"
    ) -> List[ExperimentResult]:
        """
        Run experiments with short queries for comparison.

        Args:
            model_name: Name of the model to test

        Returns:
            List[ExperimentResult]: Results of short query experiments
        """
        short_queries = [
            "Что такое машинное обучение?",
            "Объясни принцип работы нейронных сетей",
            "Как работает алгоритм градиентного спуска?",
            "Что такое overfitting в ML?",
            "Объясни разницу между supervised и unsupervised learning",
        ]

        results = []

        self.logger.info("short_query_experiment_started", 
                        model=model_name, 
                        query_count=len(short_queries))

        for i, query in enumerate(short_queries, 1):
            self.logger.info("short_query_testing", 
                            query_index=i, 
                            query_preview=query[:50])

            try:
                result = await self._run_single_experiment(
                    model_name=model_name,
                    query=query,
                    experiment_name=f"short_query_{i}",
                    compress=False,
                )
                results.append(result)
                self.logger.info("short_query_completed", query_index=i)
            except Exception as e:
                self.logger.error("short_query_failed", 
                                query_index=i, 
                                error=str(e))

        return results

    def get_experiment_summary(self, results: List[ExperimentResult]) -> dict:
        """
        Get summary statistics for experiment results.

        Args:
            results: List of experiment results

        Returns:
            dict: Summary statistics
        """
        if not results:
            return {}

        total_experiments = len(results)
        successful_experiments = len([r for r in results if r.response])
        compression_experiments = len([r for r in results if r.compression_applied])

        avg_response_time = sum(r.response_time for r in results) / total_experiments
        avg_input_tokens = sum(r.input_tokens for r in results) / total_experiments
        avg_output_tokens = sum(r.output_tokens for r in results) / total_experiments

        return {
            "total_experiments": total_experiments,
            "successful_experiments": successful_experiments,
            "compression_experiments": compression_experiments,
            "success_rate": successful_experiments / total_experiments,
            "avg_response_time": avg_response_time,
            "avg_input_tokens": avg_input_tokens,
            "avg_output_tokens": avg_output_tokens,
            "total_tokens_used": sum(r.total_tokens for r in results),
        }
