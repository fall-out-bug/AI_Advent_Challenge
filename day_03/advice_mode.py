#!/usr/bin/env python3
"""
Класс для управления режимом советчика
"""

import httpx
from typing import Dict, Optional
from advice_session import AdviceSession


class AdviceMode:
    """
    Управляет режимом советчика с ограничениями модели и структурированным диалогом
    """
    
    def __init__(self, api_key: str, api_type: str = "perplexity"):
        """
        Инициализация режима советчика
        
        Args:
            api_key: API ключ для запросов
            api_type: Тип API (perplexity или chadgpt)
        """
        self.api_key = api_key
        self.api_type = api_type
        self.session = AdviceSession()
    
    def detect_advice_trigger(self, message: str) -> bool:
        """
        Определяет, содержит ли сообщение триггер для режима советчика
        
        Args:
            message: Сообщение пользователя
            
        Returns:
            True если нужно активировать режим советчика
        """
        trigger_phrases = [
            "дай совет",
            "дай мне совет", 
            "нужен совет",
            "посоветуй",
            "что посоветуешь",
            "как быть",
            "что делать"
        ]
        
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in trigger_phrases)
    
    def extract_topic(self, message: str) -> str:
        """
        Извлекает тему из сообщения пользователя
        
        Args:
            message: Сообщение пользователя
            
        Returns:
            Извлеченная тема
        """
        # Простая логика извлечения темы
        # Можно улучшить с помощью NLP
        words = message.lower().split()
        
        # Убираем триггерные фразы
        trigger_words = ["дай", "совет", "мне", "нужен", "посоветуй", "что", "как", "быть", "делать"]
        topic_words = [word for word in words if word not in trigger_words]
        
        return " ".join(topic_words).strip() or "общая тема"
    
    def get_advice_prompt(self, stage: str, context: Dict[str, str]) -> str:
        """
        Генерирует промпт для модели в зависимости от этапа диалога
        
        Args:
            stage: Этап диалога (initial, followup, final)
            context: Контекст сессии
            
        Returns:
            Сформированный промпт
        """
        base_personality = (
            "Ты ехидный пожилой дедушка с народной мудростью. "
            "Сохраняй свой характер, но проявляй живой интерес к проблемам собеседника. "
            "Можешь использовать крепкие выражения и народную мудрость. "
            "Отвечай на русском языке."
        )
        
        if stage == "initial":
            return (
                f"{base_personality}\n\n"
                f"Пользователь просит совет. Твоя задача:\n"
                f"1. Спроси ЧТО ИМЕННО его беспокоит или в чем нужна помощь\n"
                f"2. Прояви живой интерес к его проблеме\n"
                f"3. ОСТАНОВИСЬ после одного вопроса - НЕ ДАВАЙ советов пока!\n"
                f"4. Будь ехидным, но заинтересованным\n\n"
                f"ВАЖНО: Задай ТОЛЬКО ОДИН вопрос и ОСТАНОВИСЬ!"
            )
        
        elif stage == "followup":
            question_num = int(context.get("question_count", 0)) + 1
            max_questions = int(context.get("max_questions", 5))
            user_responses = context.get("user_responses", "")
            
            return (
                f"{base_personality}\n\n"
                f"Это уточняющий вопрос #{question_num} из максимум {max_questions}.\n"
                f"Предыдущие ответы пользователя: {user_responses}\n\n"
                f"Твоя задача:\n"
                f"1. Задай ОДИН уточняющий вопрос для лучшего понимания проблемы\n"
                f"2. Прояви живой интерес и ехидство\n"
                f"3. ОСТАНОВИСЬ после вопроса - НЕ ДАВАЙ советов!\n"
                f"4. Вопрос должен быть конкретным и полезным\n\n"
                f"ВАЖНО: Задай ТОЛЬКО ОДИН уточняющий вопрос и ОСТАНОВИСЬ!"
            )
        
        elif stage == "final":
            user_responses = context.get("user_responses", "")
            topic = context.get("topic", "")
            
            return (
                f"{base_personality}\n\n"
                f"Тема совета: {topic}\n"
                f"Ответы пользователя: {user_responses}\n\n"
                f"Твоя задача:\n"
                f"1. Дай финальный совет на основе всей собранной информации\n"
                f"2. Сохрани ехидный характер, но добавь теплоту настоящего дедушки\n"
                f"3. Используй народную мудрость и практические советы\n"
                f"4. Совет должен быть конкретным и полезным\n"
                f"5. ОСТАНОВИСЬ после совета - диалог завершен!\n\n"
                f"ВАЖНО: Дай ТОЛЬКО совет и ОСТАНОВИСЬ!"
            )
        
        return base_personality
    
    async def get_perplexity_response(self, prompt: str) -> str:
        """
        Получает ответ от Perplexity API
        
        Args:
            prompt: Промпт для модели
            
        Returns:
            Ответ от модели
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar-pro",
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": "Продолжи диалог"}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code != 200:
                    return f"❌ Ошибка API: {response.status_code}"
                
                data = response.json()
                
                if "choices" not in data or not data["choices"]:
                    return "❌ Неожиданный формат ответа от API"
                
                ai_response = data["choices"][0]["message"]["content"]
                return ai_response.strip() if ai_response else "❌ Получен пустой ответ от API"
                
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    async def get_chadgpt_response(self, prompt: str) -> str:
        """
        Получает ответ от ChadGPT API
        
        Args:
            prompt: Промпт для модели
            
        Returns:
            Ответ от модели
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://ask.chadgpt.ru/api/public/gpt-5-mini',
                    json={
                        "message": prompt,
                        "api_key": self.api_key
                    }
                )
                
                if response.status_code != 200:
                    return f"❌ Ошибка API: {response.status_code}"
                
                resp_json = response.json()
                
                if resp_json.get('is_success'):
                    return resp_json.get('response', '❌ Пустой ответ от API')
                else:
                    error = resp_json.get('error_message', 'Неизвестная ошибка')
                    return f"❌ Ошибка ChadGPT: {error}"
                    
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    async def get_advice_response(self, stage: str, context: Dict[str, str]) -> str:
        """
        Получает ответ от модели в режиме советчика
        
        Args:
            stage: Этап диалога
            context: Контекст сессии
            
        Returns:
            Ответ от модели
        """
        prompt = self.get_advice_prompt(stage, context)
        
        if self.api_type == "perplexity":
            return await self.get_perplexity_response(prompt)
        elif self.api_type == "chadgpt":
            return await self.get_chadgpt_response(prompt)
        else:
            return "❌ Неизвестный API"
    
    async def handle_advice_request(self, user_message: str) -> str:
        """
        Обрабатывает запрос на совет
        
        Args:
            user_message: Сообщение пользователя
            
        Returns:
            Ответ дедушки
        """
        if not self.session.is_active:
            # Начинаем новую сессию советчика
            topic = self.extract_topic(user_message)
            self.session.start(topic)
            self.session.increment_question_count()
            
            context = self.session.get_context_for_model()
            return await self.get_advice_response("initial", context)
        
        else:
            # Продолжаем диалог
            self.session.add_response(user_message)
            
            if self.session.can_ask_more_questions():
                self.session.increment_question_count()
                context = self.session.get_context_for_model()
                return await self.get_advice_response("followup", context)
            else:
                # Даем финальный совет
                context = self.session.get_context_for_model()
                advice = await self.get_advice_response("final", context)
                self.session.end()
                return advice
    
    def is_advice_mode_active(self) -> bool:
        """
        Проверяет, активен ли режим советчика
        
        Returns:
            True если режим активен
        """
        return self.session.is_active
    
    def get_session_info(self) -> str:
        """
        Возвращает информацию о текущей сессии
        
        Returns:
            Информация о сессии
        """
        return self.session.get_session_summary()
