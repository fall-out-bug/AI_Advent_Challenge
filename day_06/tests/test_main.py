"""
Unit тесты для модуля main.

Тестирует функциональность основного модуля запуска тестирования.
"""

import pytest
from unittest.mock import AsyncMock, patch, mock_open

from src.main import ModelTester


class TestModelTester:
    """Тесты для класса ModelTester."""
    
    @pytest.fixture
    def tester(self):
        """Фикстура для создания тестера."""
        from unittest.mock import AsyncMock
        mock_client = AsyncMock()
        return ModelTester(client=mock_client)
    
    def test_tester_initialization(self, tester):
        """Тест инициализации тестера."""
        assert tester.client is not None
        assert tester.riddle_collection is not None
        assert tester.report_generator is not None
    
    @pytest.mark.asyncio
    async def test_check_model_availability_success(self, tester):
        """Тест успешной проверки доступности моделей."""
        with patch.object(tester.client, 'check_model_availability') as mock_check:
            mock_check.return_value = {
                "qwen": True,
                "mistral": True,
                "tinyllama": False
            }
            
            await tester._check_model_availability()
            
            mock_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_model_availability_no_models(self, tester):
        """Тест проверки доступности когда нет доступных моделей."""
        with patch.object(tester.client, 'check_model_availability') as mock_check:
            mock_check.return_value = {
                "qwen": False,
                "mistral": False,
                "tinyllama": False
            }
            
            with pytest.raises(SystemExit):
                await tester._check_model_availability()
    
    def test_print_console_summary(self, tester):
        """Тест вывода краткой сводки в консоль."""
        # Создаем мок-объекты для результатов
        mock_result1 = type('MockResult', (), {
            'model_name': 'qwen',
            'word_difference': 5,
            'direct_response_time': 1.0,
            'stepwise_response_time': 2.0,
            'stepwise_analysis': {'has_logical_keywords': True, 'has_step_by_step': True}
        })()
        
        mock_result2 = type('MockResult', (), {
            'model_name': 'qwen',
            'word_difference': 3,
            'direct_response_time': 1.5,
            'stepwise_response_time': 2.5,
            'stepwise_analysis': {'has_logical_keywords': False, 'has_step_by_step': True}
        })()
        
        results = [mock_result1, mock_result2]
        
        # Тест не должен вызывать исключений
        tester._print_console_summary(results)
        assert True  # Если дошли сюда, тест прошел
    
    def test_print_console_summary_empty_results(self, tester):
        """Тест вывода сводки для пустых результатов."""
        tester._print_console_summary([])
        assert True  # Если дошли сюда, тест прошел
    
    @pytest.mark.asyncio
    async def test_context_manager(self, tester):
        """Test context manager functionality."""
        async with tester as ctx_tester:
            assert ctx_tester is tester
            # Test that tester can be used in context
            assert ctx_tester.client is not None
