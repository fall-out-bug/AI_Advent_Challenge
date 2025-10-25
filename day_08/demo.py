"""
Demo script for the token analysis system.

This module provides simple usage examples and demonstrations
of the token counting and compression functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from core.text_compressor import SimpleTextCompressor
from core.token_analyzer import SimpleTokenCounter
from utils.console_reporter import ConsoleReporter


async def demo_token_counting():
    """
    Demonstrate token counting functionality.
    """
    print("🔢 Демонстрация подсчета токенов")
    print("=" * 40)

    token_counter = SimpleTokenCounter()

    # Test different texts
    test_texts = [
        "Привет, как дела?",
        "Объясни принцип работы нейронных сетей в машинном обучении.",
        "Детально объясни архитектуру трансформеров, включая механизм внимания, multi-head attention, positional encoding, feed-forward networks, layer normalization, residual connections, практические применения, примеры кода на Python, оптимизации и современные варианты.",
    ]

    for i, text in enumerate(test_texts, 1):
        token_info = token_counter.count_tokens(text)
        print(f"\n📝 Текст {i}: {text[:50]}...")
        print(f"   Токенов: {token_info.count}")
        print(f"   Слов: {len(text.split())}")
        print(f"   Коэффициент: {token_info.count / len(text.split()):.2f}")

        # Check limits
        for model_name in ["starcoder", "tinyllama"]:
            limits = token_counter.get_model_limits(model_name)
            exceeds = token_counter.check_limit_exceeded(text, model_name)
            print(
                f"   {model_name}: {'❌ Превышен' if exceeds else '✅ В пределах'} (лимит: {limits.max_input_tokens})"
            )


async def demo_text_compression():
    """
    Demonstrate text compression functionality.
    """
    print("\n🗜️  Демонстрация сжатия текста")
    print("=" * 40)

    token_counter = SimpleTokenCounter()
    text_compressor = SimpleTextCompressor(token_counter)

    # Long text that exceeds limits
    long_text = (
        """
    Детально объясни архитектуру трансформеров в машинном обучении. 
    Включи в ответ следующую информацию:
    
    1. Механизм внимания (attention mechanism):
    - Как работает scaled dot-product attention
    - Формула вычисления attention weights
    - Почему используется масштабирование
    - Примеры применения в разных задачах
    
    2. Multi-head attention:
    - Зачем нужны несколько голов внимания
    - Как происходит объединение результатов
    - Преимущества перед single-head attention
    - Оптимальное количество голов
    
    3. Positional encoding:
    - Как модель понимает порядок слов
    - Sinusoidal и learned positional encoding
    - Проблемы с длинными последовательностями
    - Современные подходы к позиционному кодированию
    
    4. Feed-forward networks:
    - Структура и назначение FFN слоев
    - Размеры скрытых слоев
    - Функции активации
    - Оптимизация параметров
    
    5. Layer normalization:
    - Нормализация и её роль в обучении
    - Pre-norm vs Post-norm архитектуры
    - Влияние на стабильность обучения
    - Сравнение с batch normalization
    
    6. Residual connections:
    - Зачем нужны skip connections
    - Решение проблемы vanishing gradients
    - Архитектурные варианты residual connections
    - Влияние на глубину сети
    
    7. Практические применения:
    - Где используются трансформеры
    - Примеры успешных моделей (BERT, GPT, T5)
    - Области применения (NLP, Computer Vision, etc.)
    - Ограничения и недостатки
    
    8. Примеры кода на Python:
    - Реализация attention mechanism с нуля
    - Multi-head attention на PyTorch
    - Полная архитектура трансформера
    - Обучение и инференс
    
    9. Оптимизации:
    - Как ускорить работу трансформеров
    - Квантизация и сжатие моделей
    - Эффективные attention механизмы
    - Hardware оптимизации
    
    10. Современные варианты:
    - BERT и его особенности
    - GPT серия моделей
    - T5 и text-to-text подход
    - Vision Transformers (ViT)
    - Efficient Transformers
    
    Пожалуйста, дай максимально подробный и технический ответ с примерами кода и математическими формулами.
    """
        * 2
    )  # Make it even longer

    print(f"📝 Исходный текст: {len(long_text)} символов")

    original_tokens = token_counter.count_tokens(long_text).count
    print(f"📊 Исходные токены: {original_tokens}")

    # Test compression strategies
    target_tokens = 1000  # Target for compression

    print(f"\n🎯 Целевые токены: {target_tokens}")

    # Truncation compression
    print(f"\n✂️  Сжатие через обрезку:")
    truncation_result = text_compressor.compress_by_truncation(long_text, target_tokens)
    print(f"   Коэффициент сжатия: {truncation_result.compression_ratio:.2f}")
    print(f"   Сжатые токены: {truncation_result.compressed_tokens}")
    print(f"   Превью: {truncation_result.compressed_text[:200]}...")

    # Keywords compression
    print(f"\n🔑 Сжатие через ключевые слова:")
    keywords_result = text_compressor.compress_by_keywords(long_text, target_tokens)
    print(f"   Коэффициент сжатия: {keywords_result.compression_ratio:.2f}")
    print(f"   Сжатые токены: {keywords_result.compressed_tokens}")
    print(f"   Превью: {keywords_result.compressed_text[:200]}...")

    # Compare strategies
    print(f"\n📊 Сравнение стратегий:")
    print(
        f"   Обрезка: {truncation_result.compression_ratio:.2f} (лучше сохраняет контекст)"
    )
    print(
        f"   Ключевые слова: {keywords_result.compression_ratio:.2f} (лучше для поиска)"
    )


async def demo_model_interaction():
    """
    Demonstrate interaction with StarCoder model.
    """
    print("\n🤖 Демонстрация взаимодействия с моделью")
    print("=" * 40)

    try:
        model_client = UnifiedModelClient()
        token_counter = SimpleTokenCounter()

        # Check availability
        print("🔍 Проверка доступности StarCoder...")
        is_available = await model_client.check_availability("starcoder")

        if not is_available:
            print("❌ StarCoder недоступен!")
            print(
                "💡 Запустите: cd ../local_models && docker-compose up -d starcoder-chat"
            )
            return

        print("✅ StarCoder доступен!")

        # Test with short query
        short_query = "Объясни что такое машинное обучение в одном предложении."
        print(f"\n📝 Короткий запрос: {short_query}")

        input_tokens = token_counter.count_tokens(short_query).count
        print(f"📊 Входные токены: {input_tokens}")

        response = await model_client.make_request(
            model_name="starcoder", prompt=short_query, max_tokens=100, temperature=0.7
        )

        output_tokens = token_counter.count_tokens(response.response).count
        print(f"📊 Выходные токены: {output_tokens}")
        print(f"📊 Общие токены: {input_tokens + output_tokens}")
        print(f"⏱️  Время ответа: {response.response_time:.2f} сек")
        print(f"📝 Ответ: {response.response}")

    except Exception as e:
        print(f"❌ Ошибка при взаимодействии с моделью: {e}")


async def demo_full_workflow():
    """
    Demonstrate the full workflow with compression.
    """
    print("\n🔄 Демонстрация полного рабочего процесса")
    print("=" * 40)

    try:
        model_client = UnifiedModelClient()
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)

        # Check availability
        is_available = await model_client.check_availability("starcoder")
        if not is_available:
            print("❌ StarCoder недоступен!")
            return

        # Create a query that exceeds limits
        long_query = (
            """
        Детально объясни архитектуру трансформеров в машинном обучении, 
        включая механизм внимания, multi-head attention, positional encoding, 
        feed-forward networks, layer normalization, residual connections, 
        практические применения, примеры кода на Python, оптимизации и 
        современные варианты. Пожалуйста, дай максимально подробный ответ.
        """
            * 5
        )  # Make it exceed limits

        print(f"📝 Исходный запрос: {len(long_query)} символов")

        original_tokens = token_counter.count_tokens(long_query).count
        limits = token_counter.get_model_limits("starcoder")

        print(f"📊 Исходные токены: {original_tokens}")
        print(f"📊 Лимит модели: {limits.max_input_tokens}")

        if original_tokens > limits.max_input_tokens:
            print("⚠️  Превышение лимита! Применяем сжатие...")

            # Compress using truncation
            compression_result = text_compressor.compress_by_truncation(
                long_query, limits.max_input_tokens
            )

            print(f"🗜️  Коэффициент сжатия: {compression_result.compression_ratio:.2f}")
            print(f"📊 Сжатые токены: {compression_result.compressed_tokens}")

            # Send compressed query
            response = await model_client.make_request(
                model_name="starcoder",
                prompt=compression_result.compressed_text,
                max_tokens=500,
                temperature=0.7,
            )

            output_tokens = token_counter.count_tokens(response.response).count
            print(f"📊 Выходные токены: {output_tokens}")
            print(f"⏱️  Время ответа: {response.response_time:.2f} сек")
            print(f"📝 Ответ: {response.response[:200]}...")

        else:
            print("✅ Запрос в пределах лимита, сжатие не требуется")

    except Exception as e:
        print(f"❌ Ошибка в полном рабочем процессе: {e}")


async def main():
    """
    Main demo function that runs all demonstrations.
    """
    print("🎬 Демонстрация системы анализа токенов")
    print("=" * 50)

    try:
        # Run all demos
        await demo_token_counting()
        await demo_text_compression()
        await demo_model_interaction()
        await demo_full_workflow()

        print("\n✅ Все демонстрации завершены!")
        print("\n💡 Для запуска полных экспериментов используйте: python main.py")

    except KeyboardInterrupt:
        print("\n⏹️  Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка в демонстрации: {e}")


if __name__ == "__main__":
    asyncio.run(main())
