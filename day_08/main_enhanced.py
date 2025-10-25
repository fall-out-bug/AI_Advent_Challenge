"""
Enhanced main entry point for the token analysis system.

This module provides the main function that orchestrates all components
with ML service integration and hybrid token counting.
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
    Enhanced main function with ML service integration.
    
    Supports configuration via environment variables and provides
    hybrid token counting with ML service fallback.
    """
    
    print("🚀 Запуск расширенной системы анализа токенов")
    print("="*60)
    
    # Read configuration from environment
    token_mode = os.getenv("TOKEN_COUNTER_MODE", "hybrid")
    limit_profile_str = os.getenv("LIMIT_PROFILE", "practical")
    
    try:
        limit_profile = LimitProfile(limit_profile_str)
    except ValueError:
        print(f"⚠️  Неверный профиль лимитов: {limit_profile_str}, используем practical")
        limit_profile = LimitProfile.PRACTICAL
    
    print(f"\n🔧 Конфигурация:")
    print(f"   Режим подсчета токенов: {token_mode}")
    print(f"   Профиль лимитов: {limit_profile.value}")
    
    print("\n🔧 Инициализация компонентов...")
    
    # Initialize ML service client
    ml_client = TokenAnalysisClient()
    
    # Initialize fallback counter
    fallback_counter = TokenCounter(mode="simple", limit_profile=limit_profile)
    
    # Initialize hybrid counter
    token_counter = HybridTokenCounter(ml_client, fallback_counter)
    
    # Check ML service availability
    try:
        health = await ml_client.health_check()
        print(f"✅ ML сервис доступен! Модели: {health.get('available_models', [])}")
        ml_service_available = True
    except Exception as e:
        print(f"⚠️  ML сервис недоступен: {e}")
        print("💡 Запустите ML сервис: make docker-run")
        ml_service_available = False
    
    # Initialize text compressor
    if ml_service_available and token_mode == "hybrid":
        # Use advanced compressor with ML service
        text_compressor = AdvancedTextCompressor(token_counter, None)  # No model_client for now
    else:
        # Use simple compressor
        text_compressor = SimpleTextCompressor(token_counter)
    
    model_client = UnifiedModelClient()
    reporter = ConsoleReporter()
    print("✅ Компоненты инициализированы")
    
    # Проверка доступности StarCoder
    print("\n🔍 Проверка доступности StarCoder...")
    is_available = await model_client.check_availability("starcoder")
    
    if not is_available:
        print("❌ StarCoder недоступен!")
        print("💡 Запустите: cd ../local_models && docker-compose up -d starcoder-chat")
        return
    
    print("✅ StarCoder доступен!")
    
    print("\n🧪 Создание экспериментатора...")
    # Создание экспериментатора
    experimenter = TokenLimitExperiments(model_client, token_counter, text_compressor)
    print("✅ Экспериментатор создан")
    
    # Выбор типа экспериментов
    print("\n🎯 Выберите тип экспериментов:")
    print("1. Базовые эксперименты с превышением лимитов")
    print("2. Продвинутые стратегии сжатия")
    print("3. Сравнение моделей (StarCoder, Mistral, Qwen)")
    print("4. Тест точного подсчета токенов")
    
    choice = input("\nВведите номер (1-4) или нажмите Enter для базовых: ").strip()
    
    try:
        if choice == "2":
            # Advanced compression experiments
            print("\n🧪 Запуск экспериментов с продвинутыми стратегиями сжатия...")
            strategies = ["truncation", "keywords", "extractive", "semantic"]
            results = await experimenter.run_advanced_compression_experiment(
                model_name="starcoder",
                strategies=strategies
            )
        elif choice == "3":
            # Model comparison
            print("\n🧪 Запуск сравнения моделей...")
            models = ["starcoder", "mistral", "qwen"]
            query = "Объясни принцип работы механизма внимания в трансформерах"
            results = await experimenter.run_model_comparison_experiment(
                models=models,
                query=query,
                auto_swap=True
            )
        elif choice == "4":
            # Token counting test
            print("\n🧪 Тест точного подсчета токенов...")
            test_texts = [
                "Hello world",
                "This is a longer text with multiple words to test token counting accuracy",
                "Детально объясни архитектуру трансформеров в машинном обучении"
            ]
            
            print("\n📊 Сравнение методов подсчета токенов:")
            for text in test_texts:
                print(f"\nТекст: {text[:50]}...")
                
                # Simple estimation
                simple_result = fallback_counter.count_tokens(text, "starcoder")
                print(f"   Простая оценка: {simple_result.count} токенов")
                
                # Accurate counting (if ML service available)
                if ml_service_available:
                    try:
                        accurate_result = await token_counter.count_tokens(text, "starcoder")
                        print(f"   Точный подсчет: {accurate_result.count} токенов")
                        print(f"   Разница: {abs(accurate_result.count - simple_result.count)} токенов")
                    except Exception as e:
                        print(f"   Ошибка точного подсчета: {e}")
                else:
                    print("   Точный подсчет недоступен (ML сервис не запущен)")
            
            print("\n✅ Тест подсчета токенов завершен!")
            return
        else:
            # Basic experiments (default)
            print("\n🧪 Запуск базовых экспериментов с превышением лимитов...")
            results = await experimenter.run_limit_exceeded_experiment("starcoder")
        
        if not results:
            print("❌ Не удалось получить результаты экспериментов")
            return
        
        print(f"✅ Получено {len(results)} результатов экспериментов")
        
        # Генерация отчетов
        print("\n📊 Генерация отчетов...")
        reporter.print_experiment_summary(results)
        reporter.print_detailed_analysis(results)
        reporter.print_recommendations(results)
        reporter.print_model_performance(results)
        reporter.print_final_statistics(results)
        print("✅ Все отчеты сгенерированы!")
        
        print("\n🎉 Эксперименты завершены успешно!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Эксперименты прерваны пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка во время экспериментов: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await token_counter.close()
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
