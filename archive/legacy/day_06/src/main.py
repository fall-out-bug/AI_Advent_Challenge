"""
Main module for testing local models on logical riddles.

Coordinates the entire testing process: model availability check,
test execution, result analysis and report generation.
"""

import asyncio
import sys
import argparse
from typing import List

# Use absolute imports for script execution
try:
    from .model_client import LocalModelClient
    from .riddles import RiddleCollection
    from .report_generator import ReportGenerator
except ImportError:
    # If relative imports don't work, use absolute imports
    from model_client import LocalModelClient
    from riddles import RiddleCollection
    from report_generator import ReportGenerator


class ModelTester:
    """
    Main class for model testing.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    """
    
    def __init__(self, client: LocalModelClient = None):
        """
        Initialize tester with dependency injection.
        
        Args:
            client: Model client instance (optional, creates default if None)
        """
        self.client = client or LocalModelClient()
        self.riddle_collection = RiddleCollection()
        self.report_generator = ReportGenerator()
    
    async def run_tests(self, verbose: bool = True) -> None:
        """
        Run full testing cycle.
        
        Performs model availability check, riddle testing
        and report generation.
        
        Args:
            verbose: Whether to output model communication to console
        """
        print("🧠 Testing local models on logical riddles")
        print("=" * 60)
        
        try:
            # Check model availability
            await self._check_model_availability()
            
            # Get riddles
            riddles = self.riddle_collection.get_riddles()
            riddle_texts = self.riddle_collection.get_riddle_texts()
            riddle_titles = [riddle.title for riddle in riddles]
            
            print(f"\n📝 Found {len(riddles)} riddles for testing:")
            for i, riddle in enumerate(riddles, 1):
                print(f"  {i}. {riddle.title} (difficulty: {riddle.difficulty}/5)")
            
            # Run tests
            print(f"\n🚀 Starting testing...")
            test_results = await self.client.test_all_models(riddle_texts, verbose=verbose)
            
            if not test_results:
                print("❌ Failed to get test results")
                return
            
            print(f"✅ Got {len(test_results)} test results")
            
            # Generate report
            print("\n📊 Generating report...")
            comparison_results = self.report_generator.generate_comparison_results(
                test_results, riddle_titles, riddle_texts
            )
            
            report = self.report_generator.generate_markdown_report(comparison_results)
            report_filename = self.report_generator.save_report(report)
            
            print(f"✅ Report saved to file: {report_filename}")
            
            # Print console summary
            self._print_console_summary(comparison_results)
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            sys.exit(1)
        
        finally:
            await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.close()
    
    async def _check_model_availability(self) -> None:
        """Check availability of all models."""
        print("\n🔍 Checking model availability...")
        
        availability = await self.client.check_model_availability()
        
        available_models = []
        for model_name, is_available in availability.items():
            status = "✅ Available" if is_available else "❌ Unavailable"
            print(f"  {model_name}: {status}")
            
            if is_available:
                available_models.append(model_name)
        
        if not available_models:
            print("\n❌ No models available!")
            print("Make sure local models are running:")
            print("  cd ../local_models && docker-compose up -d")
            sys.exit(1)
        
        print(f"\n✅ Available models: {len(available_models)}")
    
    def _print_console_summary(self, results: List) -> None:
        """Print brief summary of results to console."""
        print("\n" + "=" * 60)
        print("📋 BRIEF SUMMARY OF RESULTS")
        print("=" * 60)
        
        # Group by models
        models = {}
        for result in results:
            if result.model_name not in models:
                models[result.model_name] = []
            models[result.model_name].append(result)
        
        for model_name, model_results in models.items():
            print(f"\n🤖 Model: {model_name}")
            print("-" * 40)
            
            avg_word_diff = sum(r.word_difference for r in model_results) / len(model_results)
            avg_direct_time = sum(r.direct_response_time for r in model_results) / len(model_results)
            avg_stepwise_time = sum(r.stepwise_response_time for r in model_results) / len(model_results)
            
            print(f"  Average word difference: {avg_word_diff:.1f}")
            print(f"  Average direct response time: {avg_direct_time:.2f}s")
            print(f"  Average stepwise response time: {avg_stepwise_time:.2f}s")
            
            # Analyze reasoning quality
            stepwise_with_logic = sum(
                1 for r in model_results 
                if r.stepwise_analysis['has_logical_keywords']
            )
            stepwise_with_structure = sum(
                1 for r in model_results 
                if r.stepwise_analysis['has_step_by_step']
            )
            
            print(f"  Stepwise answers with logic: {stepwise_with_logic}/{len(model_results)}")
            print(f"  Stepwise answers with structure: {stepwise_with_structure}/{len(model_results)}")
        
        print("\n" + "=" * 60)
        print("🎯 CONCLUSIONS:")
        print("=" * 60)
        
        # General conclusions
        total_results = len(results)
        if total_results == 0:
            print("No results for analysis")
            return
            
        avg_word_diff = sum(r.word_difference for r in results) / total_results
        
        if avg_word_diff > 0:
            print(f"✅ Stepwise answers are on average {avg_word_diff:.1f} words longer")
        else:
            print(f"⚠️  Stepwise answers are not always longer than direct ones")
        
        # Analyze logical reasoning
        stepwise_with_logic = sum(
            1 for r in results 
            if r.stepwise_analysis['has_logical_keywords']
        )
        logic_percentage = (stepwise_with_logic / total_results) * 100
        
        print(f"📊 {logic_percentage:.1f}% of stepwise answers contain logical keywords")
        
        print("\n📄 Detailed report saved in Markdown file")


async def main():
    """
    Main function for running tests.
    
    Following Python Zen: "Simple is better than complex"
    and proper resource management.
    """
    parser = argparse.ArgumentParser(description="Testing local models on logical riddles")
    parser.add_argument("--quiet", "-q", action="store_true", 
                       help="Disable verbose output of model communication")
    
    args = parser.parse_args()
    
    async with ModelTester() as tester:
        await tester.run_tests(verbose=not args.quiet)


if __name__ == "__main__":
    asyncio.run(main())
