"""
Unified entry point for the token analysis system.

This module provides a single entry point that replaces multiple
main files (main.py, main_enhanced.py, demo.py) with a clean,
configurable interface.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from core.bootstrap import ApplicationBootstrapper, BootstrapError
from models.application_context import ApplicationContext
from utils.logging import LoggerFactory


async def run_experiments(context: ApplicationContext) -> None:
    """
    Run full token limit experiments.
    
    Args:
        context: Application context with all components
    """
    context.logger.info("Starting full token limit experiments")
    
    try:
        # Check StarCoder availability
        context.logger.info("Checking StarCoder availability")
        is_available = await context.ml_client.check_availability("starcoder")
        
        if not is_available:
            context.logger.error("StarCoder is not available")
            print("❌ StarCoder недоступен!")
            print("💡 Запустите: cd ../local_models && docker-compose up -d starcoder-chat")
            return
        
        context.logger.info("StarCoder is available")
        print("✅ StarCoder доступен!")
        
        # Run experiments
        context.logger.info("Running limit exceeded experiments")
        print("\n🧪 Запуск экспериментов с превышением лимитов...")
        
        results = await context.experiments.run_limit_exceeded_experiment("starcoder")
        
        if not results:
            context.logger.error("No experiment results received")
            print("❌ Не удалось получить результаты экспериментов")
            return
        
        context.logger.info(f"Received {len(results)} experiment results")
        print(f"✅ Получено {len(results)} результатов экспериментов")
        
        # Generate reports
        await _generate_reports(context, results)
        
        # Show summary
        await _show_experiment_summary(context, results)
        
        context.logger.info("Experiments completed successfully")
        print("\n🎉 Эксперименты завершены успешно!")
        
    except Exception as e:
        context.logger.error(f"Error during experiments: {e}")
        print(f"\n❌ Ошибка при выполнении экспериментов: {e}")
        raise


async def run_demo(context: ApplicationContext) -> None:
    """
    Run demo with short queries for quick testing.
    
    Args:
        context: Application context with all components
    """
    context.logger.info("Starting demo with short queries")
    
    try:
        # Check availability
        is_available = await context.ml_client.check_availability("starcoder")
        if not is_available:
            print("❌ StarCoder недоступен!")
            return
        
        # Run short query experiments
        context.logger.info("Running short query experiments")
        results = await context.experiments.run_short_query_experiment("starcoder")
        
        # Generate basic reports
        context.reporter.print_experiment_summary(results)
        context.reporter.print_detailed_analysis(results)
        context.reporter.print_recommendations(results)
        
        context.logger.info("Demo completed successfully")
        print("\n✅ Демо завершено!")
        
    except Exception as e:
        context.logger.error(f"Error during demo: {e}")
        print(f"❌ Ошибка в демо: {e}")
        raise


async def run_comparison(context: ApplicationContext) -> None:
    """
    Run model comparison experiments.
    
    Args:
        context: Application context with all components
    """
    context.logger.info("Starting model comparison experiments")
    
    try:
        # Check availability
        is_available = await context.ml_client.check_availability("starcoder")
        if not is_available:
            print("❌ StarCoder недоступен!")
            return
        
        # Run model comparison
        context.logger.info("Running model comparison")
        models = ["starcoder", "mistral", "qwen"]
        query = "Объясни принцип работы механизма внимания в трансформерах"
        
        results = await context.experiments.run_model_comparison_experiment(
            models=models,
            query=query,
            auto_swap=True
        )
        
        # Generate reports
        await _generate_reports(context, results)
        
        context.logger.info("Model comparison completed successfully")
        print("\n🎉 Сравнение моделей завершено!")
        
    except Exception as e:
        context.logger.error(f"Error during model comparison: {e}")
        print(f"❌ Ошибка при сравнении моделей: {e}")
        raise


async def run_advanced_compression(context: ApplicationContext) -> None:
    """
    Run advanced compression experiments.
    
    Args:
        context: Application context with all components
    """
    context.logger.info("Starting advanced compression experiments")
    
    try:
        # Run advanced compression experiments
        context.logger.info("Running advanced compression experiments")
        strategies = ["truncation", "keywords", "extractive", "semantic"]
        
        results = await context.experiments.run_advanced_compression_experiment(
            model_name="starcoder",
            strategies=strategies
        )
        
        # Generate reports
        await _generate_reports(context, results)
        
        context.logger.info("Advanced compression experiments completed successfully")
        print("\n🎉 Продвинутые эксперименты сжатия завершены!")
        
    except Exception as e:
        context.logger.error(f"Error during advanced compression: {e}")
        print(f"❌ Ошибка при продвинутых экспериментах: {e}")
        raise


async def _generate_reports(context: ApplicationContext, results: list) -> None:
    """
    Generate all reports for experiment results.
    
    Args:
        context: Application context
        results: Experiment results
    """
    context.logger.info("Generating reports")
    print("\n📊 Генерация отчетов...")
    
    context.reporter.print_experiment_summary(results)
    context.reporter.print_detailed_analysis(results)
    context.reporter.print_recommendations(results)
    context.reporter.print_compression_comparison(results)
    context.reporter.print_model_performance(results)
    
    context.logger.info("All reports generated")
    print("✅ Все отчеты сгенерированы!")


async def _show_experiment_summary(context: ApplicationContext, results: list) -> None:
    """
    Show experiment summary statistics.
    
    Args:
        context: Application context
        results: Experiment results
    """
    context.logger.info("Showing experiment summary")
    
    summary = context.experiments.get_experiment_summary(results)
    print(f"\n📈 Итоговая статистика:")
    print(f"   Всего экспериментов: {summary['total_experiments']}")
    print(f"   Успешных: {summary['successful_experiments']}")
    print(f"   Процент успеха: {summary['success_rate']*100:.1f}%")
    print(f"   Среднее время ответа: {summary['avg_response_time']:.2f} сек")
    print(f"   Общие токены: {summary['total_tokens_used']}")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {
        'token_counter_mode': os.getenv("TOKEN_COUNTER_MODE", "simple"),
        'limit_profile': os.getenv("LIMIT_PROFILE", "practical"),
        'ml_service_url': os.getenv("ML_SERVICE_URL", "http://localhost:8004"),
        'log_level': os.getenv("LOG_LEVEL", "INFO"),
        'debug': os.getenv("DEBUG", "false").lower() == "true"
    }
    
    return config


def print_help() -> None:
    """Print help information."""
    print("""
🚀 Система анализа токенов - Day 8

Использование:
    python run.py                    # Запуск полных экспериментов
    python run.py --demo             # Запуск демо с короткими запросами
    python run.py --comparison       # Сравнение моделей
    python run.py --advanced         # Продвинутые эксперименты сжатия
    python run.py --help             # Показать эту справку

Переменные окружения:
    TOKEN_COUNTER_MODE=simple        # Режим подсчета токенов
    LIMIT_PROFILE=practical          # Профиль лимитов (theoretical/practical)
    ML_SERVICE_URL=http://localhost:8004  # URL ML сервиса
    LOG_LEVEL=INFO                   # Уровень логирования
    DEBUG=false                      # Режим отладки

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


async def main() -> None:
    """
    Main function that orchestrates the token analysis system.
    
    Initializes all components using ApplicationBootstrapper,
    then runs the selected experiment type.
    """
    print("🚀 Запуск системы анализа токенов")
    print("="*50)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize application
        bootstrapper = ApplicationBootstrapper(config)
        context = bootstrapper.bootstrap()
        
        print("✅ Приложение инициализировано")
        print(f"📋 Конфигурация: {config}")
        
        # Determine experiment type
        experiment_type = _get_experiment_type()
        
        # Run selected experiment
        await _run_experiment(context, experiment_type)
        
    except BootstrapError as e:
        print(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Эксперименты прерваны пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        raise
    finally:
        # Cleanup
        if 'context' in locals():
            await context.cleanup()


def _get_experiment_type() -> str:
    """
    Get experiment type from command line arguments.
    
    Returns:
        str: Experiment type
    """
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--demo":
            return "demo"
        elif arg == "--comparison":
            return "comparison"
        elif arg == "--advanced":
            return "advanced"
        elif arg == "--help":
            print_help()
            sys.exit(0)
        else:
            print("❌ Неизвестный аргумент. Используйте --help для справки")
            sys.exit(1)
    
    return "full"


async def _run_experiment(context: ApplicationContext, experiment_type: str) -> None:
    """
    Run the specified experiment type.
    
    Args:
        context: Application context
        experiment_type: Type of experiment to run
    """
    if experiment_type == "demo":
        await run_demo(context)
    elif experiment_type == "comparison":
        await run_comparison(context)
    elif experiment_type == "advanced":
        await run_advanced_compression(context)
    else:  # full
        await run_experiments(context)


if __name__ == "__main__":
    asyncio.run(main())
