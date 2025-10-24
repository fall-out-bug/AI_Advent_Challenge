#!/usr/bin/env python3
"""
Test script for TechxGenus/starcoder2-7b-instruct model integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from communication.message_schema import OrchestratorRequest
from orchestrator import MultiAgentOrchestrator, process_simple_task

# Use environment variables for URLs with fallbacks
DEMO_GENERATOR_URL = os.getenv("GENERATOR_URL", "http://generator.localhost")
DEMO_REVIEWER_URL = os.getenv("REVIEWER_URL", "http://reviewer.localhost")


async def test_new_model():
    """Test the new TechxGenus/starcoder2-7b-instruct model."""
    print("🚀 Testing TechxGenus/starcoder2-7b-instruct Model")
    print("=" * 60)

    # Simple test task
    task = "Напиши функцию на Python для вычисления среднего значения списка чисел"

    try:
        result = await process_simple_task(
            task_description=task,
            language="python",
            requirements=["Handle edge cases", "Include type hints", "Add docstring"],
            generator_url=DEMO_GENERATOR_URL,
            reviewer_url=DEMO_REVIEWER_URL,
        )

        if result.success:
            print(f"✅ Test completed successfully!")
            print(f"⏱️  Workflow time: {result.workflow_time:.2f}s")
            print(
                f"📊 Code quality score: {result.review_result.code_quality_score}/10"
            )
            print(f"🔍 Issues found: {len(result.review_result.issues)}")
            print(f"💡 Recommendations: {len(result.review_result.recommendations)}")

            print("\n📝 Generated Code:")
            print("-" * 30)
            print(result.generation_result.generated_code)

            print("\n🧪 Generated Tests:")
            print("-" * 30)
            print(result.generation_result.tests)

            if result.review_result.issues:
                print("\n🔍 Review Issues:")
                print("-" * 30)
                for issue in result.review_result.issues:
                    print(f"• {issue}")

            if result.review_result.recommendations:
                print("\n💡 Recommendations:")
                print("-" * 30)
                for rec in result.review_result.recommendations:
                    print(f"• {rec}")
        else:
            print(f"❌ Test failed: {result.error_message}")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("• Make sure StarCoder service is running on port 8003")
        print("• Make sure agent services are running on ports 9001 and 9002")
        print("• Check the logs for detailed error information")


async def test_direct_model_call():
    """Test direct model call to verify the new model works."""
    print("\n🔧 Testing Direct Model Call")
    print("=" * 40)
    
    try:
        from agents.core.model_client_adapter import ModelClientAdapter
        
        # Test direct model call
        adapter = ModelClientAdapter(model_name="starcoder", timeout=60.0)
        
        # Check if model is available
        is_available = await adapter.check_availability()
        print(f"Model available: {is_available}")
        
        if is_available:
            # Test simple generation
            response = await adapter.make_request(
                prompt="### Instruction\nНапиши функцию на Python для вычисления среднего значения списка чисел.\n### Response\n",
                max_tokens=200,
                temperature=0.3
            )
            
            print(f"Response: {response.get('response', 'No response')}")
            print(f"Tokens used: {response.get('total_tokens', 0)}")
        
        await adapter.close()
        
    except Exception as e:
        print(f"❌ Direct model test failed: {str(e)}")


async def main():
    """Main test function."""
    print("🌟 TechxGenus/StarCoder2-7B-Instruct Model Test")
    print("=" * 60)

    try:
        # Test 1: Direct model call
        await test_direct_model_call()
        
        # Test 2: Full orchestrator test
        await test_new_model()

        print("\n🎉 All tests completed!")
        print("\n💡 Next steps:")
        print("• Check the 'results/' directory for saved workflow results")
        print("• Monitor agent health with the status endpoints")
        print("• Test with more complex tasks to verify model performance")

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
