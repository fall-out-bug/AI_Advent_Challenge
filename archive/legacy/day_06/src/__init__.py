"""
Пакет для тестирования локальных моделей на логических загадках.

Модули:
- model_client: Клиент для работы с локальными моделями
- riddles: Коллекция загадок и анализатор ответов
- report_generator: Генератор отчетов
- main: Основной модуль для запуска тестирования
"""

from .model_client import LocalModelClient, ModelTestResult, ModelResponse
from .riddles import RiddleCollection, RiddleAnalyzer, Riddle
from .report_generator import ReportGenerator, ComparisonResult
from .main import ModelTester

__all__ = [
    "LocalModelClient",
    "ModelTestResult", 
    "ModelResponse",
    "RiddleCollection",
    "RiddleAnalyzer",
    "Riddle",
    "ReportGenerator",
    "ComparisonResult",
    "ModelTester"
]
