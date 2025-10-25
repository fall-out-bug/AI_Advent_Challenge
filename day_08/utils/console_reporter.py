"""
Console reporting module for displaying experiment results.

This module provides methods to display experiment results in a
clear, formatted way in the console, including summaries, analysis,
and recommendations.
"""

from typing import Any, Dict, List

from models.data_models import ExperimentResult


class ConsoleReporter:
    """
    Console reporter for displaying experiment results.

    Provides methods to format and display experiment results
    in a clear, readable format in the console.
    """

    def print_experiment_summary(self, results: List[ExperimentResult]) -> None:
        """
        Print summary of all experiments.

        Args:
            results: List of experiment results to summarize
        """
        if not results:
            print("\n❌ Нет результатов для отображения")
            return

        print("\n" + "=" * 80)
        print("📊 СВОДКА ЭКСПЕРИМЕНТОВ С ТОКЕНАМИ")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n🔬 Эксперимент {i}: {result.experiment_name}")
            print(f"   Модель: {result.model_name}")
            print(f"   Время ответа: {result.response_time:.2f} сек")
            print(f"   Входные токены: {result.input_tokens}")
            print(f"   Выходные токены: {result.output_tokens}")
            print(f"   Общие токены: {result.total_tokens}")
            print(
                f"   Сжатие применено: {'Да' if result.compression_applied else 'Нет'}"
            )

            if result.compression_result:
                print(
                    f"   Коэффициент сжатия: {result.compression_result.compression_ratio:.2f}"
                )
                print(f"   Стратегия сжатия: {result.compression_result.strategy_used}")

            print(f"   Длина ответа: {len(result.response)} символов")
            print(f"   Время выполнения: {result.timestamp.strftime('%H:%M:%S')}")

    def print_detailed_analysis(self, results: List[ExperimentResult]) -> None:
        """
        Print detailed analysis of experiment results.

        Args:
            results: List of experiment results to analyze
        """
        if not results:
            print("\n❌ Нет результатов для анализа")
            return

        print("\n" + "=" * 80)
        print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ")
        print("=" * 80)

        # Basic statistics
        total_experiments = len(results)
        successful_experiments = len([r for r in results if r.response])
        compression_experiments = len([r for r in results if r.compression_applied])

        total_input_tokens = sum(r.input_tokens for r in results)
        total_output_tokens = sum(r.output_tokens for r in results)
        avg_response_time = sum(r.response_time for r in results) / total_experiments

        print(f"\n📈 Общая статистика:")
        print(f"   Всего экспериментов: {total_experiments}")
        print(f"   Успешных экспериментов: {successful_experiments}")
        print(f"   Экспериментов со сжатием: {compression_experiments}")
        print(
            f"   Процент успеха: {(successful_experiments/total_experiments)*100:.1f}%"
        )

        print(f"\n📊 Статистика токенов:")
        print(f"   Общие входные токены: {total_input_tokens}")
        print(f"   Общие выходные токены: {total_output_tokens}")
        print(f"   Общие токены: {total_input_tokens + total_output_tokens}")
        print(f"   Среднее время ответа: {avg_response_time:.2f} сек")

        # Compression analysis
        compressed_results = [r for r in results if r.compression_applied]
        if compressed_results:
            print(f"\n🗜️  Анализ сжатия:")
            print(f"   Экспериментов со сжатием: {len(compressed_results)}")

            avg_compression_ratio = sum(
                r.compression_result.compression_ratio for r in compressed_results
            ) / len(compressed_results)

            print(f"   Средний коэффициент сжатия: {avg_compression_ratio:.2f}")

            # Compare strategies
            strategies = {}
            for r in compressed_results:
                strategy = r.compression_result.strategy_used
                if strategy not in strategies:
                    strategies[strategy] = []
                strategies[strategy].append(r.compression_result.compression_ratio)

            print(f"   Стратегии сжатия:")
            for strategy, ratios in strategies.items():
                avg_ratio = sum(ratios) / len(ratios)
                print(
                    f"     {strategy}: {avg_ratio:.2f} (экспериментов: {len(ratios)})"
                )

        # Performance analysis
        print(f"\n⚡ Анализ производительности:")
        fastest_result = min(results, key=lambda r: r.response_time)
        slowest_result = max(results, key=lambda r: r.response_time)

        print(
            f"   Самый быстрый ответ: {fastest_result.experiment_name} ({fastest_result.response_time:.2f} сек)"
        )
        print(
            f"   Самый медленный ответ: {slowest_result.experiment_name} ({slowest_result.response_time:.2f} сек)"
        )
        print(
            f"   Разница во времени: {slowest_result.response_time - fastest_result.response_time:.2f} сек"
        )

    def print_recommendations(self, results: List[ExperimentResult]) -> None:
        """
        Print recommendations based on experiment results.

        Args:
            results: List of experiment results to analyze
        """
        if not results:
            print("\n❌ Нет результатов для рекомендаций")
            return

        print("\n" + "=" * 80)
        print("💡 РЕКОМЕНДАЦИИ")
        print("=" * 80)

        # Performance recommendations
        fastest_result = min(results, key=lambda r: r.response_time)
        slowest_result = max(results, key=lambda r: r.response_time)

        print(f"\n⚡ Производительность:")
        print(
            f"   Самый быстрый ответ: {fastest_result.experiment_name} ({fastest_result.response_time:.2f} сек)"
        )
        print(
            f"   Самый медленный ответ: {slowest_result.experiment_name} ({slowest_result.response_time:.2f} сек)"
        )

        # Compression recommendations
        compressed_results = [r for r in results if r.compression_applied]
        if compressed_results:
            best_compression = min(
                compressed_results, key=lambda r: r.compression_result.compression_ratio
            )
            print(f"\n🗜️  Сжатие:")
            print(
                f"   Лучшее сжатие: {best_compression.experiment_name} (коэффициент: {best_compression.compression_result.compression_ratio:.2f})"
            )
            print(f"   Стратегия: {best_compression.compression_result.strategy_used}")

        # General recommendations
        print(f"\n🎯 Общие рекомендации:")

        # Check if any experiments exceeded limits
        exceeded_limit = any(
            r.input_tokens > 8192 for r in results if r.model_name == "starcoder"
        )

        if exceeded_limit:
            print(f"   ⚠️  Обнаружены запросы, превышающие лимиты модели")
            print(f"   💡 Используйте сжатие для запросов >8192 токенов")

        # Compression strategy recommendations
        truncation_results = [
            r
            for r in compressed_results
            if r.compression_result
            and r.compression_result.strategy_used == "truncation"
        ]
        keyword_results = [
            r
            for r in compressed_results
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
                print(f"   💡 Стратегия 'truncation' лучше сохраняет контекст")
            else:
                print(f"   💡 Стратегия 'keywords' лучше для поиска информации")

        print(f"   💡 Мониторьте время ответа при больших запросах")
        print(f"   💡 Используйте сжатие для оптимизации использования токенов")

    def print_compression_comparison(self, results: List[ExperimentResult]) -> None:
        """
        Print detailed comparison of compression strategies.

        Args:
            results: List of experiment results to compare
        """
        compressed_results = [r for r in results if r.compression_applied]

        if not compressed_results:
            print("\n❌ Нет экспериментов со сжатием для сравнения")
            return

        print("\n" + "=" * 80)
        print("🔄 СРАВНЕНИЕ СТРАТЕГИЙ СЖАТИЯ")
        print("=" * 80)

        strategies = {}
        for r in compressed_results:
            strategy = r.compression_result.strategy_used
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(r)

        for strategy, strategy_results in strategies.items():
            print(f"\n📋 Стратегия: {strategy}")
            print(f"   Количество экспериментов: {len(strategy_results)}")

            avg_compression_ratio = sum(
                r.compression_result.compression_ratio for r in strategy_results
            ) / len(strategy_results)

            avg_response_time = sum(r.response_time for r in strategy_results) / len(
                strategy_results
            )
            avg_output_length = sum(len(r.response) for r in strategy_results) / len(
                strategy_results
            )

            print(f"   Средний коэффициент сжатия: {avg_compression_ratio:.2f}")
            print(f"   Среднее время ответа: {avg_response_time:.2f} сек")
            print(f"   Средняя длина ответа: {avg_output_length:.0f} символов")

            # Show example of compressed text
            if strategy_results:
                example = strategy_results[0]
                print(f"   Пример сжатого текста:")
                preview = example.compression_result.compressed_text[:150] + "..."
                print(f"     {preview}")

    def print_model_performance(self, results: List[ExperimentResult]) -> None:
        """
        Print model performance analysis.

        Args:
            results: List of experiment results to analyze
        """
        if not results:
            print("\n❌ Нет результатов для анализа производительности модели")
            return

        print("\n" + "=" * 80)
        print("🤖 ПРОИЗВОДИТЕЛЬНОСТЬ МОДЕЛИ")
        print("=" * 80)

        # Group by model
        models = {}
        for r in results:
            if r.model_name not in models:
                models[r.model_name] = []
            models[r.model_name].append(r)

        for model_name, model_results in models.items():
            print(f"\n🔧 Модель: {model_name}")
            print(f"   Количество экспериментов: {len(model_results)}")

            avg_response_time = sum(r.response_time for r in model_results) / len(
                model_results
            )
            avg_input_tokens = sum(r.input_tokens for r in model_results) / len(
                model_results
            )
            avg_output_tokens = sum(r.output_tokens for r in model_results) / len(
                model_results
            )

            print(f"   Среднее время ответа: {avg_response_time:.2f} сек")
            print(f"   Средние входные токены: {avg_input_tokens:.0f}")
            print(f"   Средние выходные токены: {avg_output_tokens:.0f}")
            print(
                f"   Скорость генерации: {avg_output_tokens/avg_response_time:.1f} токенов/сек"
            )

            # Check for errors or issues
            failed_experiments = [r for r in model_results if not r.response]
            if failed_experiments:
                print(f"   ⚠️  Неудачных экспериментов: {len(failed_experiments)}")
            else:
                print(f"   ✅ Все эксперименты успешны")
