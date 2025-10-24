#!/usr/bin/env python3
"""
Quick test script for TechxGenus/starcoder2-7b-instruct model.
This script tests the model directly without the full orchestrator.
"""

import json
import time

import requests


def test_model_health():
    """Test if the model service is running and healthy."""
    try:
        response = requests.get("http://localhost:8003/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model service is healthy")
            print(f"📦 Model: {data.get('model', 'Unknown')}")
            return True
        else:
            print(f"❌ Model service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to model service: {e}")
        return False


def test_simple_generation():
    """Test simple code generation with the new model."""
    print("\n🧪 Testing Simple Code Generation")
    print("-" * 40)

    # Test prompt following the new format
    test_prompt = {
        "messages": [
            {
                "role": "user",
                "content": "Напиши функцию на Python для вычисления среднего значения списка чисел",
            }
        ],
        "max_tokens": 200,
        "temperature": 0.3,
    }

    try:
        print("📤 Sending request to model...")
        start_time = time.time()

        response = requests.post(
            "http://localhost:8003/chat", json=test_prompt, timeout=60
        )

        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generation successful!")
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"🎯 Tokens used: {data.get('total_tokens', 0)}")

            print("\n📝 Generated Code:")
            print("-" * 20)
            print(data.get("response", "No response"))

            return True
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def test_instruction_format():
    """Test the instruction format specifically."""
    print("\n🎯 Testing Instruction Format")
    print("-" * 40)

    # Test with system and user messages
    test_prompt = {
        "messages": [
            {
                "role": "system",
                "content": "Ты эксперт по программированию на Python. Пиши чистый, хорошо документированный код.",
            },
            {
                "role": "user",
                "content": "Создай функцию для проверки, является ли число простым",
            },
        ],
        "max_tokens": 300,
        "temperature": 0.2,
    }

    try:
        print("📤 Testing instruction format...")

        response = requests.post(
            "http://localhost:8003/chat", json=test_prompt, timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Instruction format test successful!")

            print("\n📝 Generated Code:")
            print("-" * 20)
            print(data.get("response", "No response"))

            return True
        else:
            print(
                f"❌ Instruction format test failed with status {response.status_code}"
            )
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Instruction format test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 TechxGenus/StarCoder2-7B-Instruct Quick Test")
    print("=" * 60)

    # Test 1: Health check
    if not test_model_health():
        print("\n❌ Model service is not available. Please check:")
        print("• Is the Docker container running?")
        print("• Is the service accessible on port 8003?")
        print("• Check logs: docker-compose logs starcoder-chat")
        return

    # Test 2: Simple generation
    simple_success = test_simple_generation()

    # Test 3: Instruction format
    instruction_success = test_instruction_format()

    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"Health Check: ✅")
    print(f"Simple Generation: {'✅' if simple_success else '❌'}")
    print(f"Instruction Format: {'✅' if instruction_success else '❌'}")

    if simple_success and instruction_success:
        print("\n🎉 All tests passed! The new model is working correctly.")
        print("\n💡 Next steps:")
        print("• Run the full orchestrator test: python test_new_model.py")
        print("• Test with the demo: python demo.py")
    else:
        print("\n⚠️  Some tests failed. Please check the model configuration.")
        print("\n🔧 Troubleshooting:")
        print("• Check Docker logs: docker-compose logs starcoder-chat")
        print("• Verify model name in docker-compose.yml")
        print("• Restart the service: docker-compose restart starcoder-chat")


if __name__ == "__main__":
    main()
