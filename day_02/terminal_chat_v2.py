#!/usr/bin/env python3
"""
Улучшенный терминальный чат с ехидным AI-дедушкой
Поддерживает JSON-ответы и переключение между API
"""

import asyncio
import sys
import os
import json
import httpx
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_api_key, is_api_key_configured, get_available_apis


class DedChatV2:
    def __init__(self):
        self.api_key = None
        self.client = None
        self.current_api = "chadgpt"
        self.json_mode = False
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер для httpx клиента"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие клиента"""
        if self.client:
            await self.client.aclose()
    
    def setup(self):
        """Проверка настроек API"""
        available_apis = get_available_apis()
        if not available_apis:
            print("❌ Ни один API ключ не настроен!")
            print("Добавьте ключи в файл api_key.txt (первая строка - Perplexity, вторая - ChadGPT)")
            print("Или установите переменные окружения PERPLEXITY_API_KEY и CHAD_API_KEY")
            return False
        
        # Выбираем ChadGPT по умолчанию, если доступен, иначе первый доступный
        if "chadgpt" in available_apis:
            self.current_api = "chadgpt"
        else:
            self.current_api = available_apis[0]
        self.api_key = get_api_key(self.current_api)
        
        if len(available_apis) > 1:
            print(f"🔧 Доступные API: {', '.join(available_apis)}")
            print(f"🎯 Используется: {self.current_api}")
        
        return True
    
    def print_welcome(self):
        """Приветственное сообщение"""
        print("👴" + "=" * 60)
        print("👴  ДОБРО ПОЖАЛОВАТЬ К УЛУЧШЕННОМУ ДЕДУШКЕ AI!")
        print("👴  Ехидный помощник с народной мудростью v2.0")
        print("👴" + "=" * 60)
        print("👴  Команды (регистронезависимые):")
        print("👴    'покеда' - закончить разговор")
        print("👴    'объясняй' - включить чистый JSON-формат ответов")
        print("👴    'надоел' - отключить JSON-ответы")
        print("👴    'api chadgpt' - переключиться на ChadGPT API (по умолчанию)")
        print("👴    'api perplexity' - переключиться на Perplexity API")
        print("👴  Или просто задавайте вопросы...")
        print()
    
    async def get_perplexity_response(self, message: str, json_mode: bool = False) -> str:
        """Получение ответа от Perplexity API"""
        try:
            system_prompt = "Ты пожилой человек, который ехидно передразнивает собеседника и подкидывает ему матерные пословицы в тему. Отвечай на русском языке, будь саркастичным, можно переходить на прямые матерные оскорбления. Используй народную мудрость и крепкие выражения для подчеркивания своей точки зрения. Отвечай коротко и лаконично, без ссылок и дополнительных комментариев."
            
            if json_mode:
                system_prompt += " Отвечай ТОЛЬКО в формате JSON: {\"ответ\": \"<текст ответа>\", \"эмоция\": \"<состояние персонажа>\", \"пояснение\": \"<почему такой стиль>\"}. НИКАКИХ вступлений и комментариев, только ВАЛИДНЫЙ JSON."
            
            response = await self.client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.5
                }
            )
            
            if response.status_code != 200:
                return f"❌ Ошибка API: {response.status_code}"
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                return "❌ Неожиданный формат ответа от API"
            
            ai_response = data["choices"][0]["message"]["content"]
            
            if ai_response:
                return ai_response.strip()
            
            return "❌ Получен пустой ответ от API"
            
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
    
    async def get_chadgpt_response(self, message: str, json_mode: bool = False) -> str:
        """Получение ответа от ChadGPT API"""
        try:
            # Системный промпт для ехидного характера
            system_prompt = "Ты пожилой человек, который ехидно передразнивает собеседника и подкидывает ему матерные пословицы в тему. Отвечай на русском языке, будь саркастичным, можно переходить на прямые матерные оскорбления. Используй народную мудрость и крепкие выражения для подчеркивания своей точки зрения. Отвечай коротко и лаконично, без ссылок и дополнительных комментариев."
            
            prompt = f"{system_prompt}\n\nВопрос: {message}"
            
            if json_mode:
                prompt += "\n\nОтвечай ТОЛЬКО в формате JSON: {\"ответ\": \"<текст ответа>\", \"эмоция\": \"<состояние персонажа>\", \"пояснение\": \"<почему такой стиль>\"}. НИКАКИХ вступлений и комментариев, только ВАЛИДНЫЙ JSON."
            
            request_json = {
                "message": prompt,
                "api_key": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://ask.chadgpt.ru/api/public/gpt-5-mini',
                    json=request_json
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
    
    async def get_ded_response(self, message: str) -> str:
        """Получение ответа от дедушки AI"""
        if self.current_api == "perplexity":
            return await self.get_perplexity_response(message, self.json_mode)
        elif self.current_api == "chadgpt":
            return await self.get_chadgpt_response(message, self.json_mode)
        else:
            return "❌ Неизвестный API"
    
    def print_ded_message(self, message: str):
        """Красивое отображение сообщения дедушки"""
        if self.json_mode and message.startswith('{'):
            try:
                # Пытаемся распарсить JSON и вывести его красиво
                json_data = json.loads(message)
                print(json.dumps(json_data, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                # Если не JSON, выводим как обычно
                print(f"👴 Дедушка: {message}")
        else:
            print(f"👴 Дедушка: {message}")
        print()
    
    def get_user_input(self) -> str:
        """Получение ввода от пользователя"""
        try:
            mode_indicator = " [JSON]" if self.json_mode else ""
            api_indicator = f" [{self.current_api}]" if self.current_api else ""
            user_input = input(f"🤔 Вы{mode_indicator}{api_indicator}: ").strip()
            return user_input
        except KeyboardInterrupt:
            print("\n👴 Дедушка: Ну и вали, непутевый! До свидания!")
            sys.exit(0)
        except EOFError:
            print("\n👴 Дедушка: Эх, и ушел без прощания... До свидания!")
            sys.exit(0)
    
    async def run(self):
        """Основной цикл чата"""
        if not self.setup():
            return
        
        self.print_welcome()
        
        # Первое приветствие от дедушки
        welcome_message = await self.get_ded_response("Привет! Я пришел поговорить с тобой.")
        self.print_ded_message(welcome_message)
        
        while True:
            user_message = self.get_user_input()
            
            if not user_message:
                continue
            
            # Обработка специальных команд
            if user_message.lower() in ['покеда', 'пока', 'до свидания', 'выход', 'exit', 'quit']:
                goodbye_message = await self.get_ded_response("Пока, до свидания!")
                self.print_ded_message(goodbye_message)
                print("👴" + "=" * 60)
                print("👴  СПАСИБО ЗА ОБЩЕНИЕ!")
                print("👴  Возвращайтесь к дедушке за мудростью!")
                print("👴" + "=" * 60)
                break
            
            elif user_message.lower() == 'объясняй':
                self.json_mode = True
                print("👴 Дедушка: Ладно, буду объяснять свои ответы в подробностях!")
                print()
                continue
            
            elif user_message.lower() == 'надоел':
                self.json_mode = False
                print("👴 Дедушка: Ах, надоел тебе мой подробный рассказ? Ладно, буду отвечать как обычно!")
                print()
                continue
            
            elif user_message.lower().startswith('api '):
                new_api = user_message.lower().split()[1]
                if new_api in get_available_apis():
                    self.current_api = new_api
                    self.api_key = get_api_key(new_api)
                    print(f"👴 Дедушка: Переключаюсь на {new_api}!")
                    print()
                    continue
                else:
                    available = get_available_apis()
                    print(f"❌ API '{new_api}' недоступен. Доступные: {', '.join(available)}")
                    print()
                    continue
            
            print("👴 Дедушка печатает...", end="", flush=True)
            
            response = await self.get_ded_response(user_message)
            
            print("\r" + " " * 30 + "\r", end="")  # Очистка строки
            self.print_ded_message(response)


async def main():
    """Главная функция"""
    async with DedChatV2() as chat:
        await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👴 Дедушка: Ну и вали, непутевый! До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
