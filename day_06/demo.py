#!/usr/bin/env python3
"""
Демонстрационный скрипт для тестирования локальных моделей.

Этот скрипт показывает, как использовать систему тестирования
локальных моделей на логических загадках.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import ModelTester
from riddles import RiddleCollection
from model_client import LocalModelClient


async def demo_riddle_collection():
    """Демонстрация коллекции загадок."""
    print("🧩 Демонстрация коллекции загадок")
    print("=" * 50)
    
    collection = RiddleCollection()
    riddles = collection.get_riddles()
    
    for i, riddle in enumerate(riddles, 1):
        print(f"\n{i}. {riddle.title}")
        print(f"   Сложность: {riddle.difficulty}/5")
        print(f"   Текст: {riddle.text[:100]}...")
    
    print(f"\nВсего загадок: {len(riddles)}")


async def demo_model_client():
    """Демонстрация клиента для работы с моделями."""
    print("\n🤖 Демонстрация клиента для работы с моделями")
    print("=" * 50)
    
    client = LocalModelClient(timeout=5.0)
    
    try:
        # Проверяем доступность моделей
        print("Проверка доступности моделей...")
        availability = await client.check_model_availability()
        
        for model_name, is_available in availability.items():
            status = "✅ Доступна" if is_available else "❌ Недоступна"
            print(f"  {model_name}: {status}")
        
        # Если есть доступные модели, тестируем одну загадку
        available_models = [name for name, available in availability.items() if available]
        
        if available_models:
            print(f"\nТестирование модели {available_models[0]} на простой загадке...")
            collection = RiddleCollection()
            simple_riddle = collection.get_riddle_by_difficulty(1)[0]
            
            result = await client.test_riddle(simple_riddle.text, available_models[0])
            
            print(f"\nРезультат тестирования:")
            print(f"  Модель: {result.model_name}")
            print(f"  Прямой ответ: {result.direct_answer[:100]}...")
            print(f"  Пошаговый ответ: {result.stepwise_answer[:100]}...")
            print(f"  Время прямого ответа: {result.direct_response_time:.2f}s")
            print(f"  Время пошагового ответа: {result.stepwise_response_time:.2f}s")
        else:
            print("\n⚠️  Нет доступных моделей для тестирования")
            print("Убедитесь, что локальные модели запущены:")
            print("  cd ../local_models && docker-compose up -d")
    
    finally:
        await client.close()


async def demo_full_testing():
    """Демонстрация полного тестирования."""
    print("\n🚀 Демонстрация полного тестирования")
    print("=" * 50)
    
    tester = ModelTester()
    
    try:
        print("Запуск полного цикла тестирования...")
        await tester.run_tests()
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        print("Убедитесь, что локальные модели запущены:")
        print("  cd ../local_models && docker-compose up -d")


async def main():
    """Главная функция демонстрации."""
    print("🧠 Демонстрация системы тестирования локальных моделей")
    print("=" * 60)
    
    # Демонстрация коллекции загадок
    await demo_riddle_collection()
    
    # Демонстрация клиента
    await demo_model_client()
    
    # Спрашиваем пользователя, хочет ли он запустить полное тестирование
    print("\n" + "=" * 60)
    try:
        response = input("Запустить полное тестирование всех моделей? (y/N): ").strip().lower()
        
        if response in ['y', 'yes', 'да']:
            await demo_full_testing()
        else:
            print("Полное тестирование пропущено.")
            print("Для запуска используйте: make run")
    except EOFError:
        # Если ввод недоступен (например, в неинтерактивном режиме)
        print("Полное тестирование пропущено (неинтерактивный режим).")
        print("Для запуска используйте: make run")


if __name__ == "__main__":
    asyncio.run(main())
