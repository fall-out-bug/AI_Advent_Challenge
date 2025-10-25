"""
Main entry point for the token analysis system.

This module provides the main function that orchestrates all components
to run experiments with token limits and compression strategies.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient
from core.token_analyzer import TokenCounter, LimitProfile
from core.text_compressor import SimpleTextCompressor, AdvancedTextCompressor
from core.ml_client import TokenAnalysisClient, HybridTokenCounter
from core.experiments import TokenLimitExperiments
from utils.console_reporter import ConsoleReporter


async def main():
    """
    Main function that orchestrates the token analysis system.
    
    Initializes all components, checks model availability,
    runs experiments, and generates reports.
    """
    print("🚀 Запуск системы анализа токенов")
    print("="*50)
    
    try:
        # Initialize components
        print("\n🔧 Инициализация компонентов...")
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)
        model_client = UnifiedModelClient()
        reporter = ConsoleReporter()
        
        print("✅ Компоненты инициализированы")
        
        # Check StarCoder availability
        print("\n🔍 Проверка доступности StarCoder...")
        is_available = await model_client.check_availability("starcoder")
        
        if not is_available:
            print("❌ StarCoder недоступен!")
            print("💡 Запустите: cd ../local_models && docker-compose up -d starcoder-chat")
            print("💡 Или проверьте, что сервис запущен на порту 8003")
            return
        
        print("✅ StarCoder доступен!")
        
        # Create experimenter
        print("\n🧪 Создание экспериментатора...")
        experimenter = TokenLimitExperiments(model_client, token_counter, text_compressor)
        print("✅ Экспериментатор создан")
        
        # Run limit exceeded experiments
        print("\n🧪 Запуск экспериментов с превышением лимитов...")
        results = await experimenter.run_limit_exceeded_experiment("starcoder")
        
        if not results:
            print("❌ Не удалось получить результаты экспериментов")
            return
        
        print(f"✅ Получено {len(results)} результатов экспериментов")
        
        # Generate reports
        print("\n📊 Генерация отчетов...")
        
        # Summary report
        reporter.print_experiment_summary(results)
        
        # Detailed analysis
        reporter.print_detailed_analysis(results)
        
        # Recommendations
        reporter.print_recommendations(results)
        
        # Additional analysis
        reporter.print_compression_comparison(results)
        reporter.print_model_performance(results)
        
        print("\n✅ Все отчеты сгенерированы!")
        
        # Show experiment summary
        summary = experimenter.get_experiment_summary(results)
        print(f"\n📈 Итоговая статистика:")
        print(f"   Всего экспериментов: {summary['total_experiments']}")
        print(f"   Успешных: {summary['successful_experiments']}")
        print(f"   Процент успеха: {summary['success_rate']*100:.1f}%")
        print(f"   Среднее время ответа: {summary['avg_response_time']:.2f} сек")
        print(f"   Общие токены: {summary['total_tokens_used']}")
        
        print("\n🎉 Эксперименты завершены успешно!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Эксперименты прерваны пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении экспериментов: {e}")
        print(f"💡 Проверьте, что все сервисы запущены и доступны")
        raise


async def run_short_query_demo():
    """
    Run a demo with short queries for quick testing.
    
    This function can be used for quick testing without
    running the full limit-exceeded experiments.
    """
    print("🚀 Запуск демо с короткими запросами")
    print("="*50)
    
    try:
        # Initialize components
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)
        model_client = UnifiedModelClient()
        reporter = ConsoleReporter()
        
        # Check availability
        is_available = await model_client.check_availability("starcoder")
        if not is_available:
            print("❌ StarCoder недоступен!")
            return
        
        # Run short query experiments
        experimenter = TokenLimitExperiments(model_client, token_counter, text_compressor)
        results = await experimenter.run_short_query_experiment("starcoder")
        
        # Generate reports
        reporter.print_experiment_summary(results)
        reporter.print_detailed_analysis(results)
        reporter.print_recommendations(results)
        
        print("\n✅ Демо завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка в демо: {e}")
        raise


def print_help():
    """Print help information."""
    print("""
🚀 Система анализа токенов - Day 8

Использование:
    python main.py              # Запуск полных экспериментов
    python main.py --demo       # Запуск демо с короткими запросами
    python main.py --help       # Показать эту справку

Требования:
    - StarCoder должен быть запущен (порт 8003)
    - Запуск: cd ../local_models && docker-compose up -d starcoder-chat

Эксперименты:
    1. Без сжатия - отправка длинного запроса как есть
    2. Сжатие через обрезку - сохранение начала и конца
    3. Сжатие через ключевые слова - извлечение важных слов

Результаты:
    - Подсчет токенов для всех запросов и ответов
    - Анализ эффективности сжатия
    - Рекомендации по оптимизации
    """)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            asyncio.run(run_short_query_demo())
        elif sys.argv[1] == "--help":
            print_help()
        else:
            print("❌ Неизвестный аргумент. Используйте --help для справки")
    else:
        asyncio.run(main())
