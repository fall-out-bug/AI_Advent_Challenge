"""
Statistics calculation utilities.

This module provides statistical calculations for experiment results
and compression analysis.
"""

import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.interfaces.protocols import StatisticsCalculatorProtocol
from models.data_models import CompressionResult, ExperimentResult


@dataclass
class StatisticsSummary:
    """Summary statistics for a dataset."""
    
    count: int
    mean: float
    median: float
    min_value: float
    max_value: float
    std_dev: float
    variance: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float


class StatisticsCalculator:
    """Statistics calculator implementation."""
    
    def calculate_average(self, values: List[float]) -> float:
        """Calculate average value."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def calculate_median(self, values: List[float]) -> float:
        """Calculate median value."""
        if not values:
            return 0.0
        return statistics.median(values)
    
    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def calculate_compression_stats(self, results: List[CompressionResult]) -> Dict[str, float]:
        """Calculate compression statistics."""
        if not results:
            return {
                "avg_ratio": 0.0,
                "min_ratio": 0.0,
                "max_ratio": 0.0,
                "median_ratio": 0.0,
                "std_dev_ratio": 0.0,
                "avg_tokens_saved": 0.0,
                "total_tokens_saved": 0.0,
            }
        
        ratios = [result.compression_ratio for result in results]
        tokens_saved = [result.original_tokens - result.compressed_tokens for result in results]
        
        return {
            "avg_ratio": self.calculate_average(ratios),
            "min_ratio": min(ratios),
            "max_ratio": max(ratios),
            "median_ratio": self.calculate_median(ratios),
            "std_dev_ratio": statistics.stdev(ratios) if len(ratios) > 1 else 0.0,
            "avg_tokens_saved": self.calculate_average(tokens_saved),
            "total_tokens_saved": sum(tokens_saved),
        }
    
    def calculate_experiment_stats(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        """Calculate experiment statistics."""
        if not results:
            return {
                "total_experiments": 0,
                "successful_experiments": 0,
                "failed_experiments": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_tokens_used": 0.0,
                "avg_compression_ratio": 0.0,
            }
        
        # Determine success based on whether there's a response and no error
        successful = [r for r in results if r.response and r.response.strip()]
        failed = [r for r in results if not r.response or not r.response.strip()]
        
        response_times = [r.response_time for r in results if r.response_time is not None]
        tokens_used = [r.total_tokens for r in results]
        compression_ratios = [r.compression_result.compression_ratio for r in results 
                            if r.compression_result is not None]
        
        return {
            "total_experiments": len(results),
            "successful_experiments": len(successful),
            "failed_experiments": len(failed),
            "success_rate": len(successful) / len(results) if results else 0.0,
            "avg_response_time": self.calculate_average(response_times),
            "avg_tokens_used": self.calculate_average(tokens_used),
            "avg_compression_ratio": self.calculate_average(compression_ratios),
        }
    
    def calculate_summary_statistics(self, values: List[float]) -> StatisticsSummary:
        """Calculate comprehensive summary statistics."""
        if not values:
            return StatisticsSummary(
                count=0, mean=0.0, median=0.0, min_value=0.0, max_value=0.0,
                std_dev=0.0, variance=0.0, percentile_25=0.0, percentile_75=0.0,
                percentile_90=0.0, percentile_95=0.0
            )
        
        return StatisticsSummary(
            count=len(values),
            mean=self.calculate_average(values),
            median=self.calculate_median(values),
            min_value=min(values),
            max_value=max(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            variance=statistics.variance(values) if len(values) > 1 else 0.0,
            percentile_25=self.calculate_percentile(values, 25),
            percentile_75=self.calculate_percentile(values, 75),
            percentile_90=self.calculate_percentile(values, 90),
            percentile_95=self.calculate_percentile(values, 95),
        )
    
    def calculate_model_comparison_stats(self, results: List[ExperimentResult]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics grouped by model."""
        model_stats = {}
        
        # Group results by model
        models = {}
        for result in results:
            model_name = result.model_name
            if model_name not in models:
                models[model_name] = []
            models[model_name].append(result)
        
        # Calculate stats for each model
        for model_name, model_results in models.items():
            model_stats[model_name] = self.calculate_experiment_stats(model_results)
        
        return model_stats
    
    def calculate_strategy_comparison_stats(self, results: List[ExperimentResult]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics grouped by compression strategy."""
        strategy_stats = {}
        
        # Group results by strategy
        strategies = {}
        for result in results:
            if result.compression_result:
                strategy = result.compression_result.strategy_used
                if strategy not in strategies:
                    strategies[strategy] = []
                strategies[strategy].append(result)
        
        # Calculate stats for each strategy
        for strategy_name, strategy_results in strategies.items():
            strategy_stats[strategy_name] = self.calculate_experiment_stats(strategy_results)
        
        return strategy_stats
    
    def calculate_performance_metrics(self, results: List[ExperimentResult]) -> Dict[str, float]:
        """Calculate performance metrics."""
        if not results:
            return {
                "throughput_experiments_per_second": 0.0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }
        
        response_times_ms = [r.response_time * 1000 for r in results if r.response_time is not None]
        
        if not response_times_ms:
            return {
                "throughput_experiments_per_second": 0.0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }
        
        total_time = sum(response_times_ms) / 1000  # Convert back to seconds
        throughput = len(results) / total_time if total_time > 0 else 0.0
        
        return {
            "throughput_experiments_per_second": throughput,
            "avg_latency_ms": self.calculate_average(response_times_ms),
            "p95_latency_ms": self.calculate_percentile(response_times_ms, 95),
            "p99_latency_ms": self.calculate_percentile(response_times_ms, 99),
        }
    
    def calculate_efficiency_metrics(self, results: List[ExperimentResult]) -> Dict[str, float]:
        """Calculate efficiency metrics."""
        if not results:
            return {
                "avg_token_efficiency": 0.0,
                "avg_compression_efficiency": 0.0,
                "avg_cost_efficiency": 0.0,
            }
        
        token_efficiencies = []
        compression_efficiencies = []
        cost_efficiencies = []
        
        for result in results:
            # Token efficiency: output tokens / input tokens
            if result.total_tokens > 0:
                token_efficiency = result.output_tokens / result.total_tokens
                token_efficiencies.append(token_efficiency)
            
            # Compression efficiency: compression ratio
            if result.compression_result:
                compression_efficiencies.append(result.compression_result.compression_ratio)
            
            # Cost efficiency: estimated cost per token
            if result.estimated_cost > 0 and result.total_tokens > 0:
                cost_efficiency = result.estimated_cost / result.total_tokens
                cost_efficiencies.append(cost_efficiency)
        
        return {
            "avg_token_efficiency": self.calculate_average(token_efficiencies),
            "avg_compression_efficiency": self.calculate_average(compression_efficiencies),
            "avg_cost_efficiency": self.calculate_average(cost_efficiencies),
        }


class StatisticsReporter:
    """Statistics reporter for generating reports."""
    
    def __init__(self, calculator: StatisticsCalculator):
        """Initialize statistics reporter."""
        self.calculator = calculator
    
    def generate_summary_report(self, results: List[ExperimentResult]) -> str:
        """Generate summary report."""
        stats = self.calculator.calculate_experiment_stats(results)
        
        report = f"""
Experiment Summary Report
========================

Total Experiments: {stats['total_experiments']}
Successful: {stats['successful_experiments']}
Failed: {stats['failed_experiments']}
Success Rate: {stats['success_rate']:.2%}

Average Response Time: {stats['avg_response_time']:.2f}s
Average Tokens Used: {stats['avg_tokens_used']:.0f}
Average Compression Ratio: {stats['avg_compression_ratio']:.2f}
"""
        return report
    
    def generate_model_comparison_report(self, results: List[ExperimentResult]) -> str:
        """Generate model comparison report."""
        model_stats = self.calculator.calculate_model_comparison_stats(results)
        
        report = "Model Comparison Report\n"
        report += "======================\n\n"
        
        for model_name, stats in model_stats.items():
            report += f"Model: {model_name}\n"
            report += f"  Success Rate: {stats['success_rate']:.2%}\n"
            report += f"  Avg Response Time: {stats['avg_response_time']:.2f}s\n"
            report += f"  Avg Tokens Used: {stats['avg_tokens_used']:.0f}\n"
            report += f"  Avg Compression Ratio: {stats['avg_compression_ratio']:.2f}\n\n"
        
        return report
    
    def generate_performance_report(self, results: List[ExperimentResult]) -> str:
        """Generate performance report."""
        perf_metrics = self.calculator.calculate_performance_metrics(results)
        efficiency_metrics = self.calculator.calculate_efficiency_metrics(results)
        
        report = f"""
Performance Report
=================

Throughput: {perf_metrics['throughput_experiments_per_second']:.2f} experiments/second
Average Latency: {perf_metrics['avg_latency_ms']:.2f}ms
95th Percentile Latency: {perf_metrics['p95_latency_ms']:.2f}ms
99th Percentile Latency: {perf_metrics['p99_latency_ms']:.2f}ms

Efficiency Metrics:
  Token Efficiency: {efficiency_metrics['avg_token_efficiency']:.2f}
  Compression Efficiency: {efficiency_metrics['avg_compression_efficiency']:.2f}
  Cost Efficiency: {efficiency_metrics['avg_cost_efficiency']:.4f}
"""
        return report
