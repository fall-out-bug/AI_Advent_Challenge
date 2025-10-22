#!/usr/bin/env python3
"""
Класс для управления состоянием сессии советчика
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class AdviceSession:
    """
    Управляет состоянием диалога в режиме советчика
    
    Attributes:
        question_count: Количество заданных вопросов
        max_questions: Максимальное количество вопросов (по умолчанию 5)
        user_responses: Список ответов пользователя
        topic: Тема, по которой нужен совет
        is_active: Активна ли сессия советчика
        start_time: Время начала сессии
        context: Дополнительный контекст для модели
    """
    question_count: int = 0
    max_questions: int = 5
    user_responses: List[str] = field(default_factory=list)
    topic: str = ""
    is_active: bool = False
    start_time: Optional[datetime] = None
    context: Dict[str, str] = field(default_factory=dict)
    
    def start(self, topic: str = "") -> None:
        """
        Начинает новую сессию советчика
        
        Args:
            topic: Тема для совета
        """
        self.question_count = 0
        self.user_responses.clear()
        self.topic = topic
        self.is_active = True
        self.start_time = datetime.now()
        self.context.clear()
    
    def add_response(self, response: str) -> None:
        """
        Добавляет ответ пользователя
        
        Args:
            response: Ответ пользователя
        """
        self.user_responses.append(response)
    
    def increment_question_count(self) -> None:
        """Увеличивает счетчик вопросов"""
        self.question_count += 1
    
    def can_ask_more_questions(self) -> bool:
        """
        Проверяет, можно ли задать еще вопросы
        
        Returns:
            True если можно задать еще вопросы
        """
        return self.question_count < self.max_questions
    
    def end(self) -> None:
        """Завершает сессию советчика"""
        self.is_active = False
    
    def get_session_summary(self) -> str:
        """
        Возвращает краткое описание сессии
        
        Returns:
            Строка с описанием сессии
        """
        duration = ""
        if self.start_time:
            duration = f" (длительность: {(datetime.now() - self.start_time).seconds}с)"
        
        return (f"Сессия советчика: тема='{self.topic}', "
                f"вопросов={self.question_count}/{self.max_questions}, "
                f"ответов={len(self.user_responses)}{duration}")
    
    def get_context_for_model(self) -> Dict[str, str]:
        """
        Возвращает контекст для передачи в модель
        
        Returns:
            Словарь с контекстом
        """
        return {
            "topic": self.topic,
            "question_count": str(self.question_count),
            "max_questions": str(self.max_questions),
            "user_responses": " | ".join(self.user_responses),
            "session_active": str(self.is_active)
        }
