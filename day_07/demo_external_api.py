#!/usr/bin/env python3
"""Demo script showing external API integration with agents."""

import asyncio
import logging
import os
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent))

from agents.core.code_generator import CodeGeneratorAgent
from agents.core.external_api_config import get_config, ProviderConfig, ProviderType
from communication.message_schema import CodeGenerationRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_external_api_integration():
    """Demonstrate external API integration with agents."""
    print("🤖 External API Integration Demo")
    print("=" * 50)
    
    # Check API keys
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_chadgpt = bool(os.getenv("CHADGPT_API_KEY"))
    
    print(f"🔑 API Keys Status:")
    print(f"   OpenAI: {'✅' if has_openai else '❌'}")
    print(f"   Anthropic: {'✅' if has_anthropic else '❌'}")
    print(f"   ChadGPT: {'✅' if has_chadgpt else '❌'}")
    
    if not has_openai and not has_anthropic and not has_chadgpt:
        print("\n⚠️  No API keys found. This demo will show configuration but skip actual API calls.")
        print("   Set OPENAI_API_KEY, ANTHROPIC_API_KEY, and/or CHADGPT_API_KEY to test external providers.")
    
    # Show current configuration
    print(f"\n⚙️  Current Configuration:")
    config = get_config()
    stats = config.get_stats()
    print(f"   Total providers: {stats['total_providers']}")
    print(f"   Enabled providers: {stats['enabled_providers']}")
    print(f"   Default provider: {stats['default_provider'] or 'None'}")
    
    # Demo 1: Local model (should always work)
    print(f"\n📝 Demo 1: Local Model Generation")
    print("-" * 35)
    
    try:
        generator = CodeGeneratorAgent(model_name="starcoder")
        print(f"✅ Created generator with local model: starcoder")
        
        request = CodeGenerationRequest(
            task_description="Create a simple function that adds two numbers",
            language="python",
            requirements=["Include type hints", "Add docstring"]
        )
        
        print("🔄 Generating code...")
        result = await generator.process(request)
        
        print(f"✅ Generated code ({result.tokens_used} tokens):")
        print("```python")
        print(result.generated_code)
        print("```")
        
        if result.tests:
            print(f"\n📋 Generated tests:")
            print("```python")
            print(result.tests)
            print("```")
        
    except Exception as e:
        print(f"❌ Local model demo failed: {e}")
    
    # Demo 2: External API (if available)
    if has_openai or has_anthropic or has_chadgpt:
        print(f"\n🌐 Demo 2: External API Generation")
        print("-" * 35)
        
        # Try ChadGPT if available (prioritize it)
        if has_chadgpt:
            try:
                print("🔄 Testing ChadGPT...")
                generator = CodeGeneratorAgent(
                    model_name="gpt-5-mini",
                    external_provider="chadgpt-real"
                )
                
                # Check availability
                if await generator.check_provider_availability():
                    print("✅ ChadGPT is available")
                    
                    request = CodeGenerationRequest(
                        task_description="Create a function that finds the longest common subsequence",
                        language="python",
                        requirements=["Use dynamic programming", "Include comprehensive tests"]
                    )
                    
                    print("🔄 Generating code with ChadGPT...")
                    result = await generator.process(request)
                    
                    print(f"✅ Generated code ({result.tokens_used} tokens):")
                    print("```python")
                    print(result.generated_code)
                    print("```")
                    
                else:
                    print("❌ ChadGPT is not available")
                    
            except Exception as e:
                print(f"❌ ChadGPT demo failed: {e}")
        
        # Try ChatGPT if available
        if has_openai:
            try:
                print("\n🔄 Testing ChatGPT...")
                generator = CodeGeneratorAgent(
                    model_name="gpt-3.5-turbo",
                    external_provider="chatgpt"
                )
                
                # Check availability
                if await generator.check_provider_availability():
                    print("✅ ChatGPT is available")
                    
                    request = CodeGenerationRequest(
                        task_description="Create a class for managing a binary search tree",
                        language="python",
                        requirements=["Include insert, delete, search methods", "Use proper error handling"]
                    )
                    
                    print("🔄 Generating code with ChatGPT...")
                    result = await generator.process(request)
                    
                    print(f"✅ Generated code ({result.tokens_used} tokens):")
                    print("```python")
                    print(result.generated_code)
                    print("```")
                    
                else:
                    print("❌ ChatGPT is not available")
                    
            except Exception as e:
                print(f"❌ ChatGPT demo failed: {e}")
        
        # Try Claude if available
        if has_anthropic:
            try:
                print("\n🔄 Testing Claude...")
                generator = CodeGeneratorAgent(
                    model_name="claude-3-sonnet-20240229",
                    external_provider="claude"
                )
                
                # Check availability
                if await generator.check_provider_availability():
                    print("✅ Claude is available")
                    
                    request = CodeGenerationRequest(
                        task_description="Create a data validation function",
                        language="python",
                        requirements=["Include comprehensive validation", "Use proper error handling"]
                    )
                    
                    print("🔄 Generating code with Claude...")
                    result = await generator.process(request)
                    
                    print(f"✅ Generated code ({result.tokens_used} tokens):")
                    print("```python")
                    print(result.generated_code)
                    print("```")
                    
                else:
                    print("❌ Claude is not available")
                    
            except Exception as e:
                print(f"❌ Claude demo failed: {e}")
    
    # Demo 3: Provider switching
    print(f"\n🔄 Demo 3: Dynamic Provider Switching")
    print("-" * 40)
    
    try:
        # Start with local model
        generator = CodeGeneratorAgent(model_name="starcoder")
        print(f"✅ Started with local model: {generator.get_provider_info()}")
        
        # Try to switch to external providers
        if has_openai:
            print("🔄 Switching to ChatGPT...")
            success = await generator.switch_to_external_provider("chatgpt")
            if success:
                print(f"✅ Switched to: {generator.get_provider_info()}")
            else:
                print("❌ Failed to switch to ChatGPT")
        
        if has_anthropic:
            print("🔄 Switching to Claude...")
            success = await generator.switch_to_external_provider("claude")
            if success:
                print(f"✅ Switched to: {generator.get_provider_info()}")
            else:
                print("❌ Failed to switch to Claude")
        
        # Switch back to local
        print("🔄 Switching back to local model...")
        success = await generator.switch_to_local_model("mistral")
        if success:
            print(f"✅ Switched to: {generator.get_provider_info()}")
        else:
            print("❌ Failed to switch to local model")
            
    except Exception as e:
        print(f"❌ Provider switching demo failed: {e}")
    
    # Demo 4: Configuration management
    print(f"\n⚙️  Demo 4: Configuration Management")
    print("-" * 35)
    
    try:
        config = get_config()
        
        # Show current providers
        print("📋 Current providers:")
        for name, provider_config in config.providers.items():
            status = "✅" if provider_config.enabled else "❌"
            print(f"   {status} {name}: {provider_config.provider_type.value} ({provider_config.model})")
        
        # Validate configuration
        print("\n🔍 Validating configuration...")
        validation_results = config.validate_config()
        
        if validation_results["valid"]:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration has issues:")
            for error in validation_results["errors"]:
                print(f"   • {error}")
            for warning in validation_results["warnings"]:
                print(f"   • {warning}")
        
        # Show statistics
        print(f"\n📊 Configuration statistics:")
        stats = config.get_stats()
        print(f"   Total providers: {stats['total_providers']}")
        print(f"   Enabled providers: {stats['enabled_providers']}")
        print(f"   Default provider: {stats['default_provider']}")
        
    except Exception as e:
        print(f"❌ Configuration demo failed: {e}")
    
    print(f"\n🎉 Demo completed!")
    print(f"\n📚 Next steps:")
    print(f"   1. Set up API keys: export OPENAI_API_KEY='your-key'")
    print(f"   2. Run examples: python examples/external_api_example.py")
    print(f"   3. Manage providers: python manage_providers.py --help")
    print(f"   4. Read guide: EXTERNAL_API_GUIDE.md")


if __name__ == "__main__":
    asyncio.run(demo_external_api_integration())
