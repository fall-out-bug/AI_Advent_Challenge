"""
Unit тесты для модуля report_generator.

Тестирует функциональность генератора отчетов.
"""

import pytest
from unittest.mock import patch, mock_open

from src.report_generator import ReportGenerator, ComparisonResult
from src.model_client import ModelTestResult


class TestReportGenerator:
    """Тесты для класса ReportGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Фикстура для создания генератора отчетов."""
        return ReportGenerator()
    
    @pytest.fixture
    def sample_test_results(self):
        """Фикстура с примерными результатами тестирования."""
        return [
            ModelTestResult(
                riddle="Тестовая загадка 1",
                model_name="qwen",
                direct_answer="Прямой ответ",
                stepwise_answer="Пошаговый ответ с рассуждениями",
                direct_response_time=1.0,
                stepwise_response_time=2.0,
                direct_tokens=5,
                stepwise_tokens=10
            ),
            ModelTestResult(
                riddle="Тестовая загадка 2",
                model_name="mistral",
                direct_answer="Короткий ответ",
                stepwise_answer="Длинный пошаговый ответ с логикой",
                direct_response_time=1.5,
                stepwise_response_time=3.0,
                direct_tokens=3,
                stepwise_tokens=15
            )
        ]
    
    @pytest.fixture
    def sample_riddle_titles(self):
        """Фикстура с названиями загадок."""
        return ["Загадка 1", "Загадка 2"]
    
    def test_generator_initialization(self, generator):
        """Тест инициализации генератора."""
        assert generator.analyzer is not None
    
    def test_generate_comparison_results(self, generator, sample_test_results, sample_riddle_titles):
        """Тест генерации результатов сравнения."""
        with patch.object(generator.analyzer, 'analyze_response') as mock_analyze:
            mock_analyze.side_effect = [
                {"word_count": 2, "logical_keywords_count": 0, "has_step_by_step": False},
                {"word_count": 5, "logical_keywords_count": 2, "has_step_by_step": True},
                {"word_count": 2, "logical_keywords_count": 0, "has_step_by_step": False},
                {"word_count": 8, "logical_keywords_count": 3, "has_step_by_step": True}
            ]
            
            results = generator.generate_comparison_results(sample_test_results, sample_riddle_titles, ["Загадка 1", "Загадка 2"])
            
            assert len(results) == 2
            assert all(isinstance(result, ComparisonResult) for result in results)
            
            # Проверяем первый результат
            first_result = results[0]
            assert first_result.riddle_title == "Загадка 1"
            assert first_result.model_name == "qwen"
            assert first_result.direct_answer == "Прямой ответ"
            assert first_result.stepwise_answer == "Пошаговый ответ с рассуждениями"
            assert first_result.word_difference == 3  # 5 - 2
            assert first_result.direct_response_time == 1.0
            assert first_result.stepwise_response_time == 2.0
            assert first_result.riddle_text == "Загадка 1"
    
    def test_generate_markdown_report(self, generator):
        """Тест генерации Markdown отчета."""
        sample_results = [
            ComparisonResult(
                riddle_title="Тестовая загадка",
                model_name="qwen",
                direct_answer="Короткий ответ",
                stepwise_answer="Длинный пошаговый ответ",
                word_difference=5,
                direct_analysis={"word_count": 2, "logical_keywords_count": 0, "has_step_by_step": False},
                stepwise_analysis={"word_count": 7, "logical_keywords_count": 2, "has_step_by_step": True},
                direct_response_time=1.0,
                stepwise_response_time=2.0,
                riddle_text="Тестовая загадка для проверки"
            )
        ]
        
        report = generator.generate_markdown_report(sample_results)
        
        assert isinstance(report, str)
        assert "# Тест моделей на логических загадках" in report
        assert "## Общая статистика" in report
        assert "## Детальный анализ" in report
        assert "## Статистика" in report
        assert "Тестовая загадка" in report
        assert "qwen" in report
        assert "Тестовая загадка для проверки" in report
    
    def test_save_report(self, generator):
        """Тест сохранения отчета в файл."""
        test_report = "# Тестовый отчет\nСодержимое отчета"
        
        with patch("builtins.open", mock_open()) as mock_file:
            filename = generator.save_report(test_report, "test_report.md")
            
            assert filename == "test_report.md"
            mock_file.assert_called_once_with("test_report.md", 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with(test_report)
    
    def test_save_report_default_filename(self, generator):
        """Тест сохранения отчета с автоматическим именем файла."""
        test_report = "# Тестовый отчет"
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch('src.report_generator.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20231201_120000"
                
                filename = generator.save_report(test_report)
                
                assert filename == "model_test_report_20231201_120000.md"
                mock_file.assert_called_once_with("model_test_report_20231201_120000.md", 'w', encoding='utf-8')
    
    def test_generate_statistics_empty_results(self, generator):
        """Тест генерации статистики для пустых результатов."""
        stats = generator._generate_statistics([])
        assert stats == ""
    
    def test_generate_statistics_with_results(self, generator):
        """Тест генерации статистики с результатами."""
        sample_results = [
            ComparisonResult(
                riddle_title="Загадка 1",
                model_name="qwen",
                direct_answer="Ответ 1",
                stepwise_answer="Ответ 2",
                word_difference=5,
                direct_analysis={},
                stepwise_analysis={},
                direct_response_time=1.0,
                stepwise_response_time=2.0,
                riddle_text=""
            ),
            ComparisonResult(
                riddle_title="Загадка 2",
                model_name="qwen",
                direct_answer="Ответ 3",
                stepwise_answer="Ответ 4",
                word_difference=3,
                direct_analysis={},
                stepwise_analysis={},
                direct_response_time=1.5,
                stepwise_response_time=2.5,
                riddle_text=""
            )
        ]
        
        stats = generator._generate_statistics(sample_results)
        
        assert "## Статистика" in stats
        assert "Общее количество тестов:** 2" in stats
        assert "Средняя разница в словах: 4.0" in stats
        assert "Среднее время прямого ответа: 1.25s" in stats
        assert "Среднее время пошагового ответа: 2.25s" in stats
        assert "qwen:" in stats
