"""
Модуль с логическими загадками и логикой их анализа.

Содержит загадки из ТЗ и функции для анализа ответов моделей.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
import re


@dataclass
class Riddle:
    """Структура загадки."""
    title: str
    text: str
    difficulty: int  # 1-5, где 5 - самая сложная


class RiddleAnalyzer:
    """Анализатор ответов на загадки."""
    
    # Ключевые слова для анализа логического рассуждения
    LOGICAL_KEYWORDS = [
        "если", "значит", "поэтому", "следовательно", "отсюда", 
        "из этого", "получается", "вывод", "рассуждение", "логика",
        "шаг", "этап", "сначала", "затем", "далее", "в итоге"
    ]
    
    def __init__(self):
        """Инициализация анализатора."""
        pass
    
    def analyze_response(self, response: str) -> Dict[str, any]:
        """
        Анализ ответа модели.
        
        Args:
            response: Текст ответа модели
            
        Returns:
            Dict: Результаты анализа
        """
        return {
            "word_count": self._count_words(response),
            "has_logical_keywords": self._has_logical_keywords(response),
            "logical_keywords_count": self._count_logical_keywords(response),
            "has_step_by_step": self._has_step_by_step_structure(response),
            "response_length": len(response)
        }
    
    def _count_words(self, text: str) -> int:
        """Подсчет количества слов в тексте."""
        return len(text.split())
    
    def _has_logical_keywords(self, text: str) -> bool:
        """Проверка наличия логических ключевых слов."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.LOGICAL_KEYWORDS)
    
    def _count_logical_keywords(self, text: str) -> int:
        """Подсчет количества логических ключевых слов."""
        text_lower = text.lower()
        count = 0
        for keyword in self.LOGICAL_KEYWORDS:
            count += text_lower.count(keyword)
        return count
    
    def _has_step_by_step_structure(self, text: str) -> bool:
        """Проверка наличия пошаговой структуры."""
        # Ищем числовые маркеры или слова, указывающие на шаги
        step_patterns = [
            r'\d+[\.\)]\s',  # 1. или 1)
            r'шаг\s*\d+',    # шаг 1
            r'этап\s*\d+',   # этап 1
            r'сначала',      # сначала
            r'затем',        # затем
            r'далее',        # далее
            r'в итоге'       # в итоге
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in step_patterns)


class RiddleCollection:
    """Коллекция загадок из ТЗ."""
    
    def __init__(self):
        """Инициализация коллекции загадок."""
        self.riddles = self._create_riddles()
    
    def _create_riddles(self) -> List[Riddle]:
        """Создание списка загадок согласно ТЗ."""
        return [
            Riddle(
                title="Про монету и котёнка",
                text="Ты заходишь в комнату и видишь монету и котёнка. Ты берёшь монету и выходишь. Что остаётся в комнате?",
                difficulty=1
            ),
            Riddle(
                title="Классическая загадка о поезде",
                text="Поезд выехал из точки А в 9 утра, а другой — из точки Б в то же время навстречу первому. Кто будет ближе к пункту А, когда они встретятся?",
                difficulty=2
            ),
            Riddle(
                title="Загадка с тремя дверями",
                text="Перед тобой три двери: за одной — приз, за другими — пусто. Ты выбираешь одну, ведущий открывает пустую из оставшихся и предлагает сменить выбор. Что выгоднее?",
                difficulty=3
            ),
            Riddle(
                title="Парадокс двух конвертов",
                text="В одном конверте сумма X, в другом — 2X. Ты выбираешь один. Стоит ли менять? Почему?",
                difficulty=4
            ),
            Riddle(
                title="Задача о мудрецах с цветными шапками",
                text="Три мудреца видят головы друг друга, знают, что каждая шапка — белая или синяя, и слышат, что как минимум одна белая. Они по очереди говорят «не знаю». Что могут заключить?",
                difficulty=5
            )
        ]
    
    def get_riddles(self) -> List[Riddle]:
        """Получение списка всех загадок."""
        return self.riddles
    
    def get_riddle_texts(self) -> List[str]:
        """Получение текстов всех загадок."""
        return [riddle.text for riddle in self.riddles]
    
    def get_riddle_by_difficulty(self, difficulty: int) -> List[Riddle]:
        """
        Получение загадок по уровню сложности.
        
        Args:
            difficulty: Уровень сложности (1-5)
            
        Returns:
            List[Riddle]: Загадки указанной сложности
        """
        return [riddle for riddle in self.riddles if riddle.difficulty == difficulty]
