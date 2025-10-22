"""
Клиент для работы с локальными языковыми моделями.

Предоставляет единообразный интерфейс для взаимодействия с различными
локальными моделями через HTTP API.
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import httpx


@dataclass
class ModelResponse:
    """Ответ от модели."""
    response: str
    response_tokens: int
    input_tokens: int
    total_tokens: int
    model_name: str
    response_time: float


@dataclass
class ModelTestResult:
    """Результат тестирования модели на загадке."""
    riddle: str
    model_name: str
    direct_answer: str
    stepwise_answer: str
    direct_response_time: float
    stepwise_response_time: float
    direct_tokens: int
    stepwise_tokens: int


class LocalModelClient:
    """Клиент для работы с локальными моделями."""
    
    # Маппинг моделей на порты согласно docker-compose.yml
    MODEL_PORTS = {
        "qwen": 8000,
        "mistral": 8001,
        "tinyllama": 8002
    }
    
    def __init__(self):
        """
        Инициализация клиента.
        """
        # Увеличиваем таймаут для длинных ответов
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def close(self):
        """Закрытие HTTP клиента."""
        await self.client.aclose()
    
    async def _make_request(
        self, 
        model_name: str, 
        prompt: str
    ) -> ModelResponse:
        """
        Выполнение запроса к модели.
        
        Args:
            model_name: Имя модели (qwen, mistral, tinyllama)
            prompt: Текст промпта
            
        Returns:
            ModelResponse: Ответ от модели
            
        Raises:
            httpx.HTTPError: Ошибка HTTP запроса
            ValueError: Неизвестная модель
        """
        if model_name not in self.MODEL_PORTS:
            raise ValueError(f"Неизвестная модель: {model_name}")
        
        port = self.MODEL_PORTS[model_name]
        url = f"http://localhost:{port}/chat"
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 10000,  # Очень большое значение
            "temperature": 0.7
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            data = response.json()
            
            return ModelResponse(
                response=data["response"],
                response_tokens=data["response_tokens"],
                input_tokens=data["input_tokens"],
                total_tokens=data["total_tokens"],
                model_name=model_name,
                response_time=response_time
            )
            
        except httpx.HTTPError as e:
            print(f"HTTP ошибка для {model_name}: {e}")
            raise httpx.HTTPError(f"Ошибка запроса к модели {model_name}: {e}")
        except Exception as e:
            print(f"Общая ошибка для {model_name}: {e}")
            raise Exception(f"Ошибка при работе с моделью {model_name}: {e}")
    
    async def test_riddle(
        self, 
        riddle: str, 
        model_name: str,
        verbose: bool = False
    ) -> ModelTestResult:
        """
        Тестирование модели на загадке в двух режимах.
        
        Args:
            riddle: Текст загадки
            model_name: Имя модели для тестирования
            verbose: Выводить ли общение с моделью в консоль
            
        Returns:
            ModelTestResult: Результат тестирования
        """
        if verbose:
            print(f"\n🤖 Тестирование модели {model_name}")
            print(f"📝 Загадка: {riddle}")
        
        # Прямой ответ
        direct_prompt = f"{riddle}\nОтвет:"
        if verbose:
            print(f"\n💬 Прямой запрос к {model_name}...")
        direct_response = await self._make_request(model_name, direct_prompt)
        
        if verbose:
            print(f"✅ Прямой ответ ({direct_response.response_time:.2f}s):")
            print(f"   {direct_response.response}")
        
        # Пошаговый ответ
        stepwise_prompt = f"{riddle}\nРешай пошагово и объясняй ход мыслей перед ответом."
        if verbose:
            print(f"\n🧠 Пошаговый запрос к {model_name}...")
        stepwise_response = await self._make_request(model_name, stepwise_prompt)
        
        if verbose:
            print(f"✅ Пошаговый ответ ({stepwise_response.response_time:.2f}s):")
            print(f"   {stepwise_response.response}")
            print("-" * 60)
        
        return ModelTestResult(
            riddle=riddle,
            model_name=model_name,
            direct_answer=direct_response.response,
            stepwise_answer=stepwise_response.response,
            direct_response_time=direct_response.response_time,
            stepwise_response_time=stepwise_response.response_time,
            direct_tokens=direct_response.response_tokens,
            stepwise_tokens=stepwise_response.response_tokens
        )
    
    async def test_all_models(self, riddles: List[str], verbose: bool = False) -> List[ModelTestResult]:
        """
        Тестирование всех моделей на всех загадках.
        
        Args:
            riddles: Список загадок для тестирования
            verbose: Выводить ли общение с моделями в консоль
            
        Returns:
            List[ModelTestResult]: Список результатов тестирования
        """
        results = []
        
        for model_name in self.MODEL_PORTS.keys():
            for riddle in riddles:
                try:
                    result = await self.test_riddle(riddle, model_name, verbose)
                    results.append(result)
                except Exception as e:
                    print(f"Ошибка при тестировании {model_name} на загадке: {e}")
                    continue
        
        return results
    
    async def check_model_availability(self) -> Dict[str, bool]:
        """
        Проверка доступности всех моделей.
        
        Returns:
            Dict[str, bool]: Статус доступности каждой модели
        """
        availability = {}
        
        for model_name, port in self.MODEL_PORTS.items():
            try:
                url = f"http://localhost:{port}/chat"
                response = await self.client.post(
                    url, 
                    json={
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1
                    }
                )
                availability[model_name] = response.status_code == 200
            except:
                availability[model_name] = False
        
        return availability
