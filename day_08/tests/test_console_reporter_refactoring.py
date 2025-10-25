"""
Tests for console reporter refactoring.

This module tests the refactored console reporter components:
StatisticsCollector, ConsoleFormatter, ReportGenerator, and ConsoleReporter facade.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from models.data_models import CompressionResult, ExperimentResult
from utils.console_formatter import ConsoleFormatter
from utils.console_reporter import ConsoleReporter
from utils.report_generator import ReportGenerator
from utils.statistics_collector import (
    CompressionStats,
    ExperimentStats,
    PerformanceStats,
    StatisticsCollector,
)


class TestStatisticsCollector:
    """Test StatisticsCollector functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = StatisticsCollector()
        self.sample_results = self._create_sample_results()

    def _create_sample_results(self):
        """Create sample experiment results for testing."""
        compression_result = CompressionResult(
            original_text="Original text",
            compressed_text="Compressed text",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation",
        )

        return [
            ExperimentResult(
                experiment_name="Test Experiment 1",
                model_name="starcoder",
                original_query="Test query 1",
                processed_query="Test query 1",
                response="Test response 1",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                response_time=1.5,
                compression_applied=True,
                compression_result=compression_result,
                timestamp=datetime.now(),
            ),
            ExperimentResult(
                experiment_name="Test Experiment 2",
                model_name="mistral",
                original_query="Test query 2",
                processed_query="Test query 2",
                response="Test response 2",
                input_tokens=30,
                output_tokens=20,
                total_tokens=50,
                response_time=2.0,
                compression_applied=False,
                compression_result=None,
                timestamp=datetime.now(),
            ),
        ]

    def test_collect_experiment_stats_with_results(self):
        """Test collecting experiment stats with valid results."""
        stats = self.collector.collect_experiment_stats(self.sample_results)

        assert stats.total_experiments == 2
        assert stats.successful_experiments == 2
        assert stats.compression_experiments == 1
        assert stats.success_rate == 100.0
        assert stats.total_input_tokens == 80
        assert stats.total_output_tokens == 45
        assert stats.total_tokens == 125
        assert stats.avg_response_time == 1.75

    def test_collect_experiment_stats_empty_results(self):
        """Test collecting experiment stats with empty results."""
        stats = self.collector.collect_experiment_stats([])

        assert stats.total_experiments == 0
        assert stats.successful_experiments == 0
        assert stats.compression_experiments == 0
        assert stats.success_rate == 0.0
        assert stats.total_input_tokens == 0
        assert stats.total_output_tokens == 0
        assert stats.total_tokens == 0
        assert stats.avg_response_time == 0.0

    def test_collect_compression_stats_with_compression(self):
        """Test collecting compression stats with compression results."""
        stats = self.collector.collect_compression_stats(self.sample_results)

        assert stats.compression_count == 1
        assert stats.avg_compression_ratio == 0.5
        assert stats.best_compression_ratio == 0.5
        assert stats.worst_compression_ratio == 0.5
        assert "truncation" in stats.strategy_stats
        assert stats.strategy_stats["truncation"]["count"] == 1
        assert stats.strategy_stats["truncation"]["avg_ratio"] == 0.5

    def test_collect_compression_stats_no_compression(self):
        """Test collecting compression stats with no compression results."""
        no_compression_results = [
            ExperimentResult(
                experiment_name="No Compression",
                model_name="starcoder",
                original_query="Test query",
                processed_query="Test query",
                response="Test response",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                response_time=1.5,
                compression_applied=False,
                compression_result=None,
                timestamp=datetime.now(),
            )
        ]

        stats = self.collector.collect_compression_stats(no_compression_results)

        assert stats.compression_count == 0
        assert stats.avg_compression_ratio == 0.0
        assert stats.strategy_stats == {}

    def test_collect_performance_stats(self):
        """Test collecting performance stats."""
        stats = self.collector.collect_performance_stats(self.sample_results)

        assert stats.fastest_experiment.experiment_name == "Test Experiment 1"
        assert stats.slowest_experiment.experiment_name == "Test Experiment 2"
        assert stats.time_difference == 0.5
        assert stats.avg_response_time == 1.75
        assert len(stats.model_performance) == 2
        assert "starcoder" in stats.model_performance
        assert "mistral" in stats.model_performance

    def test_collect_performance_stats_empty_results(self):
        """Test collecting performance stats with empty results."""
        stats = self.collector.collect_performance_stats([])

        assert stats.fastest_experiment is None
        assert stats.slowest_experiment is None
        assert stats.time_difference == 0.0
        assert stats.avg_response_time == 0.0
        assert stats.model_performance == {}


class TestConsoleFormatter:
    """Test ConsoleFormatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ConsoleFormatter()
        self.sample_results = self._create_sample_results()

    def _create_sample_results(self):
        """Create sample experiment results for testing."""
        compression_result = CompressionResult(
            original_text="Original text",
            compressed_text="Compressed text",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation",
        )

        return [
            ExperimentResult(
                experiment_name="Test Experiment",
                model_name="starcoder",
                original_query="Test query",
                processed_query="Test query",
                response="Test response",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                response_time=1.5,
                compression_applied=True,
                compression_result=compression_result,
                timestamp=datetime.now(),
            )
        ]

    def test_format_experiment_summary_with_results(self):
        """Test formatting experiment summary with results."""
        summary = self.formatter.format_experiment_summary(self.sample_results)

        assert "СВОДКА ЭКСПЕРИМЕНТОВ С ТОКЕНАМИ" in summary
        assert "Test Experiment" in summary
        assert "starcoder" in summary
        assert "1.50 сек" in summary
        assert "50" in summary  # input tokens
        assert "25" in summary  # output tokens

    def test_format_experiment_summary_empty_results(self):
        """Test formatting experiment summary with empty results."""
        summary = self.formatter.format_experiment_summary([])

        assert "Нет результатов для отображения" in summary

    def test_format_compression_comparison_with_compression(self):
        """Test formatting compression comparison with compression data."""
        compression_stats = CompressionStats(
            compression_count=1,
            avg_compression_ratio=0.5,
            strategy_stats={
                "truncation": {
                    "avg_ratio": 0.5,
                    "count": 1,
                    "best_ratio": 0.5,
                    "worst_ratio": 0.5,
                }
            },
            best_compression_ratio=0.5,
            worst_compression_ratio=0.5,
        )

        comparison = self.formatter.format_compression_comparison(compression_stats)

        assert "СРАВНЕНИЕ СТРАТЕГИЙ СЖАТИЯ" in comparison
        assert "truncation" in comparison
        assert "0.50" in comparison

    def test_format_compression_comparison_no_compression(self):
        """Test formatting compression comparison with no compression data."""
        compression_stats = CompressionStats(
            compression_count=0,
            avg_compression_ratio=0.0,
            strategy_stats={},
            best_compression_ratio=0.0,
            worst_compression_ratio=0.0,
        )

        comparison = self.formatter.format_compression_comparison(compression_stats)

        assert "Нет экспериментов со сжатием для сравнения" in comparison

    def test_format_performance_metrics(self):
        """Test formatting performance metrics."""
        performance_stats = PerformanceStats(
            fastest_experiment=self.sample_results[0],
            slowest_experiment=self.sample_results[0],
            time_difference=0.0,
            avg_response_time=1.5,
            model_performance={
                "starcoder": {
                    "avg_response_time": 1.5,
                    "avg_input_tokens": 50.0,
                    "avg_output_tokens": 25.0,
                    "generation_speed": 16.7,
                    "experiment_count": 1,
                    "success_rate": 100.0,
                }
            },
        )

        metrics = self.formatter.format_performance_metrics(performance_stats)

        assert "АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ" in metrics
        assert "Test Experiment" in metrics
        assert "1.50 сек" in metrics
        assert "starcoder" in metrics

    def test_format_recommendations(self):
        """Test formatting recommendations."""
        recommendations = self.formatter.format_recommendations(self.sample_results)

        assert "РЕКОМЕНДАЦИИ" in recommendations
        assert "Производительность" in recommendations
        assert "Сжатие" in recommendations
        assert "Общие рекомендации" in recommendations

    def test_format_detailed_analysis(self):
        """Test formatting detailed analysis."""
        experiment_stats = ExperimentStats(
            total_experiments=1,
            successful_experiments=1,
            compression_experiments=1,
            success_rate=100.0,
            total_input_tokens=50,
            total_output_tokens=25,
            total_tokens=75,
            avg_response_time=1.5,
        )

        compression_stats = CompressionStats(
            compression_count=1,
            avg_compression_ratio=0.5,
            strategy_stats={
                "truncation": {
                    "avg_ratio": 0.5,
                    "count": 1,
                    "best_ratio": 0.5,
                    "worst_ratio": 0.5,
                }
            },
            best_compression_ratio=0.5,
            worst_compression_ratio=0.5,
        )

        analysis = self.formatter.format_detailed_analysis(
            experiment_stats, compression_stats
        )

        assert "ДЕТАЛЬНЫЙ АНАЛИЗ" in analysis
        assert "Общая статистика" in analysis
        assert "Статистика токенов" in analysis
        assert "Анализ сжатия" in analysis


class TestReportGenerator:
    """Test ReportGenerator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = Mock(spec=StatisticsCollector)
        self.formatter = Mock(spec=ConsoleFormatter)
        self.generator = ReportGenerator(self.collector, self.formatter)
        self.sample_results = self._create_sample_results()

    def _create_sample_results(self):
        """Create sample experiment results for testing."""
        return [
            ExperimentResult(
                experiment_name="Test Experiment",
                model_name="starcoder",
                original_query="Test query",
                processed_query="Test query",
                response="Test response",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                response_time=1.5,
                compression_applied=False,
                compression_result=None,
                timestamp=datetime.now(),
            )
        ]

    @patch("builtins.print")
    def test_generate_summary_report_success(self, mock_print):
        """Test successful summary report generation."""
        self.formatter.format_experiment_summary.return_value = "Test summary"

        self.generator.generate_summary_report(self.sample_results)

        self.formatter.format_experiment_summary.assert_called_once_with(
            self.sample_results
        )
        mock_print.assert_called_once_with("Test summary")

    @patch("builtins.print")
    def test_generate_summary_report_error(self, mock_print):
        """Test summary report generation with error."""
        self.formatter.format_experiment_summary.side_effect = Exception("Test error")

        self.generator.generate_summary_report(self.sample_results)

        mock_print.assert_called_with(
            "\n❌ Ошибка при генерации сводного отчета: Test error"
        )

    @patch("builtins.print")
    def test_generate_detailed_analysis_success(self, mock_print):
        """Test successful detailed analysis generation."""
        experiment_stats = Mock()
        compression_stats = Mock()
        self.collector.collect_experiment_stats.return_value = experiment_stats
        self.collector.collect_compression_stats.return_value = compression_stats
        self.formatter.format_detailed_analysis.return_value = "Test analysis"

        self.generator.generate_detailed_analysis(self.sample_results)

        self.collector.collect_experiment_stats.assert_called_once_with(
            self.sample_results
        )
        self.collector.collect_compression_stats.assert_called_once_with(
            self.sample_results
        )
        self.formatter.format_detailed_analysis.assert_called_once_with(
            experiment_stats, compression_stats
        )
        mock_print.assert_called_once_with("Test analysis")

    @patch("builtins.print")
    def test_generate_comparison_report_success(self, mock_print):
        """Test successful comparison report generation."""
        compression_stats = Mock()
        performance_stats = Mock()
        self.collector.collect_compression_stats.return_value = compression_stats
        self.collector.collect_performance_stats.return_value = performance_stats
        self.formatter.format_compression_comparison.return_value = "Test comparison"
        self.formatter.format_performance_metrics.return_value = "Test performance"

        self.generator.generate_comparison_report(self.sample_results)

        self.collector.collect_compression_stats.assert_called_once_with(
            self.sample_results
        )
        self.collector.collect_performance_stats.assert_called_once_with(
            self.sample_results
        )
        self.formatter.format_compression_comparison.assert_called_once_with(
            compression_stats
        )
        self.formatter.format_performance_metrics.assert_called_once_with(
            performance_stats
        )
        assert mock_print.call_count == 2

    @patch("builtins.print")
    def test_generate_recommendations_report_success(self, mock_print):
        """Test successful recommendations report generation."""
        self.formatter.format_recommendations.return_value = "Test recommendations"

        self.generator.generate_recommendations_report(self.sample_results)

        self.formatter.format_recommendations.assert_called_once_with(
            self.sample_results
        )
        mock_print.assert_called_once_with("Test recommendations")

    @patch("builtins.print")
    def test_generate_full_report_success(self, mock_print):
        """Test successful full report generation."""
        self.generator.generate_summary_report = Mock()
        self.generator.generate_detailed_analysis = Mock()
        self.generator.generate_comparison_report = Mock()
        self.generator.generate_recommendations_report = Mock()

        self.generator.generate_full_report(self.sample_results)

        self.generator.generate_summary_report.assert_called_once_with(
            self.sample_results
        )
        self.generator.generate_detailed_analysis.assert_called_once_with(
            self.sample_results
        )
        self.generator.generate_comparison_report.assert_called_once_with(
            self.sample_results
        )
        self.generator.generate_recommendations_report.assert_called_once_with(
            self.sample_results
        )


class TestConsoleReporterFacade:
    """Test ConsoleReporter facade functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ConsoleReporter()
        self.sample_results = self._create_sample_results()

    def _create_sample_results(self):
        """Create sample experiment results for testing."""
        return [
            ExperimentResult(
                experiment_name="Test Experiment",
                model_name="starcoder",
                original_query="Test query",
                processed_query="Test query",
                response="Test response",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                response_time=1.5,
                compression_applied=False,
                compression_result=None,
                timestamp=datetime.now(),
            )
        ]

    def test_initialization(self):
        """Test ConsoleReporter initialization."""
        assert self.reporter.collector is not None
        assert self.reporter.formatter is not None
        assert self.reporter.report_generator is not None
        assert self.reporter.logger is not None

    @patch("utils.report_generator.ReportGenerator.generate_summary_report")
    def test_print_experiment_summary_delegation(self, mock_generate):
        """Test that print_experiment_summary delegates to report generator."""
        self.reporter.print_experiment_summary(self.sample_results)

        mock_generate.assert_called_once_with(self.sample_results)

    @patch("utils.report_generator.ReportGenerator.generate_detailed_analysis")
    def test_print_detailed_analysis_delegation(self, mock_generate):
        """Test that print_detailed_analysis delegates to report generator."""
        self.reporter.print_detailed_analysis(self.sample_results)

        mock_generate.assert_called_once_with(self.sample_results)

    @patch("utils.report_generator.ReportGenerator.generate_recommendations_report")
    def test_print_recommendations_delegation(self, mock_generate):
        """Test that print_recommendations delegates to report generator."""
        self.reporter.print_recommendations(self.sample_results)

        mock_generate.assert_called_once_with(self.sample_results)

    @patch("utils.statistics_collector.StatisticsCollector.collect_compression_stats")
    @patch("utils.console_formatter.ConsoleFormatter.format_compression_comparison")
    @patch("builtins.print")
    def test_print_compression_comparison_delegation(
        self, mock_print, mock_format, mock_collect
    ):
        """Test that print_compression_comparison delegates to collector and formatter."""
        mock_stats = Mock()
        mock_collect.return_value = mock_stats
        mock_format.return_value = "Test comparison"

        self.reporter.print_compression_comparison(self.sample_results)

        mock_collect.assert_called_once_with(self.sample_results)
        mock_format.assert_called_once_with(mock_stats)
        mock_print.assert_called_once_with("Test comparison")

    @patch("utils.report_generator.ReportGenerator.generate_model_performance_report")
    def test_print_model_performance_delegation(self, mock_generate):
        """Test that print_model_performance delegates to report generator."""
        self.reporter.print_model_performance(self.sample_results)

        mock_generate.assert_called_once_with(self.sample_results)
