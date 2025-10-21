#!/usr/bin/env python3
"""
Скрипт для проверки доступности локальных моделей.
"""
import asyncio
import httpx
import sys


LOCAL_MODELS = {
    "qwen": "http://localhost:8000",
    "mistral": "http://localhost:8001", 
    "tinyllama": "http://localhost:8002"
}


async def check_model(model_name: str, url: str) -> bool:
    """
    Purpose: Check if local model is available.
    Args:
        model_name: Name of the model
        url: URL of the model API
    Returns:
        bool: True if model is available
    """
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                f"{url}/chat",
                json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10,
                    "temperature": 0.7
                }
            )
            return response.status_code == 200
    except Exception:
        return False


async def main():
    """Check all local models."""
    print("🔍 Проверка доступности локальных моделей...")
    print()
    
    available_models = []
    
    for model_name, url in LOCAL_MODELS.items():
        print(f"Проверяю {model_name} ({url})...", end=" ")
        
        is_available = await check_model(model_name, url)
        
        if is_available:
            print("✅ доступна")
            available_models.append(model_name)
        else:
            print("❌ недоступна")
    
    print()
    
    if available_models:
        print(f"✅ Доступные модели: {', '.join(available_models)}")
        print("Можете запускать чат: python terminal_chat_v5.py")
    else:
        print("❌ Ни одна локальная модель не доступна!")
        print("Запустите модели: make run-models")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
