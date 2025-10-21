#!/usr/bin/env python3
"""
Демонстрационный скрипт для показа работы с историей сообщений в локальных моделях.
"""
import asyncio
import httpx
import time


async def demo_conversation_history():
    """Демонстрация работы с историей сообщений."""
    print("💬 Демонстрация работы с историей сообщений")
    print("=" * 60)
    
    # Тестируем с Qwen моделью
    url = "http://localhost:8000"
    
    print("🔍 Тестирую модель: qwen с историей сообщений")
    print()
    
    # Первое сообщение
    print("1️⃣ Первое сообщение:")
    messages1 = [
        {"role": "system", "content": "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично."},
        {"role": "user", "content": "Привет! Как дела?"}
    ]
    
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=None) as client:
            response1 = await client.post(
                f"{url}/chat",
                json={
                    "messages": messages1,
                    "max_tokens": 100,
                    "temperature": 0.7
                }
            )
            duration1 = int((time.time() - start_time) * 1000)
            
            if response1.status_code == 200:
                data1 = response1.json()
                print(f"👴 Дедушка: {data1['response']}")
                print(f"📊 Токены: input={data1.get('input_tokens', 0)}, response={data1.get('response_tokens', 0)}, total={data1.get('total_tokens', 0)}")
                print(f"⏱️  Время: {duration1}ms")
                print()
                
                # Второе сообщение с историей
                print("2️⃣ Второе сообщение (с историей):")
                messages2 = messages1 + [
                    {"role": "assistant", "content": data1['response']},
                    {"role": "user", "content": "А что ты думаешь о погоде?"}
                ]
                
                start_time = time.time()
                response2 = await client.post(
                    f"{url}/chat",
                    json={
                        "messages": messages2,
                        "max_tokens": 100,
                        "temperature": 0.7
                    }
                )
                duration2 = int((time.time() - start_time) * 1000)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"👴 Дедушка: {data2['response']}")
                    print(f"📊 Токены: input={data2.get('input_tokens', 0)}, response={data2.get('response_tokens', 0)}, total={data2.get('total_tokens', 0)}")
                    print(f"⏱️  Время: {duration2}ms")
                    print()
                    
                    # Третье сообщение с полной историей
                    print("3️⃣ Третье сообщение (с полной историей):")
                    messages3 = messages2 + [
                        {"role": "assistant", "content": data2['response']},
                        {"role": "user", "content": "Спасибо за ответ!"}
                    ]
                    
                    start_time = time.time()
                    response3 = await client.post(
                        f"{url}/chat",
                        json={
                            "messages": messages3,
                            "max_tokens": 100,
                            "temperature": 0.7
                        }
                    )
                    duration3 = int((time.time() - start_time) * 1000)
                    
                    if response3.status_code == 200:
                        data3 = response3.json()
                        print(f"👴 Дедушка: {data3['response']}")
                        print(f"📊 Токены: input={data3.get('input_tokens', 0)}, response={data3.get('response_tokens', 0)}, total={data3.get('total_tokens', 0)}")
                        print(f"⏱️  Время: {duration3}ms")
                        print()
                        
                        print("✅ Демонстрация успешно завершена!")
                        print("📈 История сообщений работает корректно:")
                        print(f"   • Сообщение 1: {len(messages1)} элементов")
                        print(f"   • Сообщение 2: {len(messages2)} элементов")
                        print(f"   • Сообщение 3: {len(messages3)} элементов")
                        print()
                        print("🎯 Локальные модели теперь поддерживают:")
                        print("   • Полную историю диалога")
                        print("   • Роли: system, user, assistant")
                        print("   • Отслеживание токенов")
                        print("   • Команду 'очисти историю' для сброса")
                    else:
                        print(f"❌ Ошибка в третьем сообщении: {response3.status_code}")
                else:
                    print(f"❌ Ошибка во втором сообщении: {response2.status_code}")
            else:
                print(f"❌ Ошибка в первом сообщении: {response1.status_code}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Демонстрация истории сообщений завершена!")
    print("Для полного тестирования запустите: python terminal_chat_v5.py")


if __name__ == "__main__":
    asyncio.run(demo_conversation_history())
