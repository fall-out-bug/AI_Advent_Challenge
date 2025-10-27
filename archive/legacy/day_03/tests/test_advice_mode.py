#!/usr/bin/env python3
"""
Тесты для класса AdviceMode
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, patch
from advice_mode import AdviceMode


class TestAdviceMode:
    """Тесты для класса AdviceMode"""
    
    def test_advice_mode_initialization(self):
        """Тест инициализации режима советчика"""
        api_key = "test_key"
        api_type = "perplexity"
        
        advice_mode = AdviceMode(api_key, api_type)
        
        assert advice_mode.api_key == api_key
        assert advice_mode.api_type == api_type
        assert advice_mode.session is not None
        assert advice_mode.session.is_active is False
    
    def test_detect_advice_trigger(self):
        """Тест определения триггера для режима советчика"""
        advice_mode = AdviceMode("test_key")
        
        # Положительные случаи
        assert advice_mode.detect_advice_trigger("дай совет") is True
        assert advice_mode.detect_advice_trigger("Дай мне совет") is True
        assert advice_mode.detect_advice_trigger("нужен совет по работе") is True
        assert advice_mode.detect_advice_trigger("посоветуй что делать") is True
        assert advice_mode.detect_advice_trigger("что посоветуешь") is True
        assert advice_mode.detect_advice_trigger("как быть") is True
        assert advice_mode.detect_advice_trigger("что делать") is True
        
        # Отрицательные случаи
        assert advice_mode.detect_advice_trigger("привет") is False
        assert advice_mode.detect_advice_trigger("как дела") is False
        assert advice_mode.detect_advice_trigger("расскажи анекдот") is False
    
    def test_extract_topic(self):
        """Тест извлечения темы из сообщения"""
        advice_mode = AdviceMode("test_key")
        
        # Тест с темой
        topic = advice_mode.extract_topic("дай совет по работе")
        assert topic == "по работе"
        
        # Тест без темы
        topic = advice_mode.extract_topic("дай совет")
        assert topic == "общая тема"
        
        # Тест с пустым сообщением
        topic = advice_mode.extract_topic("")
        assert topic == "общая тема"
    
    def test_get_advice_prompt_initial(self):
        """Тест генерации промпта для начального этапа"""
        advice_mode = AdviceMode("test_key")
        context = {"topic": "работа"}
        
        prompt = advice_mode.get_advice_prompt("initial", context)
        
        assert "Спроси ЧТО ИМЕННО" in prompt
        assert "ОСТАНОВИСЬ после одного вопроса" in prompt
        assert "НЕ ДАВАЙ советов пока" in prompt
    
    def test_get_advice_prompt_followup(self):
        """Тест генерации промпта для уточняющих вопросов"""
        advice_mode = AdviceMode("test_key")
        context = {
            "question_count": "2",
            "max_questions": "5",
            "user_responses": "Ответ 1 | Ответ 2"
        }
        
        prompt = advice_mode.get_advice_prompt("followup", context)
        
        assert "уточняющий вопрос #3" in prompt
        assert "из максимум 5" in prompt
        assert "Ответ 1 | Ответ 2" in prompt
        assert "ОСТАНОВИСЬ после вопроса" in prompt
    
    def test_get_advice_prompt_final(self):
        """Тест генерации промпта для финального совета"""
        advice_mode = AdviceMode("test_key")
        context = {
            "topic": "отношения",
            "user_responses": "Проблема с партнером | Не понимаем друг друга"
        }
        
        prompt = advice_mode.get_advice_prompt("final", context)
        
        assert "Тема совета: отношения" in prompt
        assert "Проблема с партнером" in prompt
        assert "Дай финальный совет" in prompt
        assert "ОСТАНОВИСЬ после совета" in prompt
    
    @pytest.mark.asyncio
    async def test_handle_advice_request_initial(self):
        """Тест обработки первого запроса на совет"""
        advice_mode = AdviceMode("test_key")
        
        with patch.object(advice_mode, 'get_advice_response', new_callable=AsyncMock) as mock_response:
            mock_response.return_value = "Что именно вас беспокоит?"
            
            response = await advice_mode.handle_advice_request("дай совет по работе")
            
            assert response == "Что именно вас беспокоит?"
            assert advice_mode.session.is_active is True
            assert advice_mode.session.topic == "по работе"
            assert advice_mode.session.question_count == 1
            mock_response.assert_called_once_with("initial", advice_mode.session.get_context_for_model())
    
    @pytest.mark.asyncio
    async def test_handle_advice_request_followup(self):
        """Тест обработки уточняющих ответов"""
        advice_mode = AdviceMode("test_key")
        advice_mode.session.start("работа")
        advice_mode.session.increment_question_count()
        
        with patch.object(advice_mode, 'get_advice_response', new_callable=AsyncMock) as mock_response:
            mock_response.return_value = "А что именно не нравится в работе?"
            
            response = await advice_mode.handle_advice_request("Не нравится начальник")
            
            assert response == "А что именно не нравится в работе?"
            assert len(advice_mode.session.user_responses) == 1
            assert advice_mode.session.user_responses[0] == "Не нравится начальник"
            assert advice_mode.session.question_count == 2
            mock_response.assert_called_once_with("followup", advice_mode.session.get_context_for_model())
    
    @pytest.mark.asyncio
    async def test_handle_advice_request_final(self):
        """Тест обработки финального совета"""
        advice_mode = AdviceMode("test_key")
        advice_mode.session.start("работа")
        advice_mode.session.question_count = 5  # Максимальное количество вопросов
        advice_mode.session.add_response("Ответ 1")
        advice_mode.session.add_response("Ответ 2")
        
        with patch.object(advice_mode, 'get_advice_response', new_callable=AsyncMock) as mock_response:
            mock_response.return_value = "Мой совет: смени работу!"
            
            response = await advice_mode.handle_advice_request("Последний ответ")
            
            assert response == "Мой совет: смени работу!"
            assert advice_mode.session.is_active is False
            mock_response.assert_called_once_with("final", advice_mode.session.get_context_for_model())
    
    def test_is_advice_mode_active(self):
        """Тест проверки активности режима советчика"""
        advice_mode = AdviceMode("test_key")
        
        assert advice_mode.is_advice_mode_active() is False
        
        advice_mode.session.start("тест")
        assert advice_mode.is_advice_mode_active() is True
        
        advice_mode.session.end()
        assert advice_mode.is_advice_mode_active() is False
    
    def test_get_session_info(self):
        """Тест получения информации о сессии"""
        advice_mode = AdviceMode("test_key")
        
        # Неактивная сессия
        info = advice_mode.get_session_info()
        assert "не активна" in info or "0/5" in info
        
        # Активная сессия
        advice_mode.session.start("тест")
        advice_mode.session.increment_question_count()
        advice_mode.session.add_response("Ответ")
        
        info = advice_mode.get_session_info()
        assert "тест" in info
        assert "1/5" in info
        assert "1" in info  # количество ответов
