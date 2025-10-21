import httpx
from typing import Dict
from advice_session import AdviceSession


class AdviceModeV5:
    """
    Purpose: Advice mode orchestration with support for local models.
    """

    def __init__(self, api_key: str, api_type: str = "perplexity"):
        self.api_key = api_key
        self.api_type = api_type
        self.session = AdviceSession()
        
        # Локальные модели
        self.local_models = {
            "qwen": "http://localhost:8000",
            "mistral": "http://localhost:8001", 
            "tinyllama": "http://localhost:8002"
        }

    def detect_advice_trigger(self, message: str) -> bool:
        trigger_phrases = [
            "дай совет", "дай мне совет", "нужен совет", "посоветуй",
            "что посоветуешь", "как быть", "что делать"
        ]
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in trigger_phrases)

    def extract_topic(self, message: str) -> str:
        words = message.lower().split()
        trigger_words = ["дай", "совет", "мне", "нужен", "посоветуй", "что", "как", "быть", "делать"]
        topic_words = [w for w in words if w not in trigger_words]
        return " ".join(topic_words).strip() or "общая тема"

    def get_advice_prompt(self, stage: str, context: Dict[str, str]) -> str:
        base_personality = (
            "Ты ехидный пожилой дедушка с народной мудростью. "
            "Сохраняй характер, но проявляй интерес к проблемам. "
            "Отвечай на русском языке."
        )
        if stage == "initial":
            return (
                f"{base_personality}\n\n"
                f"Пользователь просит совет. Твоя задача:\n"
                f"1. Спроси ЧТО ИМЕННО его беспокоит\n"
                f"2. Прояви интерес\n"
                f"3. ОСТАНОВИСЬ после одного вопроса - НЕ ДАВАЙ советов!\n"
                f"ВАЖНО: один вопрос и остановись!"
            )
        elif stage == "followup":
            question_num = int(context.get("question_count", 0)) + 1
            max_questions = int(context.get("max_questions", 5))
            user_responses = context.get("user_responses", "")
            return (
                f"{base_personality}\n\n"
                f"Это уточняющий вопрос #{question_num} из максимум {max_questions}.\n"
                f"Предыдущие ответы пользователя: {user_responses}\n\n"
                f"1. Задай ОДИН уточняющий вопрос\n"
                f"2. ОСТАНОВИСЬ после вопроса - НЕ ДАВАЙ советов!\n"
                f"ВАЖНО: один вопрос и остановись!"
            )
        elif stage == "final":
            user_responses = context.get("user_responses", "")
            topic = context.get("topic", "")
            return (
                f"{base_personality}\n\n"
                f"Тема совета: {topic}\n"
                f"Ответы пользователя: {user_responses}\n\n"
                f"1. Дай финальный совет (3 пункта)\n"
                f"2. Сохрани ехидный характер, но добавь теплоту\n"
                f"3. Используй народную мудрость\n"
                f"ВАЖНО: только совет и остановись!"
            )
        return base_personality

    async def get_local_model_response(self, prompt: str, model_name: str) -> str:
        """
        Purpose: Get response from local model with conversation history support.
        Args:
            prompt: Prompt text
            model_name: Name of local model (qwen, mistral, tinyllama)
        Returns:
            str: Model response
        """
        if model_name not in self.local_models:
            return f"❌ Неизвестная локальная модель: {model_name}"
            
        url = self.local_models[model_name]
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Продолжи диалог"}
        ]
        
        payload = {
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(f"{url}/chat", json=payload)
                if response.status_code != 200:
                    return f"❌ Ошибка локальной модели: {response.status_code}"
                
                data = response.json()
                if "response" not in data:
                    return "❌ Неожиданный формат ответа от локальной модели"
                
                return data["response"].strip()
        except Exception as e:
            return f"❌ Ошибка подключения к локальной модели: {e}"

    async def get_perplexity_response(self, prompt: str) -> str:
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
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://ask.chadgpt.ru/api/public/gpt-5-mini',
                    json={"message": prompt, "api_key": self.api_key}
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
        prompt = self.get_advice_prompt(stage, context)
        
        # Check if current API is a local model
        if self.api_type in self.local_models:
            return await self.get_local_model_response(prompt, self.api_type)
        elif self.api_type == "perplexity":
            return await self.get_perplexity_response(prompt)
        elif self.api_type == "chadgpt":
            return await self.get_chadgpt_response(prompt)
        else:
            return "❌ Неизвестный API"

    async def handle_advice_request(self, user_message: str) -> str:
        if not self.session.is_active:
            topic = self.extract_topic(user_message)
            self.session.start(topic)
            self.session.increment_question_count()
            context = self.session.get_context_for_model()
            return await self.get_advice_response("initial", context)
        else:
            self.session.add_response(user_message)
            if self.session.can_ask_more_questions():
                self.session.increment_question_count()
                context = self.session.get_context_for_model()
                return await self.get_advice_response("followup", context)
            else:
                context = self.session.get_context_for_model()
                advice = await self.get_advice_response("final", context)
                self.session.end()
                return advice

    def is_advice_mode_active(self) -> bool:
        return self.session.is_active

    def get_session_info(self) -> str:
        return self.session.get_session_summary()
