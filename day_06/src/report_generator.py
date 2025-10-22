"""
Генератор отчетов для тестирования локальных моделей.

Создает Markdown отчеты с результатами тестирования моделей на загадках.
"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

# Используем абсолютные импорты для работы как скрипт
try:
    from .model_client import ModelTestResult
    from .riddles import RiddleAnalyzer
except ImportError:
    # Если относительные импорты не работают, используем абсолютные
    from model_client import ModelTestResult
    from riddles import RiddleAnalyzer


@dataclass
class ComparisonResult:
    """Результат сравнения ответов модели."""
    riddle_title: str
    model_name: str
    direct_answer: str
    stepwise_answer: str
    word_difference: int
    direct_analysis: Dict
    stepwise_analysis: Dict
    direct_response_time: float
    stepwise_response_time: float
    riddle_text: str = ""


class ReportGenerator:
    """Генератор отчетов о тестировании моделей."""
    
    def __init__(self):
        """Инициализация генератора отчетов."""
        self.analyzer = RiddleAnalyzer()
    
    def generate_comparison_results(
        self, 
        test_results: List[ModelTestResult],
        riddle_titles: List[str],
        riddle_texts: List[str] = None
    ) -> List[ComparisonResult]:
        """
        Генерация результатов сравнения.
        
        Args:
            test_results: Результаты тестирования
            riddle_titles: Названия загадок
            riddle_texts: Тексты загадок (опционально)
            
        Returns:
            List[ComparisonResult]: Результаты сравнения
        """
        comparison_results = []
        
        for i, result in enumerate(test_results):
            # Анализ прямого ответа
            direct_analysis = self.analyzer.analyze_response(result.direct_answer)
            
            # Анализ пошагового ответа
            stepwise_analysis = self.analyzer.analyze_response(result.stepwise_answer)
            
            # Вычисление разницы в словах
            word_difference = stepwise_analysis["word_count"] - direct_analysis["word_count"]
            
            # Получаем текст загадки, если доступен
            riddle_text = ""
            if riddle_texts and i < len(riddle_texts):
                riddle_text = riddle_texts[i % len(riddle_texts)]
            
            comparison_result = ComparisonResult(
                riddle_title=riddle_titles[i % len(riddle_titles)],
                model_name=result.model_name,
                direct_answer=result.direct_answer,
                stepwise_answer=result.stepwise_answer,
                word_difference=word_difference,
                direct_analysis=direct_analysis,
                stepwise_analysis=stepwise_analysis,
                direct_response_time=result.direct_response_time,
                stepwise_response_time=result.stepwise_response_time,
                riddle_text=riddle_text
            )
            
            comparison_results.append(comparison_result)
        
        return comparison_results
    
    def generate_markdown_report(
        self, 
        comparison_results: List[ComparisonResult]
    ) -> str:
        """
        Генерация Markdown отчета.
        
        Args:
            comparison_results: Результаты сравнения
            
        Returns:
            str: Markdown отчет
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Тест моделей на логических загадках

**Дата тестирования:** {timestamp}

## Общая статистика

- **Общее количество тестов:** {len(comparison_results)}
- **Количество моделей:** {len(set(r.model_name for r in comparison_results))}
- **Количество загадок:** {len(set(r.riddle_title for r in comparison_results))}

"""
        
        # Добавляем детальный анализ
        report += self._generate_detailed_analysis(comparison_results)
        
        # Добавляем статистику
        report += self._generate_statistics(comparison_results)
        
        return report
    
    def _generate_detailed_analysis(self, results: List[ComparisonResult]) -> str:
        """Генерация детального анализа."""
        analysis = "\n## Детальный анализ\n\n"
        
        for result in results:
            analysis += f"### {result.riddle_title} - {result.model_name}\n\n"
            
            # Добавляем текст загадки, если доступен
            if result.riddle_text:
                analysis += f"**Загадка:**\n{result.riddle_text}\n\n"
            
            # Анализ прямого ответа
            analysis += "**Прямой ответ:**\n"
            analysis += f"- Количество слов: {result.direct_analysis['word_count']}\n"
            analysis += f"- Логические ключевые слова: {result.direct_analysis['logical_keywords_count']}\n"
            analysis += f"- Пошаговая структура: {'Да' if result.direct_analysis['has_step_by_step'] else 'Нет'}\n"
            analysis += f"- Время ответа: {result.direct_response_time:.2f}s\n\n"
            
            # Анализ пошагового ответа
            analysis += "**Пошаговый ответ:**\n"
            analysis += f"- Количество слов: {result.stepwise_analysis['word_count']}\n"
            analysis += f"- Логические ключевые слова: {result.stepwise_analysis['logical_keywords_count']}\n"
            analysis += f"- Пошаговая структура: {'Да' if result.stepwise_analysis['has_step_by_step'] else 'Нет'}\n"
            analysis += f"- Время ответа: {result.stepwise_response_time:.2f}s\n"
            analysis += f"- Разница в словах: {result.word_difference:+d}\n\n"
            
            # Полные ответы
            analysis += "**Полные ответы:**\n\n"
            analysis += f"*Прямой:*\n```\n{result.direct_answer}\n```\n\n"
            analysis += f"*Пошаговый:*\n```\n{result.stepwise_answer}\n```\n\n"
            analysis += "---\n\n"
        
        return analysis
    
    def _generate_statistics(self, results: List[ComparisonResult]) -> str:
        """Генерация статистики."""
        if not results:
            return ""
        
        # Статистика по моделям
        models = set(result.model_name for result in results)
        model_stats = {}
        
        for model in models:
            model_results = [r for r in results if r.model_name == model]
            avg_word_diff = sum(r.word_difference for r in model_results) / len(model_results)
            avg_direct_time = sum(r.direct_response_time for r in model_results) / len(model_results)
            avg_stepwise_time = sum(r.stepwise_response_time for r in model_results) / len(model_results)
            
            model_stats[model] = {
                "avg_word_diff": avg_word_diff,
                "avg_direct_time": avg_direct_time,
                "avg_stepwise_time": avg_stepwise_time,
                "total_tests": len(model_results)
            }
        
        stats = "## Статистика\n\n"
        
        # Общая статистика
        total_word_diff = sum(r.word_difference for r in results)
        avg_word_diff = total_word_diff / len(results)
        avg_direct_time = sum(r.direct_response_time for r in results) / len(results)
        avg_stepwise_time = sum(r.stepwise_response_time for r in results) / len(results)
        
        stats += f"- **Общее количество тестов:** {len(results)}\n"
        stats += f"- **Средняя разница в словах:** {avg_word_diff:.1f}\n"
        stats += f"- **Среднее время прямого ответа:** {avg_direct_time:.2f}s\n"
        stats += f"- **Среднее время пошагового ответа:** {avg_stepwise_time:.2f}s\n\n"
        
        # Статистика по моделям
        stats += "### Статистика по моделям\n\n"
        for model, stat in model_stats.items():
            stats += f"**{model}:**\n"
            stats += f"- Количество тестов: {stat['total_tests']}\n"
            stats += f"- Средняя разница в словах: {stat['avg_word_diff']:.1f}\n"
            stats += f"- Среднее время прямого ответа: {stat['avg_direct_time']:.2f}s\n"
            stats += f"- Среднее время пошагового ответа: {stat['avg_stepwise_time']:.2f}s\n\n"
        
        return stats
    
    def save_report(self, report: str, filename: str = None) -> str:
        """
        Сохранение отчета в файл.
        
        Args:
            report: Текст отчета
            filename: Имя файла (опционально)
            
        Returns:
            str: Путь к сохраненному файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"model_test_report_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename
