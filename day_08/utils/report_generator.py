"""
Report generation module for experiment results.

This module provides classes for generating comprehensive reports
from experiment results using statistics collectors and formatters.
"""

from typing import List

from models.data_models import ExperimentResult
from utils.console_formatter import ConsoleFormatter
from utils.logging import LoggerFactory
from utils.statistics_collector import StatisticsCollector


class ReportGenerator:
    """
    Generate comprehensive reports from experiment results.
    
    Combines statistics collection and console formatting to create
    comprehensive reports for experiment analysis.
    """

    def __init__(self, collector: StatisticsCollector, formatter: ConsoleFormatter):
        """
        Initialize report generator with dependencies.
        
        Args:
            collector: Statistics collector for data analysis
            formatter: Console formatter for output formatting
        """
        self.collector = collector
        self.formatter = formatter
        self.logger = LoggerFactory.create_logger(__name__)

    def generate_summary_report(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print summary report.
        
        Args:
            results: List of experiment results to summarize
        """
        self.logger.info("Generating summary report", experiment_count=len(results))
        
        try:
            summary = self.formatter.format_experiment_summary(results)
            print(summary)
            self.logger.info("Summary report generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate summary report", error=str(e))
            print(f"\n❌ Ошибка при генерации сводного отчета: {e}")

    def generate_detailed_analysis(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print detailed analysis report.
        
        Args:
            results: List of experiment results to analyze
        """
        self.logger.info("Generating detailed analysis", experiment_count=len(results))
        
        try:
            experiment_stats = self.collector.collect_experiment_stats(results)
            compression_stats = self.collector.collect_compression_stats(results)
            
            analysis = self.formatter.format_detailed_analysis(experiment_stats, compression_stats)
            print(analysis)
            self.logger.info("Detailed analysis generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate detailed analysis", error=str(e))
            print(f"\n❌ Ошибка при генерации детального анализа: {e}")

    def generate_comparison_report(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print comparison report.
        
        Args:
            results: List of experiment results to compare
        """
        self.logger.info("Generating comparison report", experiment_count=len(results))
        
        try:
            compression_stats = self.collector.collect_compression_stats(results)
            performance_stats = self.collector.collect_performance_stats(results)
            
            comparison = self.formatter.format_compression_comparison(compression_stats)
            print(comparison)
            
            performance = self.formatter.format_performance_metrics(performance_stats)
            print(performance)
            
            self.logger.info("Comparison report generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate comparison report", error=str(e))
            print(f"\n❌ Ошибка при генерации отчета сравнения: {e}")

    def generate_recommendations_report(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print recommendations report.
        
        Args:
            results: List of experiment results to analyze for recommendations
        """
        self.logger.info("Generating recommendations report", experiment_count=len(results))
        
        try:
            recommendations = self.formatter.format_recommendations(results)
            print(recommendations)
            self.logger.info("Recommendations report generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate recommendations report", error=str(e))
            print(f"\n❌ Ошибка при генерации отчета рекомендаций: {e}")

    def generate_full_report(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print complete report with all sections.
        
        Args:
            results: List of experiment results to analyze
        """
        self.logger.info("Generating full report", experiment_count=len(results))
        
        try:
            # Summary
            self.generate_summary_report(results)
            
            # Detailed analysis
            self.generate_detailed_analysis(results)
            
            # Comparison
            self.generate_comparison_report(results)
            
            # Recommendations
            self.generate_recommendations_report(results)
            
            self.logger.info("Full report generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate full report", error=str(e))
            print(f"\n❌ Ошибка при генерации полного отчета: {e}")

    def generate_model_performance_report(self, results: List[ExperimentResult]) -> None:
        """
        Generate and print model performance report.
        
        Args:
            results: List of experiment results to analyze for model performance
        """
        self.logger.info("Generating model performance report", experiment_count=len(results))
        
        try:
            performance_stats = self.collector.collect_performance_stats(results)
            performance_report = self.formatter.format_performance_metrics(performance_stats)
            print(performance_report)
            self.logger.info("Model performance report generated successfully")
        except Exception as e:
            self.logger.error("Failed to generate model performance report", error=str(e))
            print(f"\n❌ Ошибка при генерации отчета производительности модели: {e}")
