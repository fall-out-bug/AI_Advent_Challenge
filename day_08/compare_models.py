"""
Model comparison script for testing multiple models.

This script compares StarCoder, Mistral, and Qwen models
with automatic Docker container management.
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
from core.text_compressor import SimpleTextCompressor
from core.experiments import TokenLimitExperiments
from utils.console_reporter import ConsoleReporter


async def main():
    """Compare StarCoder, Mistral, and Qwen models."""
    
    print("🔬 Сравнение моделей: StarCoder vs Mistral vs Qwen")
    print("="*60)
    
    # Configuration
    token_mode = os.getenv("TOKEN_COUNTER_MODE", "accurate")
    limit_profile = LimitProfile(os.getenv("LIMIT_PROFILE", "practical"))
    auto_swap = os.getenv("AUTO_SWAP_MODELS", "true").lower() == "true"
    
    print(f"\n🔧 Конфигурация:")
    print(f"   Режим подсчета токенов: {token_mode}")
    print(f"   Профиль лимитов: {limit_profile.value}")
    print(f"   Автоматическое управление контейнерами: {auto_swap}")
    
    # Initialize components
    print("\n🔧 Инициализация компонентов...")
    token_counter = TokenCounter(mode=token_mode, limit_profile=limit_profile)
    text_compressor = SimpleTextCompressor(token_counter)
    model_client = UnifiedModelClient()
    reporter = ConsoleReporter()
    
    # Check Docker manager availability
    docker_manager = None
    if auto_swap:
        try:
            from utils.docker_manager import ModelDockerManager
            docker_manager = ModelDockerManager()
            print("✅ Docker менеджер инициализирован")
        except ImportError:
            print("⚠️  Docker менеджер недоступен, отключаем auto-swap")
            auto_swap = False
    
    print("✅ Компоненты инициализированы")
    
    # Models to compare
    models = ["starcoder", "mistral", "qwen"]
    
    # Test queries
    queries = [
        "Объясни принцип работы механизма внимания в трансформерах",
        "Как работает машинное обучение?",
        "Напиши простую функцию на Python для сортировки списка"
    ]
    
    print(f"\n📝 Тестовые запросы:")
    for i, query in enumerate(queries, 1):
        print(f"   {i}. {query}")
    
    # Create experimenter
    experimenter = TokenLimitExperiments(model_client, token_counter, text_compressor)
    
    all_results = []
    
    # Run experiments for each query
    for query_idx, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Тестирование запроса {query_idx}/{len(queries)}")
        print(f"📝 Запрос: {query}")
        print(f"{'='*60}")
        
        # Check which models are available
        available_models = []
        for model in models:
            is_available = await model_client.check_availability(model)
            if is_available:
                available_models.append(model)
                print(f"✅ {model} доступен")
            else:
                print(f"❌ {model} недоступен")
        
        if not available_models:
            print("❌ Нет доступных моделей для тестирования")
            continue
        
        # Run comparison experiment
        try:
            results = await experimenter.run_model_comparison_experiment(
                models=available_models,
                query=query,
                auto_swap=auto_swap
            )
            
            # Add query info to results
            for result in results:
                result.experiment_name = f"query_{query_idx}_{result.experiment_name}"
            
            all_results.extend(results)
            
            print(f"✅ Запрос {query_idx} протестирован с {len(results)} моделями")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании запроса {query_idx}: {e}")
    
    # Generate comprehensive reports
    if all_results:
        print(f"\n📊 Генерация отчетов для {len(all_results)} экспериментов...")
        
        reporter.print_experiment_summary(all_results)
        reporter.print_detailed_analysis(all_results)
        reporter.print_recommendations(all_results)
        reporter.print_model_performance(all_results)
        reporter.print_final_statistics(all_results)
        
        # Model-specific analysis
        print(f"\n🔍 Анализ по моделям:")
        for model in models:
            model_results = [r for r in all_results if r.model_name == model]
            if model_results:
                avg_time = sum(r.response_time for r in model_results) / len(model_results)
                avg_tokens = sum(r.total_tokens for r in model_results) / len(model_results)
                print(f"   {model}: {len(model_results)} экспериментов, "
                      f"среднее время: {avg_time:.2f}с, средние токены: {avg_tokens:.0f}")
        
        print("✅ Все отчеты сгенерированы!")
    else:
        print("❌ Нет результатов для анализа")
    
    print("\n🎉 Сравнение моделей завершено!")


if __name__ == "__main__":
    asyncio.run(main())
