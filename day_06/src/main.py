"""
Основной модуль для тестирования локальных моделей на логических загадках.

Координирует весь процесс тестирования: проверку доступности моделей,
запуск тестов, анализ результатов и генерацию отчетов.
"""

import asyncio
import sys
from typing import List

# Используем абсолютные импорты для работы как скрипт
try:
    from .model_client import LocalModelClient
    from .riddles import RiddleCollection
    from .report_generator import ReportGenerator
except ImportError:
    # Если относительные импорты не работают, используем абсолютные
    from model_client import LocalModelClient
    from riddles import RiddleCollection
    from report_generator import ReportGenerator


class ModelTester:
    """Основной класс для тестирования моделей."""
    
    def __init__(self):
        """Инициализация тестера."""
        self.client = LocalModelClient()
        self.riddle_collection = RiddleCollection()
        self.report_generator = ReportGenerator()
    
    async def run_tests(self) -> None:
        """
        Запуск полного цикла тестирования.
        
        Выполняет проверку доступности моделей, тестирование на загадках
        и генерацию отчета.
        """
        print("🧠 Тестирование локальных моделей на логических загадках")
        print("=" * 60)
        
        try:
            # Проверка доступности моделей
            await self._check_model_availability()
            
            # Получение загадок
            riddles = self.riddle_collection.get_riddles()
            riddle_texts = self.riddle_collection.get_riddle_texts()
            riddle_titles = [riddle.title for riddle in riddles]
            
            print(f"\n📝 Найдено {len(riddles)} загадок для тестирования:")
            for i, riddle in enumerate(riddles, 1):
                print(f"  {i}. {riddle.title} (сложность: {riddle.difficulty}/5)")
            
            # Запуск тестов
            print(f"\n🚀 Запуск тестирования...")
            test_results = await self.client.test_all_models(riddle_texts)
            
            if not test_results:
                print("❌ Не удалось получить результаты тестирования")
                return
            
            print(f"✅ Получено {len(test_results)} результатов тестирования")
            
            # Генерация отчета
            print("\n📊 Генерация отчета...")
            comparison_results = self.report_generator.generate_comparison_results(
                test_results, riddle_titles, riddle_texts
            )
            
            report = self.report_generator.generate_markdown_report(comparison_results)
            report_filename = self.report_generator.save_report(report)
            
            print(f"✅ Отчет сохранен в файл: {report_filename}")
            
            # Вывод краткой сводки в консоль
            self._print_console_summary(comparison_results)
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении тестирования: {e}")
            sys.exit(1)
        
        finally:
            await self.client.close()
    
    async def _check_model_availability(self) -> None:
        """Проверка доступности всех моделей."""
        print("\n🔍 Проверка доступности моделей...")
        
        availability = await self.client.check_model_availability()
        
        available_models = []
        for model_name, is_available in availability.items():
            status = "✅ Доступна" if is_available else "❌ Недоступна"
            print(f"  {model_name}: {status}")
            
            if is_available:
                available_models.append(model_name)
        
        if not available_models:
            print("\n❌ Ни одна модель не доступна!")
            print("Убедитесь, что локальные модели запущены:")
            print("  cd ../local_models && docker-compose up -d")
            sys.exit(1)
        
        print(f"\n✅ Доступно моделей: {len(available_models)}")
    
    def _print_console_summary(self, results: List) -> None:
        """Вывод краткой сводки результатов в консоль."""
        print("\n" + "=" * 60)
        print("📋 КРАТКАЯ СВОДКА РЕЗУЛЬТАТОВ")
        print("=" * 60)
        
        # Группировка по моделям
        models = {}
        for result in results:
            if result.model_name not in models:
                models[result.model_name] = []
            models[result.model_name].append(result)
        
        for model_name, model_results in models.items():
            print(f"\n🤖 Модель: {model_name}")
            print("-" * 40)
            
            avg_word_diff = sum(r.word_difference for r in model_results) / len(model_results)
            avg_direct_time = sum(r.direct_response_time for r in model_results) / len(model_results)
            avg_stepwise_time = sum(r.stepwise_response_time for r in model_results) / len(model_results)
            
            print(f"  Средняя разница в словах: {avg_word_diff:.1f}")
            print(f"  Среднее время прямого ответа: {avg_direct_time:.2f}s")
            print(f"  Среднее время пошагового ответа: {avg_stepwise_time:.2f}s")
            
            # Анализ качества рассуждений
            stepwise_with_logic = sum(
                1 for r in model_results 
                if r.stepwise_analysis['has_logical_keywords']
            )
            stepwise_with_structure = sum(
                1 for r in model_results 
                if r.stepwise_analysis['has_step_by_step']
            )
            
            print(f"  Пошаговые ответы с логикой: {stepwise_with_logic}/{len(model_results)}")
            print(f"  Пошаговые ответы со структурой: {stepwise_with_structure}/{len(model_results)}")
        
        print("\n" + "=" * 60)
        print("🎯 ВЫВОДЫ:")
        print("=" * 60)
        
        # Общие выводы
        total_results = len(results)
        if total_results == 0:
            print("Нет результатов для анализа")
            return
            
        avg_word_diff = sum(r.word_difference for r in results) / total_results
        
        if avg_word_diff > 0:
            print(f"✅ Пошаговые ответы в среднем длиннее на {avg_word_diff:.1f} слов")
        else:
            print(f"⚠️  Пошаговые ответы не всегда длиннее прямых")
        
        # Анализ логических рассуждений
        stepwise_with_logic = sum(
            1 for r in results 
            if r.stepwise_analysis['has_logical_keywords']
        )
        logic_percentage = (stepwise_with_logic / total_results) * 100
        
        print(f"📊 {logic_percentage:.1f}% пошаговых ответов содержат логические ключевые слова")
        
        print("\n📄 Подробный отчет сохранен в Markdown файл")


async def main():
    """Главная функция для запуска тестирования."""
    tester = ModelTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
