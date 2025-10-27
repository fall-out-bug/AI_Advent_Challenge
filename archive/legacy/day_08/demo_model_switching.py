"""
Model Switching Demo - Base Implementation.

This module provides the core ModelSwitchingDemo class that orchestrates
model switching, token limit testing, compression evaluation, and quality analysis.

Following Python Zen principles:
- Beautiful is better than ugly
- Explicit is better than implicit
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.code_generator_adapter import CodeGeneratorAdapter
from agents.code_reviewer_adapter import CodeReviewerAdapter
from config.demo_config import get_config, get_model_config
from core.compression_evaluator import CompressionEvaluator
from core.model_switcher import ModelSwitcherOrchestrator
from core.quality_analyzer import QualityAnalyzer
from core.token_limit_tester import TokenLimitTester
from models.data_models import ExperimentResult, ThreeStageResult, CompressionTestResult
from utils.report_generator import ReportGenerator


class ModelSwitchingDemo:
    """
    Base model switching demo orchestrator.
    
    This class coordinates all components of the model switching demo including
    model orchestration, token limit testing, compression evaluation, and quality analysis.
    
    Attributes:
        config: Demo configuration dictionary
        orchestrator: Model switcher orchestrator
        token_tester: Token limit tester
        compression_evaluator: Compression evaluator
        quality_analyzer: Quality analyzer
        generator_adapter: Code generator adapter
        reviewer_adapter: Code reviewer adapter
        report_generator: Report generator
        results: Demo results dictionary
        logger: Logger instance
        
    Example:
        ```python
        from demo_model_switching import ModelSwitchingDemo
        
        # Initialize demo
        demo = ModelSwitchingDemo()
        
        # Run complete demo
        results = await demo.run_complete_demo()
        
        print(f"Demo completed with {len(results['models_tested'])} models")
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model switching demo.
        
        Args:
            config: Optional custom configuration dictionary
            
        Example:
            ```python
            from demo_model_switching import ModelSwitchingDemo
            
            # Initialize with default config
            demo = ModelSwitchingDemo()
            
            # Or with custom config
            custom_config = {"models": ["starcoder", "mistral"]}
            demo = ModelSwitchingDemo(custom_config)
            ```
        """
        # Load configuration
        self.config = config or get_config()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize core components
        self.orchestrator = ModelSwitcherOrchestrator(
            models=self.config["models"]
        )
        self.token_tester = TokenLimitTester()
        self.compression_evaluator = CompressionEvaluator()
        self.quality_analyzer = QualityAnalyzer()
        self.generator_adapter = CodeGeneratorAdapter()
        self.reviewer_adapter = CodeReviewerAdapter()
        self.report_generator = ReportGenerator()
        
        # Initialize results storage
        self.results = {
            "three_stage_results": {},
            "compression_results": {},
            "quality_results": {},
            "model_statistics": {},
            "summary": {}
        }
        
        self.logger.info("Initialized ModelSwitchingDemo")
    
    async def run_complete_demo(self) -> Dict[str, Any]:
        """
        Run the complete model switching demo.
        
        This method orchestrates the entire demo process including model availability
        checking, testing, compression evaluation, and report generation.
        
        Returns:
            Dictionary containing all demo results
            
        Example:
            ```python
            # Run complete demo
            results = await demo.run_complete_demo()
            
            print(f"Models tested: {len(results['models_tested'])}")
            print(f"Success rate: {results['summary']['success_rate']*100:.1f}%")
            ```
        """
        try:
            print("=" * 80)
            print("MODEL SWITCHING DEMO")
            print("=" * 80)
            
            # Check model availability
            await self._check_model_availability()
            
            # Test each model
            for model_name in self.config["models"]:
                await self._test_model(model_name)
            
            # Generate summary
            self._generate_summary()
            
            # Print results
            self._print_results()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            raise
        finally:
            # Always cleanup containers
            await self.orchestrator.cleanup_containers()
    
    async def _check_model_availability(self) -> None:
        """
        Check availability of all configured models.
        
        This method checks which models are available and updates the configuration
        to only test available models.
        """
        print("\n🔍 Checking model availability...")
        
        availability = await self.orchestrator.check_all_models_availability(
            start_containers=False
        )
        
        available_models = []
        for model, is_available in availability.items():
            if is_available:
                print(f"✅ {model} is available")
                available_models.append(model)
            else:
                print(f"❌ {model} is not available")
        
        # Test all configured models regardless of current availability
        print("🎯 Testing all configured models (will attempt to start unavailable models)")
        # Keep all configured models - don't filter by availability
        # self.config["models"] remains unchanged
        
        print(f"📊 Will test {len(self.config['models'])} models: {self.config['models']}")
    
    async def _test_model(self, model_name: str) -> None:
        """
        Test a specific model with comprehensive evaluation.
        
        Args:
            model_name: Name of the model to test
            
        Example:
            ```python
            await self._test_model("starcoder")
            ```
        """
        print(f"\n{'='*60}")
        print(f"Testing Model: {model_name.upper()}")
        print(f"{'='*60}")
        
        # Switch to model
        success = await self.orchestrator.switch_to_model(model_name)
        if not success:
            print(f"❌ Failed to switch to {model_name}")
            return
        
        print(f"✅ Successfully switched to {model_name}")
        
        try:
            # Run three-stage token limit test
            await self._run_three_stage_test(model_name)
            
            # Test compression strategies
            await self._test_compression_strategies(model_name)
            
            # Update model statistics
            self.results["model_statistics"][model_name] = self.orchestrator.get_model_statistics(model_name)
            
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
    
    async def _run_three_stage_test(self, model_name: str) -> None:
        """
        Run three-stage token limit test for a model.
        
        Args:
            model_name: Name of the model being tested
        """
        print(f"\n📊 Running three-stage token limit test...")
        
        result = await self.token_tester.run_three_stage_test(model_name)
        self.results["three_stage_results"][model_name] = result
        
        if result.success:
            print(f"✅ Three-stage test completed successfully")
            print(f"   Short query: {result.short_query_tokens} tokens")
            print(f"   Medium query: {result.medium_query_tokens} tokens")
            print(f"   Long query: {result.long_query_tokens} tokens")
            print(f"   Queries exceeding limit: {result.queries_exceeding_limit}")
        else:
            print(f"❌ Three-stage test failed: {result.error_message}")
    
    async def _test_compression_strategies(self, model_name: str) -> None:
        """
        Test compression strategies for a model.
        
        Args:
            model_name: Name of the model being tested
        """
        print(f"\n🗜️  Testing compression strategies...")
        
        # Get the three-stage result for this model
        three_stage_result = self.results["three_stage_results"].get(model_name)
        if not three_stage_result or not three_stage_result.success:
            print("⚠️  Skipping compression tests - three-stage test failed")
            return
        
        # Test compression on queries that exceed limits
        compression_algorithms = self.config.get("compression_algorithms", [
            "truncation", "keywords", "extractive", "semantic", "summarization"
        ])
        
        model_compression_results = {}
        
        for stage in ["short", "medium", "long"]:
            stage_results = {}
            exceeds_limit = getattr(three_stage_result, f"{stage}_exceeds_limit")
            
            if exceeds_limit:
                query = getattr(three_stage_result, f"{stage}_query")
                print(f"\n  Testing compression on {stage} query (exceeds limit)")
                
                for strategy in compression_algorithms:
                    result = await self.compression_evaluator.compress_and_test(
                        query, model_name, strategy
                    )
                    stage_results[strategy] = result
                    
                    if result.success:
                        print(f"    ✅ {strategy}: {result.compression_ratio:.2%} compression")
                    else:
                        print(f"    ❌ {strategy}: {result.error_message}")
            
            if stage_results:
                model_compression_results[stage] = stage_results
        
        if model_compression_results:
            self.results["compression_results"][model_name] = model_compression_results
        else:
            print("ℹ️  No compression tests needed - no queries exceed limits")
    
    def _generate_summary(self) -> None:
        """Generate summary of all demo results."""
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
        
        # Find best performing model
        best_model = None
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
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _print_results(self) -> None:
        """Print summary results."""
        summary = self.results["summary"]
        
        print(f"\n{'='*80}")
        print(f"📊 DEMO SUMMARY")
        print(f"{'='*80}")
        print(f"Models tested: {summary['models_tested']}")
        print(f"Total experiments: {summary['total_experiments']}")
        print(f"Successful experiments: {summary['successful_experiments']}")
        print(f"Success rate: {summary['success_rate']*100:.1f}%")
        print(f"Total compressions: {summary['total_compressions']}")
        print(f"Successful compressions: {summary['successful_compressions']}")
        print(f"Best performing model: {summary['best_model']}")
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


async def main():
    """
    Main function to run the model switching demo.
    
    Example:
        ```bash
        python demo_model_switching.py
        ```
    """
    try:
        print("🚀 Model Switching Demo - Day 08")
        print("=" * 80)
        
        demo = ModelSwitchingDemo()
        results = await demo.run_complete_demo()
        
        print(f"\n🎉 Demo completed successfully!")
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
