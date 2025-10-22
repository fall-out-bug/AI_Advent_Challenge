#!/usr/bin/env python3
"""
Demo script for testing local models.

This script shows how to use the local model testing system
on logical riddles.
"""

import asyncio
import sys
from pathlib import Path

# Add path to modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import ModelTester
from riddles import RiddleCollection
from model_client import LocalModelClient
from constants import QUICK_TIMEOUT


async def demo_riddle_collection():
    """Demo of riddle collection."""
    print("🧩 Riddle Collection Demo")
    print("=" * 50)
    
    collection = RiddleCollection()
    riddles = collection.get_riddles()
    
    for i, riddle in enumerate(riddles, 1):
        print(f"\n{i}. {riddle.title}")
        print(f"   Difficulty: {riddle.difficulty}/5")
        print(f"   Text: {riddle.text[:100]}...")
    
    print(f"\nTotal riddles: {len(riddles)}")


async def demo_model_client():
    """Demo of model client."""
    print("\n🤖 Model Client Demo")
    print("=" * 50)
    
    client = LocalModelClient(timeout=QUICK_TIMEOUT)
    
    try:
        # Check model availability
        print("Checking model availability...")
        availability = await client.check_model_availability()
        
        for model_name, is_available in availability.items():
            status = "✅ Available" if is_available else "❌ Unavailable"
            print(f"  {model_name}: {status}")
        
        # If there are available models, test one riddle
        available_models = [name for name, available in availability.items() if available]
        
        if available_models:
            print(f"\nTesting model {available_models[0]} on simple riddle...")
            collection = RiddleCollection()
            simple_riddle = collection.get_riddle_by_difficulty(1)[0]
            
            result = await client.test_riddle(simple_riddle.text, available_models[0])
            
            print(f"\nTest result:")
            print(f"  Model: {result.model_name}")
            print(f"  Direct answer: {result.direct_answer[:100]}...")
            print(f"  Stepwise answer: {result.stepwise_answer[:100]}...")
            print(f"  Direct response time: {result.direct_response_time:.2f}s")
            print(f"  Stepwise response time: {result.stepwise_response_time:.2f}s")
        else:
            print("\n⚠️  No available models for testing")
            print("Make sure local models are running:")
            print("  cd ../local_models && docker-compose up -d")
    
    finally:
        await client.close()


async def demo_full_testing():
    """Demo of full testing."""
    print("\n🚀 Full Testing Demo")
    print("=" * 50)
    
    tester = ModelTester()
    
    try:
        print("Running full testing cycle...")
        await tester.run_tests()
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure local models are running:")
        print("  cd ../local_models && docker-compose up -d")


async def main():
    """Main demo function."""
    print("🧠 Local Model Testing System Demo")
    print("=" * 60)
    
    # Demo riddle collection
    await demo_riddle_collection()
    
    # Demo client
    await demo_model_client()
    
    # Ask user if they want to run full testing
    print("\n" + "=" * 60)
    try:
        response = input("Run full testing of all models? (y/N): ").strip().lower()
        
        if response in ['y', 'yes', 'да']:
            await demo_full_testing()
        else:
            print("Full testing skipped.")
            print("To run use: make run")
    except EOFError:
        # If input is not available (e.g., in non-interactive mode)
        print("Full testing skipped (non-interactive mode).")
        print("To run use: make run")


if __name__ == "__main__":
    asyncio.run(main())
