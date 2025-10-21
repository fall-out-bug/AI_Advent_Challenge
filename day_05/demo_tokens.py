#!/usr/bin/env python3
"""
Демонстрационный скрипт для показа работы с токенами в локальных моделях.
"""
import asyncio
import httpx
import time


async def demo_local_model():
    """Демонстрация работы с локальной моделью."""
    print("🤖 Демонстрация работы с локальными моделями")
    print("=" * 50)
    
    models = {
        "qwen": "http://localhost:8000",
        "mistral": "http://localhost:8001", 
        "tinyllama": "http://localhost:8002"
    }
    
    test_message = [
        {"role": "system", "content": "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
    
    for model_name, url in models.items():
        print(f"\n🔍 Тестирую модель: {model_name} ({url})")
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.post(
                    f"{url}/chat",
                    json={
                        "messages": test_message,
                        "max_tokens": 100,
                        "temperature": 0.7
                    }
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Ответ: {data['response']}")
                    print(f"📊 Токены: input={data.get('input_tokens', 0)}, response={data.get('response_tokens', 0)}, total={data.get('total_tokens', 0)}")
                    print(f"⏱️  Время: {duration_ms}ms ({duration_ms/1000:.2f}s)")
                else:
                    print(f"❌ Ошибка: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Демонстрация завершена!")
    print("Для полного тестирования запустите: python terminal_chat_v5.py")


if __name__ == "__main__":
    asyncio.run(demo_local_model())
