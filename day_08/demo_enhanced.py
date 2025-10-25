"""
Enhanced Model Switching Demo with Comprehensive Testing.

This module provides an enhanced demo that tests each model independently with
queries that significantly exceed token limits, tests all compression strategies
on all queries, displays detailed outputs including query content and model
responses, and adds human-readable pacing with delays.

Following Python Zen principles:
- Beautiful is better than ugly
- Explicit is better than implicit
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

import asyncio
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from demo_model_switching import ModelSwitchingDemo
from config.demo_config import get_config, get_model_config


class EnhancedModelSwitchingDemo(ModelSwitchingDemo):
    """
    Enhanced demo with detailed output and human-readable pacing.
    
    This class extends the base ModelSwitchingDemo to provide comprehensive
    testing with large queries, detailed output, and user-friendly pacing.
    
    Attributes:
        Inherits all attributes from ModelSwitchingDemo
        display_config: Configuration for demo display settings
        
    Example:
        ```python
        from demo_enhanced import EnhancedModelSwitchingDemo
        
        # Initialize enhanced demo
        demo = EnhancedModelSwitchingDemo()
        
        # Run comprehensive demo
        results = await demo.run_enhanced_demo()
        
        print(f"Demo completed with {len(results['models_tested'])} models")
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced model switching demo.
        
        Args:
            config: Optional custom configuration
            
        Example:
            ```python
            from demo_enhanced import EnhancedModelSwitchingDemo
            
            # Initialize with default config
            demo = EnhancedModelSwitchingDemo()
            
            # Or with custom config
            custom_config = {"models": ["starcoder", "mistral"]}
            demo = EnhancedModelSwitchingDemo(custom_config)
            ```
        """
        super().__init__(config)
        self.display_config = self.config.get("demo_display", {})
        self.logger.info("Initialized EnhancedModelSwitchingDemo")
    
    async def run_enhanced_demo(self) -> Dict[str, Any]:
        """
        Run enhanced demo with detailed output and comprehensive testing.
        
        Returns:
            Dictionary containing all demo results with detailed information
            
        Example:
            ```python
            # Run enhanced demo
            results = await demo.run_enhanced_demo()
            
            print(f"Models tested: {len(results['models_tested'])}")
            print(f"Total experiments: {results['summary']['total_experiments']}")
            ```
        """
        print("=" * 80)
        print("ENHANCED MODEL SWITCHING DEMO")
        print("Testing models with large queries exceeding token limits")
        print("=" * 80)
        
        await self._pause("Initializing enhanced demo...", 1.0)
        
        # Check model availability and start testing all configured models
        await self._check_model_availability()
        
        # Test each model independently with comprehensive testing
        for model_name in self.config["models"]:
            await self._test_model_enhanced(model_name)
            await self._pause(f"Completed testing {model_name}", 
                            self.display_config.get("pause_between_models", 3.0))
        
        # Generate comprehensive summary
        self._generate_enhanced_summary()
        
        # Print detailed results
        self._print_enhanced_results()
        
        # Generate comprehensive markdown report
        report_path = self._generate_markdown_report()
        print(f"\n📄 Full report saved to: {report_path}")
        
        return self.results
    
    async def _check_model_availability(self) -> None:
        """Check availability of all configured models."""
        print("\n🔍 Checking model availability...")
        
        # Don't start containers during availability check
        availability = await self.orchestrator.check_all_models_availability(start_containers=False)
        
        available_models = []
        for model, is_available in availability.items():
            if is_available:
                print(f"✅ {model} is available")
                available_models.append(model)
            else:
                print(f"❌ {model} is not available")
        
        # If specific models were requested, only test those (even if not available)
        if len(self.config["models"]) == 1:
            requested_model = self.config["models"][0]
            print(f"🎯 Testing specific model: {requested_model}")
            if requested_model not in available_models:
                print(f"⚠️  {requested_model} is not available, but will attempt to start it during testing.")
            # Keep only the requested model
            self.config["models"] = [requested_model]
        else:
            # Test all configured models regardless of current availability
            print("🎯 Testing all configured models (will attempt to start unavailable models)")
            # Keep all configured models - don't filter by availability
            # self.config["models"] remains unchanged
        
        print(f"📊 Will test {len(self.config['models'])} models: {self.config['models']}")

    async def _pause(self, message: str, seconds: float) -> None:
        """
        Add human-readable pause with message.
        
        Args:
            message: Message to display during pause
            seconds: Duration of pause in seconds
            
        Example:
            ```python
            await self._pause("Processing...", 2.0)
            ```
        """
        print(f"\n{message}")
        print(f"⏳ Pausing for {seconds}s...")
        await asyncio.sleep(seconds)
    
    
    async def _test_model_enhanced(self, model_name: str) -> None:
        """
        Test model with detailed output and comprehensive testing.
        
        Args:
            model_name: Name of the model to test
            
        Example:
            ```python
            await self._test_model_enhanced("starcoder")
            ```
        """
        print(f"\n{'='*80}")
        print(f"MODEL: {model_name.upper()}")
        print(f"{'='*80}")
        
        # Show model configuration
        model_config = get_model_config(model_name)
        print(f"Max Tokens: {model_config.get('max_tokens', 'Unknown')}")
        print(f"Recommended Input: {model_config.get('recommended_input', 'Unknown')}")
        
        await self._pause("Switching to model...", 1.0)
        
        # Switch to model
        success = await self.orchestrator.switch_to_model(model_name)
        if not success:
            print(f"❌ Failed to switch to {model_name}")
            return
        
        print(f"✅ Successfully switched to {model_name}")
        
        try:
            # Run three-stage tests with detailed output
            await self._run_three_stage_detailed(model_name)
            
            # Test compression on ALL queries
            await self._test_all_compressions_detailed(model_name)
            
        finally:
            # Always stop the current model container after testing
            if self.orchestrator.use_container_management and self.orchestrator.docker_manager:
                if model_name in self.orchestrator.running_containers:
                    print(f"\n🛑 Stopping {model_name} container...")
                    stop_success = await self.orchestrator.docker_manager.stop_model(model_name, timeout=30)
                    if stop_success:
                        self.orchestrator.running_containers.discard(model_name)
                        print(f"✅ Successfully stopped {model_name}")
                    else:
                        print(f"⚠️  Failed to stop {model_name}, continuing anyway")
            
            # Clear current model
            self.orchestrator.current_model = None
    
    async def _run_three_stage_detailed(self, model_name: str) -> None:
        """
        Run three-stage test with detailed query and response output.
        
        Args:
            model_name: Name of the model being tested
        """
        print(f"\n📊 THREE-STAGE TOKEN LIMIT TESTING")
        print("-" * 80)
        
        result = await self.token_tester.run_three_stage_test(model_name)
        self.results["three_stage_results"][model_name] = result
        
        if not result.success:
            print(f"❌ Three-stage test failed: {result.error_message}")
            return
        
        for stage in ["short", "medium", "long"]:
            await self._show_stage_details(stage, result, model_name)
            await self._pause(f"Completed {stage} stage", 1.5)
    
    async def _show_stage_details(self, stage: str, result, model_name: str) -> None:
        """
        Show detailed information for each stage.
        
        Args:
            stage: Stage name (short/medium/long)
            result: ThreeStageResult object
            model_name: Name of the model
        """
        print(f"\n🔍 {stage.upper()} QUERY TEST")
        
        query = getattr(result, f"{stage}_query")
        tokens = getattr(result, f"{stage}_query_tokens")
        exceeds = getattr(result, f"{stage}_exceeds_limit")
        
        print(f"Token Count: {tokens}")
        print(f"Exceeds Limit: {'YES' if exceeds else 'NO'}")
        
        # Show query preview
        preview_length = self.display_config.get("show_query_preview", 200)
        print(f"\nQuery Preview (first {preview_length} chars):")
        print(f"{query[:preview_length]}...")
        print(f"\nFull query length: {len(query)} characters")
        
        # Show model limits comparison
        model_limits = result.model_limits
        print(f"Model limit: {model_limits.max_input_tokens}")
        print(f"Token usage: {tokens}/{model_limits.max_input_tokens} ({tokens/model_limits.max_input_tokens*100:.1f}%)")
    
    async def _test_all_compressions_detailed(self, model_name: str) -> None:
        """
        Test all compression strategies on long/heavy queries only.
        
        Args:
            model_name: Name of the model being tested
        """
        print(f"\n🗜️  COMPRESSION TESTING ON HEAVY QUERIES")
        print("-" * 80)
        
        result = self.results["three_stage_results"][model_name]
        
        # Only test compression on "long" query that exceeds limits
        if result.long_exceeds_limit:
            query = result.long_query
            print(f"\n📦 Testing compressions on LONG query (exceeds limit)")
        else:
            # Force compression testing even when query doesn't exceed limit
            query = result.long_query
            print(f"\n📦 Testing compressions on LONG query (forced testing)")
        
        # Test all compression strategies
        compression_algorithms = self.config.get("compression_algorithms", [
            "truncation", "keywords", "extractive", "semantic", "summarization"
        ])
        
        for strategy in compression_algorithms:
            await self._test_single_compression_detailed(query, model_name, strategy, "long")
            await self._pause(f"Completed {strategy} compression", 1.0)
    
    async def _test_single_compression_detailed(self, query: str, model_name: str, 
                                               strategy: str, stage: str) -> None:
        """
        Test single compression with full output details.
        
        Args:
            query: Original query text
            model_name: Name of the model
            strategy: Compression strategy name
            stage: Query stage (short/medium/long)
        """
        print(f"\n  Strategy: {strategy}")
        
        try:
            # Perform compression
            compression_result = await self.compression_evaluator.compress_and_test(
                query, model_name, strategy
            )
            
            if compression_result.success:
                print(f"  ✅ Success")
                print(f"  Original tokens: {compression_result.original_tokens}")
                print(f"  Compressed tokens: {compression_result.compressed_tokens}")
                print(f"  Compression ratio: {compression_result.compression_ratio:.2%}")
                print(f"  Response time: {compression_result.response_time:.2f}s")
                
                # Show compressed query preview
                preview_length = self.display_config.get("show_query_preview", 200)
                print(f"\n  Compressed query preview:")
                print(f"  {compression_result.compressed_query[:preview_length]}...")
                
                # Show model response preview
                response_preview_length = self.display_config.get("show_response_preview", 500)
                print(f"\n  Model response preview:")
                print(f"  {compression_result.response[:response_preview_length]}...")
                
                # Display generator and reviewer agent outputs
                await self._display_generator_output(compression_result, stage)
                await self._display_reviewer_output(
                    compression_result.response, 
                    query, 
                    model_name, 
                    strategy
                )
                
                # Store results
                if model_name not in self.results["compression_results"]:
                    self.results["compression_results"][model_name] = {}
                if stage not in self.results["compression_results"][model_name]:
                    self.results["compression_results"][model_name][stage] = {}
                
                self.results["compression_results"][model_name][stage][strategy] = compression_result
                
            else:
                print(f"  ❌ Failed: {compression_result.error_message}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.logger.error(f"Compression test failed for {strategy}: {e}")
    
    def _generate_enhanced_summary(self) -> None:
        """Generate comprehensive summary of all results."""
        models_tested = list(self.results["three_stage_results"].keys())
        
        total_experiments = 0
        successful_experiments = 0
        total_compressions = 0
        successful_compressions = 0
        
        for model_name in models_tested:
            # Count three-stage experiments
            if model_name in self.results["three_stage_results"]:
                total_experiments += 3
                if self.results["three_stage_results"][model_name].success:
                    successful_experiments += 3
            
            # Count compression experiments
            if model_name in self.results["compression_results"]:
                model_compressions = self.results["compression_results"][model_name]
                for stage, stage_compressions in model_compressions.items():
                    total_compressions += len(stage_compressions)
                    successful_compressions += sum(
                        1 for comp in stage_compressions.values() 
                        if hasattr(comp, 'success') and comp.success
                    )
        
        # Find best performing model and compression strategy
        best_model = None
        best_compression = None
        
        if self.results["model_statistics"]:
            best_model = max(
                self.results["model_statistics"].keys(),
                key=lambda m: self.results["model_statistics"][m]["successful_requests"]
            )
        
        # Calculate overall success rate
        overall_success_rate = (successful_experiments + successful_compressions) / max(1, total_experiments + total_compressions)
        
        self.results["summary"] = {
            "models_tested": len(models_tested),
            "total_experiments": total_experiments + total_compressions,
            "successful_experiments": successful_experiments + successful_compressions,
            "success_rate": overall_success_rate,
            "total_compressions": total_compressions,
            "successful_compressions": successful_compressions,
            "best_model": best_model,
            "best_compression": best_compression,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _display_generator_output(self, result, stage: str) -> None:
        """
        Display code generator agent output with formatted code preview.
        
        Args:
            result: Compression result containing generated code
            stage: Current testing stage (short/medium/long)
            
        Example:
            ```python
            await self._display_generator_output(compression_result, "long")
            ```
        """
        print(f"\n  🤖 GENERATOR OUTPUT:")
        response_preview = self.display_config.get("show_response_preview", 500)
        print(f"  Generated code (first {response_preview} chars):")
        print(f"  {result.response[:response_preview]}...")
        if len(result.response) > response_preview:
            print(f"  (Total length: {len(result.response)} characters)")
    
    async def _display_reviewer_output(self, code: str, query: str, model: str, strategy: str) -> None:
        """
        Display code reviewer agent analysis with quality metrics.
        
        Args:
            code: Generated code to review
            query: Original query that generated the code
            model: Model name used for generation
            strategy: Compression strategy used
            
        Example:
            ```python
            await self._display_reviewer_output(
                generated_code, original_query, "starcoder", "semantic"
            )
            ```
        """
        print(f"\n  🔍 REVIEWER ANALYSIS:")
        
        try:
            # Check if reviewer adapter is available
            if not hasattr(self.reviewer_adapter, 'review_code_quality'):
                print(f"  ⚠️  Reviewer adapter not properly initialized")
                return
                
            quality = await self.reviewer_adapter.review_code_quality(
                code, query, model
            )
            
            if quality:
                print(f"  Code Quality Score: {quality.code_quality_score:.2f}")
                print(f"  PEP8 Compliance: {'Yes' if quality.pep8_compliance else 'No'}")
                print(f"  Has Docstrings: {'Yes' if quality.has_docstrings else 'No'}")
                print(f"  Has Type Hints: {'Yes' if quality.has_type_hints else 'No'}")
                print(f"  Test Coverage: {quality.test_coverage}")
                print(f"  Complexity Score: {quality.complexity_score:.2f}")
                print(f"  Requirements Coverage: {quality.requirements_coverage:.2f}")
                print(f"  Completeness Score: {quality.completeness_score:.2f}")
            else:
                print(f"  ⚠️  Reviewer not available (SDK dependencies missing)")
        except Exception as e:
            print(f"  ⚠️  Reviewer error: {str(e)}")
            if "SDK agent not available" in str(e):
                print(f"  💡 Note: SDK CodeReviewerAgent dependencies are missing")

    def _print_enhanced_results(self) -> None:
        """Print comprehensive summary results."""
        summary = self.results["summary"]
        
        print(f"\n{'='*80}")
        print(f"📊 ENHANCED DEMO SUMMARY")
        print(f"{'='*80}")
        print(f"Models tested: {summary['models_tested']}")
        print(f"Total experiments: {summary['total_experiments']}")
        print(f"Successful experiments: {summary['successful_experiments']}")
        print(f"Success rate: {summary['success_rate']*100:.1f}%")
        print(f"Total compressions: {summary['total_compressions']}")
        print(f"Successful compressions: {summary['successful_compressions']}")
        print(f"Best performing model: {summary['best_model']}")
        print(f"Best compression strategy: {summary['best_compression']}")
        print(f"Completed at: {summary['timestamp']}")
        
        # Show detailed model results
        print(f"\n📈 DETAILED MODEL RESULTS:")
        print("-" * 80)
        
        for model_name in self.results["three_stage_results"]:
            print(f"\n🔧 {model_name.upper()}:")
            
            # Three-stage results
            three_stage = self.results["three_stage_results"][model_name]
            if three_stage.success:
                print(f"  Short query: {three_stage.short_query_tokens} tokens")
                print(f"  Medium query: {three_stage.medium_query_tokens} tokens")
                print(f"  Long query: {three_stage.long_query_tokens} tokens")
                print(f"  Queries exceeding limit: {three_stage.queries_exceeding_limit}")
            
            # Compression results
            if model_name in self.results["compression_results"]:
                model_compressions = self.results["compression_results"][model_name]
                print(f"  Compression tests: {len(model_compressions)} stages")
                
                for stage, stage_compressions in model_compressions.items():
                    successful = sum(1 for comp in stage_compressions.values() 
                                    if hasattr(comp, 'success') and comp.success)
                    print(f"    {stage}: {successful}/{len(stage_compressions)} successful")
    
    def _generate_markdown_report(self) -> str:
        """
        Generate and save comprehensive markdown report.
        
        Returns:
            Path to the generated report file
            
        Example:
            ```python
            report_path = self._generate_markdown_report()
            print(f"Report saved to: {report_path}")
            ```
        """
        from utils.demo_report_generator import DemoReportGenerator
        
        generator = DemoReportGenerator()
        report_content = generator.generate_report(self.results)
        
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"demo_report_{timestamp}.md"
        
        # Write report to file
        report_path.write_text(report_content, encoding='utf-8')
        
        return str(report_path)


async def main():
    """
    Main function to run the enhanced model switching demo.
    
    Example:
        ```bash
        python demo_enhanced.py
        python demo_enhanced.py --model starcoder
        python demo_enhanced.py --model tinyllama
        ```
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced Model Switching Demo')
    parser.add_argument('--model', type=str, help='Specific model to test (starcoder, mistral, qwen, tinyllama)')
    parser.add_argument('--all', action='store_true', help='Test all available models')
    args = parser.parse_args()
    
    try:
        print("🚀 Enhanced Model Switching Demo - Day 08")
        print("=" * 80)
        print("This enhanced demo will:")
        print("1. Test models with large queries exceeding token limits")
        print("2. Test ALL compression strategies on ALL query sizes")
        print("3. Show detailed output with query, response, and agent analysis")
        print("4. Display both generator and reviewer agent outputs")
        print("5. Provide human-readable pacing with delays")
        print("6. Generate comprehensive reports")
        print("=" * 80)
        
        # Determine which models to test
        if args.model:
            print(f"🎯 Testing specific model: {args.model}")
            config = get_config()
            config["models"] = [args.model]
            demo = EnhancedModelSwitchingDemo(config)
        elif args.all:
            print("🎯 Testing all available models")
            demo = EnhancedModelSwitchingDemo()
        else:
            print("🎯 Testing available models (use --model <name> for specific model)")
            demo = EnhancedModelSwitchingDemo()
        
        results = await demo.run_enhanced_demo()
        
        print(f"\n🎉 Enhanced demo completed successfully!")
        print(f"📊 Tested {len(results.get('models_tested', []))} models")
        print(f"🧪 Ran {results['summary']['total_experiments']} experiments")
        print(f"✅ Success rate: {results['summary']['success_rate']*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
