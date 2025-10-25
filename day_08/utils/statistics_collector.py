"""
Statistics collection module for experiment analysis.

This module provides classes for collecting and aggregating
statistics from experiment results.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from models.data_models import ExperimentResult


@dataclass
class ExperimentStats:
    """Statistics for experiment results."""
    
    total_experiments: int
    successful_experiments: int
    compression_experiments: int
    success_rate: float
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    avg_response_time: float


@dataclass
class CompressionStats:
    """Statistics for compression analysis."""
    
    compression_count: int
    avg_compression_ratio: float
    strategy_stats: Dict[str, Dict[str, float]]
    best_compression_ratio: float
    worst_compression_ratio: float


@dataclass
class PerformanceStats:
    """Statistics for performance analysis."""
    
    fastest_experiment: ExperimentResult
    slowest_experiment: ExperimentResult
    time_difference: float
    avg_response_time: float
    model_performance: Dict[str, Dict[str, float]]


class StatisticsCollector:
    """
    Collect and aggregate experiment statistics.
    
    Provides methods to analyze experiment results and extract
    meaningful statistics for reporting and analysis.
    """

    def collect_experiment_stats(self, results: List[ExperimentResult]) -> ExperimentStats:
        """
        Collect basic experiment statistics.
        
        Args:
            results: List of experiment results to analyze
            
        Returns:
            ExperimentStats: Aggregated experiment statistics
        """
        if not results:
            return self._empty_experiment_stats()
        
        total_experiments = len(results)
        successful_experiments = len([r for r in results if r.response])
        compression_experiments = len([r for r in results if r.compression_applied])
        
        total_input_tokens = sum(r.input_tokens for r in results)
        total_output_tokens = sum(r.output_tokens for r in results)
        avg_response_time = sum(r.response_time for r in results) / total_experiments
        
        return ExperimentStats(
            total_experiments=total_experiments,
            successful_experiments=successful_experiments,
            compression_experiments=compression_experiments,
            success_rate=(successful_experiments / total_experiments) * 100,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            avg_response_time=avg_response_time
        )

    def collect_compression_stats(self, results: List[ExperimentResult]) -> CompressionStats:
        """
        Collect compression-specific statistics.
        
        Args:
            results: List of experiment results to analyze
            
        Returns:
            CompressionStats: Aggregated compression statistics
        """
        compressed_results = [r for r in results if r.compression_applied]
        
        if not compressed_results:
            return self._empty_compression_stats()
        
        compression_count = len(compressed_results)
        ratios = [r.compression_result.compression_ratio for r in compressed_results]
        avg_compression_ratio = sum(ratios) / compression_count
        
        strategy_stats = self._analyze_strategies(compressed_results)
        
        return CompressionStats(
            compression_count=compression_count,
            avg_compression_ratio=avg_compression_ratio,
            strategy_stats=strategy_stats,
            best_compression_ratio=min(ratios),
            worst_compression_ratio=max(ratios)
        )

    def collect_performance_stats(self, results: List[ExperimentResult]) -> PerformanceStats:
        """
        Collect performance-specific statistics.
        
        Args:
            results: List of experiment results to analyze
            
        Returns:
            PerformanceStats: Aggregated performance statistics
        """
        if not results:
            return self._empty_performance_stats()
        
        fastest_experiment = min(results, key=lambda r: r.response_time)
        slowest_experiment = max(results, key=lambda r: r.response_time)
        time_difference = slowest_experiment.response_time - fastest_experiment.response_time
        avg_response_time = sum(r.response_time for r in results) / len(results)
        
        model_performance = self._analyze_model_performance(results)
        
        return PerformanceStats(
            fastest_experiment=fastest_experiment,
            slowest_experiment=slowest_experiment,
            time_difference=time_difference,
            avg_response_time=avg_response_time,
            model_performance=model_performance
        )

    def _empty_experiment_stats(self) -> ExperimentStats:
        """Create empty experiment stats for empty results."""
        return ExperimentStats(
            total_experiments=0,
            successful_experiments=0,
            compression_experiments=0,
            success_rate=0.0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            avg_response_time=0.0
        )

    def _empty_compression_stats(self) -> CompressionStats:
        """Create empty compression stats for no compression results."""
        return CompressionStats(
            compression_count=0,
            avg_compression_ratio=0.0,
            strategy_stats={},
            best_compression_ratio=0.0,
            worst_compression_ratio=0.0
        )

    def _empty_performance_stats(self) -> PerformanceStats:
        """Create empty performance stats for empty results."""
        return PerformanceStats(
            fastest_experiment=None,
            slowest_experiment=None,
            time_difference=0.0,
            avg_response_time=0.0,
            model_performance={}
        )

    def _analyze_strategies(self, compressed_results: List[ExperimentResult]) -> Dict[str, Dict[str, float]]:
        """Analyze compression strategies and their performance."""
        strategies = {}
        
        for result in compressed_results:
            strategy = result.compression_result.strategy_used
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(result.compression_result.compression_ratio)
        
        strategy_stats = {}
        for strategy, ratios in strategies.items():
            strategy_stats[strategy] = {
                'avg_ratio': sum(ratios) / len(ratios),
                'count': len(ratios),
                'best_ratio': min(ratios),
                'worst_ratio': max(ratios)
            }
        
        return strategy_stats

    def _analyze_model_performance(self, results: List[ExperimentResult]) -> Dict[str, Dict[str, float]]:
        """Analyze performance by model."""
        models = {}
        
        for result in results:
            if result.model_name not in models:
                models[result.model_name] = []
            models[result.model_name].append(result)
        
        model_performance = {}
        for model_name, model_results in models.items():
            avg_response_time = sum(r.response_time for r in model_results) / len(model_results)
            avg_input_tokens = sum(r.input_tokens for r in model_results) / len(model_results)
            avg_output_tokens = sum(r.output_tokens for r in model_results) / len(model_results)
            
            model_performance[model_name] = {
                'avg_response_time': avg_response_time,
                'avg_input_tokens': avg_input_tokens,
                'avg_output_tokens': avg_output_tokens,
                'generation_speed': avg_output_tokens / avg_response_time if avg_response_time > 0 else 0,
                'experiment_count': len(model_results),
                'success_rate': len([r for r in model_results if r.response]) / len(model_results) * 100
            }
        
        return model_performance
