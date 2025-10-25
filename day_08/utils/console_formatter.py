"""
Console formatting module for experiment results.

This module provides classes for formatting experiment data
into readable console output.
"""

from typing import Dict, List

from models.data_models import ExperimentResult
from utils.statistics_collector import CompressionStats, ExperimentStats, PerformanceStats


class ConsoleFormatter:
    """
    Format data for console output.
    
    Provides methods to format experiment statistics and results
    into human-readable console output with proper formatting.
    """

    def format_experiment_summary(self, results: List[ExperimentResult]) -> str:
        """
        Format experiment summary for console output.
        
        Args:
            results: List of experiment results to format
            
        Returns:
            str: Formatted summary string
        """
        if not results:
            return "\n❌ Нет результатов для отображения"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("📊 СВОДКА ЭКСПЕРИМЕНТОВ С ТОКЕНАМИ")
        output.append("=" * 80)
        
        for i, result in enumerate(results, 1):
            output.append(f"\n🔬 Эксперимент {i}: {result.experiment_name}")
            output.append(f"   Модель: {result.model_name}")
            output.append(f"   Время ответа: {result.response_time:.2f} сек")
            output.append(f"   Входные токены: {result.input_tokens}")
            output.append(f"   Выходные токены: {result.output_tokens}")
            output.append(f"   Общие токены: {result.total_tokens}")
            output.append(
                f"   Сжатие применено: {'Да' if result.compression_applied else 'Нет'}"
            )
            
            if result.compression_result:
                output.append(
                    f"   Коэффициент сжатия: {result.compression_result.compression_ratio:.2f}"
                )
                output.append(f"   Стратегия сжатия: {result.compression_result.strategy_used}")
            
            output.append(f"   Длина ответа: {len(result.response)} символов")
            output.append(f"   Время выполнения: {result.timestamp.strftime('%H:%M:%S')}")
        
        return "\n".join(output)

    def format_compression_comparison(self, stats: CompressionStats) -> str:
        """
        Format compression comparison for console output.
        
        Args:
            stats: Compression statistics to format
            
        Returns:
            str: Formatted comparison string
        """
        if stats.compression_count == 0:
            return "\n❌ Нет экспериментов со сжатием для сравнения"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("🔄 СРАВНЕНИЕ СТРАТЕГИЙ СЖАТИЯ")
        output.append("=" * 80)
        
        for strategy, strategy_data in stats.strategy_stats.items():
            output.append(f"\n📋 Стратегия: {strategy}")
            output.append(f"   Количество экспериментов: {strategy_data['count']}")
            output.append(f"   Средний коэффициент сжатия: {strategy_data['avg_ratio']:.2f}")
            output.append(f"   Лучший коэффициент: {strategy_data['best_ratio']:.2f}")
            output.append(f"   Худший коэффициент: {strategy_data['worst_ratio']:.2f}")
        
        return "\n".join(output)

    def format_performance_metrics(self, stats: PerformanceStats) -> str:
        """
        Format performance metrics for console output.
        
        Args:
            stats: Performance statistics to format
            
        Returns:
            str: Formatted metrics string
        """
        if not stats.fastest_experiment:
            return "\n❌ Нет результатов для анализа производительности"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("⚡ АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ")
        output.append("=" * 80)
        
        output.append(f"\n📈 Общая производительность:")
        output.append(
            f"   Самый быстрый ответ: {stats.fastest_experiment.experiment_name} "
            f"({stats.fastest_experiment.response_time:.2f} сек)"
        )
        output.append(
            f"   Самый медленный ответ: {stats.slowest_experiment.experiment_name} "
            f"({stats.slowest_experiment.response_time:.2f} сек)"
        )
        output.append(f"   Разница во времени: {stats.time_difference:.2f} сек")
        output.append(f"   Среднее время ответа: {stats.avg_response_time:.2f} сек")
        
        if stats.model_performance:
            output.append(f"\n🤖 Производительность по моделям:")
            for model_name, model_data in stats.model_performance.items():
                output.append(f"\n🔧 Модель: {model_name}")
                output.append(f"   Количество экспериментов: {model_data['experiment_count']}")
                output.append(f"   Среднее время ответа: {model_data['avg_response_time']:.2f} сек")
                output.append(f"   Средние входные токены: {model_data['avg_input_tokens']:.0f}")
                output.append(f"   Средние выходные токены: {model_data['avg_output_tokens']:.0f}")
                output.append(f"   Скорость генерации: {model_data['generation_speed']:.1f} токенов/сек")
                output.append(f"   Процент успеха: {model_data['success_rate']:.1f}%")
        
        return "\n".join(output)

    def format_recommendations(self, results: List[ExperimentResult]) -> str:
        """
        Format recommendations based on experiment results.
        
        Args:
            results: List of experiment results to analyze
            
        Returns:
            str: Formatted recommendations string
        """
        if not results:
            return "\n❌ Нет результатов для рекомендаций"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append("💡 РЕКОМЕНДАЦИИ")
        output.append("=" * 80)
        
        # Performance recommendations
        fastest_result = min(results, key=lambda r: r.response_time)
        slowest_result = max(results, key=lambda r: r.response_time)
        
        output.append(f"\n⚡ Производительность:")
        output.append(
            f"   Самый быстрый ответ: {fastest_result.experiment_name} "
            f"({fastest_result.response_time:.2f} сек)"
        )
        output.append(
            f"   Самый медленный ответ: {slowest_result.experiment_name} "
            f"({slowest_result.response_time:.2f} сек)"
        )
        
        # Compression recommendations
        compressed_results = [r for r in results if r.compression_applied]
        if compressed_results:
            best_compression = min(
                compressed_results, key=lambda r: r.compression_result.compression_ratio
            )
            output.append(f"\n🗜️  Сжатие:")
            output.append(
                f"   Лучшее сжатие: {best_compression.experiment_name} "
                f"(коэффициент: {best_compression.compression_result.compression_ratio:.2f})"
            )
            output.append(f"   Стратегия: {best_compression.compression_result.strategy_used}")
        
        # General recommendations
        output.append(f"\n🎯 Общие рекомендации:")
        
        # Check if any experiments exceeded limits
        exceeded_limit = any(
            r.input_tokens > 8192 for r in results if r.model_name == "starcoder"
        )
        
        if exceeded_limit:
            output.append(f"   ⚠️  Обнаружены запросы, превышающие лимиты модели")
            output.append(f"   💡 Используйте сжатие для запросов >8192 токенов")
        
        # Compression strategy recommendations
        truncation_results = [
            r for r in compressed_results
            if r.compression_result and r.compression_result.strategy_used == "truncation"
        ]
        keyword_results = [
            r for r in compressed_results
            if r.compression_result and r.compression_result.strategy_used == "keywords"
        ]
        
        if truncation_results and keyword_results:
            avg_truncation = sum(
                r.compression_result.compression_ratio for r in truncation_results
            ) / len(truncation_results)
            avg_keywords = sum(
                r.compression_result.compression_ratio for r in keyword_results
            ) / len(keyword_results)
            
            if avg_truncation < avg_keywords:
                output.append(f"   💡 Стратегия 'truncation' лучше сохраняет контекст")
            else:
                output.append(f"   💡 Стратегия 'keywords' лучше для поиска информации")
        
        output.append(f"   💡 Мониторьте время ответа при больших запросах")
        output.append(f"   💡 Используйте сжатие для оптимизации использования токенов")
        
        return "\n".join(output)

    def format_detailed_analysis(self, stats: ExperimentStats, compression_stats: CompressionStats) -> str:
        """
        Format detailed analysis combining experiment and compression stats.
        
        Args:
            stats: Experiment statistics to format
            compression_stats: Compression statistics to format
            
        Returns:
            str: Formatted detailed analysis string
        """
        output = []
        output.append("\n" + "=" * 80)
        output.append("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ")
        output.append("=" * 80)
        
        output.append(f"\n📈 Общая статистика:")
        output.append(f"   Всего экспериментов: {stats.total_experiments}")
        output.append(f"   Успешных экспериментов: {stats.successful_experiments}")
        output.append(f"   Экспериментов со сжатием: {stats.compression_experiments}")
        output.append(f"   Процент успеха: {stats.success_rate:.1f}%")
        
        output.append(f"\n📊 Статистика токенов:")
        output.append(f"   Общие входные токены: {stats.total_input_tokens}")
        output.append(f"   Общие выходные токены: {stats.total_output_tokens}")
        output.append(f"   Общие токены: {stats.total_tokens}")
        output.append(f"   Среднее время ответа: {stats.avg_response_time:.2f} сек")
        
        # Compression analysis
        if compression_stats.compression_count > 0:
            output.append(f"\n🗜️  Анализ сжатия:")
            output.append(f"   Экспериментов со сжатием: {compression_stats.compression_count}")
            output.append(f"   Средний коэффициент сжатия: {compression_stats.avg_compression_ratio:.2f}")
            
            if compression_stats.strategy_stats:
                output.append(f"   Стратегии сжатия:")
                for strategy, strategy_data in compression_stats.strategy_stats.items():
                    output.append(
                        f"     {strategy}: {strategy_data['avg_ratio']:.2f} "
                        f"(экспериментов: {strategy_data['count']})"
                    )
        
        return "\n".join(output)
