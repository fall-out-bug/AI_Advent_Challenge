"""
Model Switching Demo - Complete workflow implementation.

This module orchestrates the full workflow: model switching, three-stage testing,
compression evaluation, and quality analysis for comprehensive model comparison.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from agents.code_generator_adapter import CodeGeneratorAdapter
from agents.code_reviewer_adapter import CodeReviewerAdapter
from config.demo_config import (
    get_config, 
    get_model_config, 
    get_quality_thresholds,
    get_compression_algorithms,
    get_task_template,
    is_model_supported
)
from core.compression_evaluator import CompressionEvaluator
from core.model_switcher import ModelSwitcherOrchestrator
from core.quality_analyzer import QualityAnalyzer
from core.token_limit_tester import TokenLimitTester
from models.data_models import (
    ExperimentResult,
    ThreeStageResult,
    CompressionTestResult,
    ModelWorkflowResult
)
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class ModelSwitchingDemo:
    """
    Complete model switching demo orchestrator.
    
    Coordinates the full workflow including model switching, three-stage testing,
    compression evaluation, and quality analysis.
    
    Attributes:
        orchestrator: ModelSwitcherOrchestrator for model management
        token_tester: TokenLimitTester for three-stage testing
        compression_evaluator: CompressionEvaluator for compression testing
        quality_analyzer: QualityAnalyzer for quality assessment
        generator_adapter: CodeGeneratorAdapter for code generation
        reviewer_adapter: CodeReviewerAdapter for code review
        config: Demo configuration
        results: Collected results from all experiments
        
    Example:
        ```python
        from demo_model_switching import ModelSwitchingDemo
        
        # Initialize demo
        demo = ModelSwitchingDemo()
        
        # Run complete demo
        results = await demo.run_complete_demo()
        
        # Generate report
        await demo.generate_report(results)
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model switching demo.
        
        Args:
            config: Optional custom configuration
            
        Example:
            ```python
            from demo_model_switching import ModelSwitchingDemo
            
            # Initialize with default config
            demo = ModelSwitchingDemo()
            
            # Or with custom config
            custom_config = {"models": ["starcoder"]}
            demo = ModelSwitchingDemo(custom_config)
            ```
        """
        self.config = config or get_config()
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Initialize components
        self.orchestrator = ModelSwitcherOrchestrator(
            models=self.config["models"]
        )
        
        self.token_tester = TokenLimitTester()
        self.compression_evaluator = CompressionEvaluator()
        self.quality_analyzer = QualityAnalyzer()
        
        # Initialize agent adapters
        self.generator_adapter = CodeGeneratorAdapter()
        self.reviewer_adapter = CodeReviewerAdapter()
        
        # Results storage
        self.results: Dict[str, Any] = {
            "models_tested": [],
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
        
        Returns:
            Dictionary containing all demo results
            
        Example:
            ```python
            # Run complete demo
            results = await demo.run_complete_demo()
            
            print(f"Models tested: {results['summary']['models_tested']}")
            print(f"Total experiments: {results['summary']['total_experiments']}")
            ```
        """
        try:
            self.logger.info("Starting complete model switching demo")
            print("🚀 Starting Model Switching Demo")
            print("=" * 50)
            
            # Check model availability
            await self._check_model_availability()
            
            # Run tests for each model
            for model_name in self.config["models"]:
                if is_model_supported(model_name):
                    await self._test_model(model_name)
                else:
                    self.logger.warning(f"Model {model_name} not supported, skipping")
            
            # Generate summary
            self._generate_summary()
            
            # Print results
            self._print_results()
            
            self.logger.info("Model switching demo completed successfully")
            return self.results
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            print(f"❌ Demo failed: {e}")
            raise
        finally:
            # Always cleanup containers
            print("\n🧹 Cleaning up containers...")
            await self.orchestrator.cleanup_containers()
    
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
        
        if not available_models:
            print("⚠️  No models are currently running. Will start models sequentially during testing.")
            available_models = self.config["models"]
        
        # Update config to include available or configured models
        self.config["models"] = available_models
        self.orchestrator.models = available_models
        
        print(f"📊 Will test {len(available_models)} models: {available_models}")
    
    async def _test_model(self, model_name: str) -> None:
        """
        Test a single model with all stages.
        
        Args:
            model_name: Name of the model to test
        """
        print(f"\n{'='*60}")
        print(f"🧪 Testing {model_name}")
        print(f"{'='*60}")
        
        try:
            # Switch to model
            if await self.orchestrator.switch_to_model(model_name):
                print(f"✅ Switched to {model_name}")
            else:
                print(f"❌ Failed to switch to {model_name}")
                return
            
            # Run three-stage token limit tests
            print(f"\n📊 Running three-stage token limit tests...")
            three_stage_results = await self.token_tester.run_three_stage_test(model_name)
            self.results["three_stage_results"][model_name] = three_stage_results
            
            if three_stage_results.success:
                print(f"✅ Three-stage test completed")
                print(f"   Short query: {three_stage_results.short_query_tokens} tokens")
                print(f"   Medium query: {three_stage_results.medium_query_tokens} tokens")
                print(f"   Long query: {three_stage_results.long_query_tokens} tokens")
                print(f"   Queries exceeding limit: {three_stage_results.queries_exceeding_limit}")
            else:
                print(f"❌ Three-stage test failed: {three_stage_results.error_message}")
                return
            
            # Test compression algorithms on heaviest query
            if three_stage_results.long_exceeds_limit:
                print(f"\n🗜️  Testing compression algorithms on heaviest query...")
                compression_results = await self.compression_evaluator.test_all_compressions(
                    three_stage_results.long_query, model_name
                )
                self.results["compression_results"][model_name] = compression_results
                
                successful_compressions = [r for r in compression_results if r.success]
                print(f"✅ Tested {len(compression_results)} compression algorithms")
                print(f"   Successful: {len(successful_compressions)}")
                
                # Show compression results
                for result in successful_compressions:
                    print(f"   {result.strategy}: {result.compression_ratio:.2f} ratio, "
                          f"{result.response_time:.2f}s")
                
                # Evaluate quality for each compression
                print(f"\n📈 Evaluating quality for each compression...")
                quality_results = await self._evaluate_compression_qualities(
                    compression_results, three_stage_results.long_query
                )
                self.results["quality_results"][model_name] = quality_results
                
                # Show quality results
                for strategy, quality in quality_results.items():
                    print(f"   {strategy}: {quality['overall_score']:.2f} overall quality")
            
            # Collect model statistics
            model_stats = self.orchestrator.get_model_statistics(model_name)
            self.results["model_statistics"][model_name] = model_stats
            
            print(f"\n📊 Model {model_name} testing completed")
            print(f"   Total requests: {model_stats['total_requests']}")
            print(f"   Success rate: {model_stats['successful_requests']/max(1, model_stats['total_requests'])*100:.1f}%")
            print(f"   Average response time: {model_stats['average_response_time']:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to test model {model_name}: {e}")
            print(f"❌ Failed to test {model_name}: {e}")
    
    async def _evaluate_compression_qualities(
        self, 
        compression_results: List[CompressionTestResult],
        original_query: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate quality for each compression result.
        
        Args:
            compression_results: List of compression test results
            original_query: Original query text
            
        Returns:
            Dictionary mapping strategy names to quality metrics
        """
        quality_results = {}
        
        for result in compression_results:
            if result.success:
                try:
                    # Evaluate compression quality
                    quality_metrics = await self.compression_evaluator.evaluate_compression_quality(
                        original_query, result.compressed_query, result.response
                    )
                    
                    # Analyze code quality if response contains code
                    code_quality = None
                    if "def " in result.response or "class " in result.response:
                        code_quality = await self.reviewer_adapter.review_code_quality(
                            result.response, original_query, result.strategy
                        )
                    
                    # Analyze completeness
                    completeness = await self.quality_analyzer.analyze_completeness(
                        result.response, original_query
                    )
                    
                    quality_results[result.strategy] = {
                        "compression_quality": quality_metrics,
                        "code_quality": code_quality,
                        "completeness": completeness,
                        "performance": {
                            "response_time": result.response_time,
                            "tokens_used": result.total_tokens_used,
                            "compression_ratio": result.compression_ratio
                        },
                        "overall_score": self._calculate_overall_quality_score(
                            quality_metrics, code_quality, completeness, result
                        )
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to evaluate quality for {result.strategy}: {e}")
                    quality_results[result.strategy] = {
                        "error": str(e),
                        "overall_score": 0.0
                    }
        
        return quality_results
    
    def _calculate_overall_quality_score(
        self,
        compression_quality,
        code_quality,
        completeness,
        compression_result: CompressionTestResult
    ) -> float:
        """Calculate overall quality score."""
        try:
            # Base score from compression quality
            base_score = compression_quality.overall_score if compression_quality else 0.5
            
            # Adjust for code quality
            if code_quality:
                code_adjustment = (code_quality.code_quality_score - 5.0) / 10.0
                base_score += code_adjustment * 0.3
            
            # Adjust for completeness
            if completeness:
                completeness_adjustment = (completeness.completeness_score - 0.5) * 2
                base_score += completeness_adjustment * 0.2
            
            # Adjust for performance
            performance_score = 1.0 / (compression_result.response_time + 0.1)
            performance_adjustment = (performance_score - 0.1) * 0.1
            base_score += performance_adjustment
            
            return max(0.0, min(1.0, base_score))
            
        except Exception:
            return 0.5
    
    def _generate_summary(self) -> None:
        """Generate summary of all results."""
        models_tested = list(self.results["three_stage_results"].keys())
        
        total_experiments = 0
        successful_experiments = 0
        
        for model_name in models_tested:
            # Count three-stage experiments
            if model_name in self.results["three_stage_results"]:
                total_experiments += 3
                if self.results["three_stage_results"][model_name].success:
                    successful_experiments += 3
            
            # Count compression experiments
            if model_name in self.results["compression_results"]:
                compression_results = self.results["compression_results"][model_name]
                total_experiments += len(compression_results)
                successful_experiments += sum(1 for r in compression_results if r.success)
        
        # Find best performing model and compression strategy
        best_model = None
        best_compression = None
        
        if self.results["model_statistics"]:
            best_model = max(
                self.results["model_statistics"].keys(),
                key=lambda m: self.results["model_statistics"][m]["successful_requests"]
            )
        
        if self.results["quality_results"]:
            best_compression_scores = {}
            for model, qualities in self.results["quality_results"].items():
                for strategy, quality in qualities.items():
                    if "overall_score" in quality:
                        best_compression_scores[f"{model}_{strategy}"] = quality["overall_score"]
            
            if best_compression_scores:
                best_compression = max(best_compression_scores.keys(), key=lambda k: best_compression_scores[k])
        
        self.results["summary"] = {
            "models_tested": len(models_tested),
            "total_experiments": total_experiments,
            "successful_experiments": successful_experiments,
            "success_rate": successful_experiments / max(1, total_experiments),
            "best_model": best_model,
            "best_compression": best_compression,
            "timestamp": datetime.now().isoformat()
        }
    
    def _print_results(self) -> None:
        """Print summary results."""
        summary = self.results["summary"]
        
        print(f"\n{'='*60}")
        print(f"📊 DEMO SUMMARY")
        print(f"{'='*60}")
        print(f"Models tested: {summary['models_tested']}")
        print(f"Total experiments: {summary['total_experiments']}")
        print(f"Successful experiments: {summary['successful_experiments']}")
        print(f"Success rate: {summary['success_rate']*100:.1f}%")
        print(f"Best performing model: {summary['best_model']}")
        print(f"Best compression strategy: {summary['best_compression']}")
        print(f"Completed at: {summary['timestamp']}")
    
    async def generate_report(self, results: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate comprehensive markdown report.
        
        Args:
            results: Optional results to report on (uses self.results if None)
            
        Returns:
            Path to generated report file
            
        Example:
            ```python
            # Generate report
            report_path = await demo.generate_report()
            print(f"Report saved to: {report_path}")
            ```
        """
        try:
            from utils.report_generator import ReportGenerator
            
            report_results = results or self.results
            report_generator = ReportGenerator()
            
            report_path = await report_generator.generate_comprehensive_report(
                results=report_results,
                config=self.config
            )
            
            print(f"\n📄 Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            print(f"❌ Failed to generate report: {e}")
            raise


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
        print("=" * 50)
        print("This demo will:")
        print("1. Test multiple models (StarCoder, Mistral)")
        print("2. Run three-stage token limit tests")
        print("3. Test all compression algorithms")
        print("4. Evaluate quality and performance")
        print("5. Generate comprehensive report")
        print("=" * 50)
        
        # Initialize and run demo
        demo = ModelSwitchingDemo()
        results = await demo.run_complete_demo()
        
        # Generate report
        report_path = await demo.generate_report(results)
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📄 Report saved to: {report_path}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
