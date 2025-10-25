"""
Console reporting module for displaying experiment results.

This module provides methods to display experiment results in a
clear, formatted way in the console, including summaries, analysis,
and recommendations.

Note: This class now acts as a facade, delegating to the new
refactored components for better separation of concerns.
"""

from typing import Any, Dict, List

from models.data_models import ExperimentResult
from utils.console_formatter import ConsoleFormatter
from utils.logging import LoggerFactory
from utils.report_generator import ReportGenerator
from utils.statistics_collector import StatisticsCollector


class ConsoleReporter:
    """
    Console reporter for displaying experiment results.

    Provides methods to format and display experiment results
    in a clear, readable format in the console.

    This class now acts as a facade, delegating to specialized
    components for better separation of concerns while maintaining
    backward compatibility.
    """

    def __init__(self):
        """Initialize console reporter with refactored components."""
        self.logger = LoggerFactory.create_logger(__name__)
        self.collector = StatisticsCollector()
        self.formatter = ConsoleFormatter()
        self.report_generator = ReportGenerator(self.collector, self.formatter)

    def print_experiment_summary(self, results: List[ExperimentResult]) -> None:
        """
        Print summary of all experiments.

        Args:
            results: List of experiment results to summarize
        """
        self.report_generator.generate_summary_report(results)

    def print_detailed_analysis(self, results: List[ExperimentResult]) -> None:
        """
        Print detailed analysis of experiment results.

        Args:
            results: List of experiment results to analyze
        """
        self.report_generator.generate_detailed_analysis(results)

    def print_recommendations(self, results: List[ExperimentResult]) -> None:
        """
        Print recommendations based on experiment results.

        Args:
            results: List of experiment results to analyze
        """
        self.report_generator.generate_recommendations_report(results)

    def print_compression_comparison(self, results: List[ExperimentResult]) -> None:
        """
        Print detailed comparison of compression strategies.

        Args:
            results: List of experiment results to compare
        """
        compression_stats = self.collector.collect_compression_stats(results)
        comparison = self.formatter.format_compression_comparison(compression_stats)
        print(comparison)

    def print_model_performance(self, results: List[ExperimentResult]) -> None:
        """
        Print model performance analysis.

        Args:
            results: List of experiment results to analyze
        """
        self.report_generator.generate_model_performance_report(results)
