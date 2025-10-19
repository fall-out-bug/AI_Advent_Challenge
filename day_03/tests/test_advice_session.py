#!/usr/bin/env python3
"""
Тесты для класса AdviceSession
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from advice_session import AdviceSession


class TestAdviceSession:
    """Тесты для класса AdviceSession"""
    
    def test_session_initialization(self):
        """Тест инициализации сессии"""
        session = AdviceSession()
        
        assert session.question_count == 0
        assert session.max_questions == 5
        assert session.user_responses == []
        assert session.topic == ""
        assert session.is_active is False
        assert session.start_time is None
        assert session.context == {}
    
    def test_session_start(self):
        """Тест начала сессии"""
        session = AdviceSession()
        topic = "работа"
        
        session.start(topic)
        
        assert session.topic == topic
        assert session.is_active is True
        assert session.start_time is not None
        assert session.question_count == 0
        assert session.user_responses == []
    
    def test_add_response(self):
        """Тест добавления ответа пользователя"""
        session = AdviceSession()
        session.start("тест")
        
        session.add_response("Мой ответ")
        
        assert len(session.user_responses) == 1
        assert session.user_responses[0] == "Мой ответ"
    
    def test_increment_question_count(self):
        """Тест увеличения счетчика вопросов"""
        session = AdviceSession()
        session.start("тест")
        
        initial_count = session.question_count
        session.increment_question_count()
        
        assert session.question_count == initial_count + 1
    
    def test_can_ask_more_questions(self):
        """Тест проверки возможности задать еще вопросы"""
        session = AdviceSession()
        session.start("тест")
        
        # По умолчанию можно задать вопросы
        assert session.can_ask_more_questions() is True
        
        # Устанавливаем максимальное количество вопросов
        session.question_count = session.max_questions
        assert session.can_ask_more_questions() is False
    
    def test_session_end(self):
        """Тест завершения сессии"""
        session = AdviceSession()
        session.start("тест")
        
        assert session.is_active is True
        session.end()
        assert session.is_active is False
    
    def test_get_session_summary(self):
        """Тест получения описания сессии"""
        session = AdviceSession()
        session.start("работа")
        session.add_response("Ответ 1")
        session.increment_question_count()
        
        summary = session.get_session_summary()
        
        assert "работа" in summary
        assert "1/5" in summary
        assert "1" in summary  # количество ответов
    
    def test_get_context_for_model(self):
        """Тест получения контекста для модели"""
        session = AdviceSession()
        session.start("личная жизнь")
        session.add_response("Проблема с отношениями")
        session.increment_question_count()
        
        context = session.get_context_for_model()
        
        assert context["topic"] == "личная жизнь"
        assert context["question_count"] == "1"
        assert context["max_questions"] == "5"
        assert context["user_responses"] == "Проблема с отношениями"
        assert context["session_active"] == "True"
    
    def test_custom_max_questions(self):
        """Тест с пользовательским максимальным количеством вопросов"""
        session = AdviceSession(max_questions=3)
        
        assert session.max_questions == 3
        assert session.can_ask_more_questions() is True
        
        session.question_count = 3
        assert session.can_ask_more_questions() is False
