#!/usr/bin/env python3
"""Quick demo of smart ChadGPT integration."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.smart_model_selector import get_smart_selector
from communication.message_schema import CodeGenerationRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def quick_demo():
    """Quick demo of smart ChadGPT features."""
    print("⚡ Quick Smart ChadGPT Demo")
    print("=" * 30)
    
    # Check API key
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    print(f"🔑 ChadGPT API: {'✅' if has_chadgpt else '❌'}")
    
    # Initialize smart selector
    selector = get_smart_selector()
    
    # Demo tasks
    tasks = [
        "Create a simple hello world function",
        "Implement a machine learning pipeline with data preprocessing",
        "Review this code for security vulnerabilities",
        "Write comprehensive unit tests for a sorting algorithm"
    ]
    
    print(f"\n🧠 Smart Model Recommendations:")
    print("-" * 35)
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📝 Task {i}: {task}")
        
        # Get recommendation
        recommendation = selector.recommend_model(task)
        
        print(f"🎯 Recommended: {recommendation.model}")
        print(f"📊 Confidence: {recommendation.confidence:.2f}")
        print(f"💭 Reason: {recommendation.reasoning}")
    
    # Demo with actual API if available
    if has_chadgpt:
        print(f"\n🤖 Live API Demo:")
        print("-" * 20)
        
        try:
            # Create generator
            generator = CodeGeneratorAgent(external_provider="chadgpt-real")
            
            # Test task
            task = "Create a simple calculator class with basic operations"
            print(f"📝 Task: {task}")
            
            # Get smart recommendation
            recommendation = generator.get_smart_model_recommendation(task)
            print(f"🎯 Smart recommendation: {recommendation.model}")
            print(f"💭 Reasoning: {recommendation.reasoning}")
            
            # Switch to smart model
            print("🔄 Switching to smart model...")
            success = await generator.switch_to_smart_model(task)
            
            if success:
                print("✅ Successfully switched to smart model")
                
                # Generate code
                request = CodeGenerationRequest(
                    task_description=task,
                    language="python"
                )
                
                print("🔄 Generating code...")
                result = await generator.process(request)
                
                print(f"✅ Generated {len(result.generated_code)} characters")
                print(f"📊 Tokens used: {result.tokens_used}")
                
                # Show code snippet
                print("\n📄 Generated code:")
                print("```python")
                print(result.generated_code)
                print("```")
                
            else:
                print("❌ Failed to switch to smart model")
                
        except Exception as e:
            print(f"❌ API demo failed: {e}")
    else:
        print(f"\n⏭️  Live API demo skipped (no API key)")
        print("   Set CHADGPT_API_KEY to test with real API calls")
    
    print(f"\n🎉 Quick demo completed!")
    print(f"\n📚 Key Features Demonstrated:")
    print(f"   • Smart model selection based on task analysis")
    print(f"   • Automatic switching to optimal models")
    print(f"   • Detailed recommendations with reasoning")
    print(f"   • Integration with ChadGPT's multiple models")


if __name__ == "__main__":
    asyncio.run(quick_demo())
