#!/usr/bin/env python3
"""
Демонстрационный скрипт для показа единообразного переключения API.
"""
import asyncio
import httpx
import time


async def demo_api_switching():
    """Демонстрация единообразного переключения API."""
    print("🔄 Демонстрация единообразного переключения API")
    print("=" * 60)
    
    # Доступные API
    external_apis = ["chadgpt", "perplexity"]
    local_models = ["qwen", "mistral", "tinyllama"]
    
    print("📋 Доступные API:")
    print("  Внешние:")
    for api in external_apis:
        print(f"    • api {api}")
    print("  Локальные:")
    for model in local_models:
        print(f"    • api local-{model}")
    
    print("\n🔍 Примеры команд переключения:")
    
    # Демонстрация переключения на локальные модели
    for model in local_models:
        print(f"\n🤔 Вы [T=0.70 • local:qwen]: api local-{model}")
        print(f"👴 Дедушка: Переключаюсь на локальную модель {model}!")
        
        # Проверим доступность модели
        url = f"http://localhost:{8000 + local_models.index(model)}"
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
                if response.status_code == 200:
                    print(f"✅ Модель {model} доступна на {url}")
                else:
                    print(f"❌ Модель {model} недоступна (статус: {response.status_code})")
        except Exception as e:
            print(f"❌ Модель {model} недоступна: {e}")
    
    # Демонстрация переключения на внешние API
    print(f"\n🤔 Вы [T=0.70 • local:qwen]: api perplexity")
    print("👴 Дедушка: Переключаюсь на perplexity!")
    print("✅ Внешний API perplexity (требует настройки ключа)")
    
    print(f"\n🤔 Вы [T=0.70 • perplexity:sonar-pro]: api chadgpt")
    print("👴 Дедушка: Переключаюсь на chadgpt!")
    print("✅ Внешний API chadgpt (требует настройки ключа)")
    
    print("\n" + "=" * 60)
    print("🎉 Единообразное переключение API готово!")
    print("Теперь все API переключаются одинаково: api <provider>")
    print("Для полного тестирования запустите: python terminal_chat_v5.py")


if __name__ == "__main__":
    asyncio.run(demo_api_switching())
