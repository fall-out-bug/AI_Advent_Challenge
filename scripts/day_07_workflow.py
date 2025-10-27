#!/usr/bin/env python3
"""Day 07 workflow: Multi-agent code generation and review."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from src.application.orchestrators.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
)
from src.domain.messaging.message_schema import OrchestratorRequest
from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent


class ModelClientAdapter:
    """Adapter to make UnifiedModelClient compatible with BaseAgent interface."""
    
    def __init__(self, unified_client, model_name: str = "starcoder"):
        """Initialize adapter.
        
        Args:
            unified_client: UnifiedModelClient instance
            model_name: Name of the model to use
        """
        self.unified_client = unified_client
        self.model_name = model_name
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.3
    ) -> dict:
        """Generate response compatible with BaseAgent interface.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Temperature
            
        Returns:
            Dictionary with 'response' and 'total_tokens' keys
        """
        response = await self.unified_client.make_request(
            model_name=self.model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "response": response.response,
            "total_tokens": response.total_tokens,
            "input_tokens": response.input_tokens,
            "response_tokens": response.response_tokens,
        }


async def main():
    """Run Day 07 multi-agent workflow."""
    print("\n" + "="*70)
    print("🤖 Day 07: Multi-Agent Workflow")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Import unified client
    try:
        from shared_package.clients.unified_client import UnifiedModelClient
    except ImportError as e:
        print(f"❌ Error: Could not import UnifiedModelClient: {e}")
        print("Please ensure shared package is available")
        return 1
    
    # Initialize model client
    unified_client = UnifiedModelClient()
    
    try:
        # Create agent adapters
        generator_adapter = ModelClientAdapter(
            unified_client, 
            model_name="starcoder"
        )
        reviewer_adapter = ModelClientAdapter(
            unified_client,
            model_name="mistral"
        )
        
        # Create agents with model clients
        generator = CodeGeneratorAgent(model_client=generator_adapter)
        reviewer = CodeReviewerAgent(model_client=reviewer_adapter)
        
        # Create orchestrator with agents
        orchestrator = MultiAgentOrchestrator(
            generator_agent=generator,
            reviewer_agent=reviewer
        )
        
        # Create workflow request
        request = OrchestratorRequest(
            task_description="Create a Python function to calculate factorial",
            requirements=[
                "Should handle edge cases (negative numbers, zero)",
                "Include type hints",
                "Include docstring"
            ],
            language="python",
            model_name="default",
            reviewer_model_name="mistral"
        )
        
        print("📝 Task: {}".format(request.task_description))
        print("   Requirements: {}".format(request.requirements))
        print("\n🚀 Running workflow (Generator → Reviewer)...\n")
        
        # Run the two-agent workflow
        result = await orchestrator.process_task(request)
        
        # Display results
        print("\n" + "="*70)
        print("📊 Workflow Results")
        print("="*70)
        print(f"Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        print(f"Time: {result.workflow_time:.2f}s")
        
        if result.success and result.generation_result:
            print("\n📦 Generated Code:")
            print("-"*70)
            code = result.generation_result.generated_code
            print(code[:400])
            if len(code) > 400:
                print("...")
            
            # Show tests if available
            if hasattr(result.generation_result, 'tests'):
                print("\n🧪 Tests:")
                tests = result.generation_result.tests
                print(tests[:400] if tests else "No tests generated")
        
        if result.success and result.review_result:
            print("\n⭐ Code Quality:")
            score = result.review_result.code_quality_score
            print(f"   Score: {score}/10")
            
            if hasattr(result.review_result, 'issues') and result.review_result.issues:
                print(f"   Issues found: {len(result.review_result.issues)}")
        
        # Show orchestrator statistics
        stats = orchestrator.get_stats()
        print("\n" + "="*70)
        print("📈 Orchestrator Statistics")
        print("="*70)
        print(f"   Total workflows: {stats['total_workflows']}")
        print(f"   Successful: {stats['successful_workflows']}")
        print(f"   Failed: {stats['failed_workflows']}")
        print(f"   Average time: {stats['average_workflow_time']:.2f}s")
        
        print("\n✅ Day 07 workflow completed!\n")
        return 0
        
    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await unified_client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

