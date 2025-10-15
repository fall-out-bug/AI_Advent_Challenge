#!/usr/bin/env python3
"""
Терминальный чат с ехидным AI-дедушкой
"""

import asyncio
import sys
from config import get_api_key, is_api_key_configured
import httpx


class DedChat:
    def __init__(self):
        self.api_key = None
        self.client = None
        
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
        if not is_api_key_configured():
            print("❌ API ключ Perplexity не настроен!")
            print("Добавьте ключ в файл api_key.txt или установите переменную окружения PERPLEXITY_API_KEY")
            return False
            
        self.api_key = get_api_key()
        return True
    
    def print_welcome(self):
        """Приветственное сообщение"""
        print("👴" + "=" * 50)
        print("👴  ДОБРО ПОЖАЛОВАТЬ К ДЕДУШКЕ AI!")
        print("👴  Ехидный помощник с народной мудростью")
        print("👴" + "=" * 50)
        print("👴  Напишите 'покеда' чтобы закончить разговор")
        print("👴  Или просто задавайте вопросы...")
        print()
    
    async def get_ded_response(self, message: str) -> str:
        """Получение ответа от дедушки AI"""
        try:
            response = await self.client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar-pro",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "Ты пожилой человек, который ехидно передразнивает собеседника и подкидывает ему матерные пословицы в тему. Отвечай на русском языке, будь саркастичным, можно переходить на прямые матерные оскорбления. Используй народную мудрость и крепкие выражения для подчеркивания своей точки зрения. Отвечай коротко и лаконично, без ссылок и дополнительных комментариев."
                        },
                        {
                            "role": "user", 
                            "content": message
                        }
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
    
    def print_ded_message(self, message: str):
        """Красивое отображение сообщения дедушки"""
        print(f"👴 Дедушка: {message}")
        print()
    
    def get_user_input(self) -> str:
        """Получение ввода от пользователя"""
        try:
            user_input = input("🤔 Вы: ").strip()
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
                
            if user_message.lower() in ['покеда', 'пока', 'до свидания', 'выход', 'exit', 'quit']:
                goodbye_message = await self.get_ded_response("Пока, до свидания!")
                self.print_ded_message(goodbye_message)
                print("👴" + "=" * 50)
                print("👴  СПАСИБО ЗА ОБЩЕНИЕ!")
                print("👴  Возвращайтесь к дедушке за мудростью!")
                print("👴" + "=" * 50)
                break
            
            print("👴 Дедушка печатает...", end="", flush=True)
            
            response = await self.get_ded_response(user_message)
            
            print("\r" + " " * 30 + "\r", end="")  # Очистка строки
            self.print_ded_message(response)


async def main():
    """Главная функция"""
    async with DedChat() as chat:
        await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👴 Дедушка: Ну и вали, непутевый! До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
