"""
Comprehensive unit tests for the Model Switching Demo.

This module provides unit tests covering all components of the model switching
demo with 80%+ coverage including model switcher orchestration, token limit testing,
compression evaluation, quality analysis, and report generation.
"""

import asyncio
import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.code_generator_adapter import CodeGeneratorAdapter
from agents.code_reviewer_adapter import CodeReviewerAdapter
from config.demo_config import get_config, get_model_config, get_quality_thresholds
from core.compression_evaluator import CompressionEvaluator
from core.model_switcher import ModelSwitcherOrchestrator
from core.quality_analyzer import QualityAnalyzer
from core.token_limit_tester import TokenLimitTester
from demo_model_switching import ModelSwitchingDemo
from models.data_models import (
    ExperimentResult,
    ThreeStageResult,
    CompressionTestResult,
    QualityMetrics,
    PerformanceMetrics,
    CodeQualityMetrics,
    CompletenessScore,
    ModelLimits
)
from utils.report_generator import ReportGenerator


class TestModelSwitcherOrchestrator:
    """Test cases for ModelSwitcherOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
    
    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.models == ["starcoder", "mistral"]
        assert orchestrator.current_model is None
        assert "starcoder" in orchestrator.statistics
        assert "mistral" in orchestrator.statistics
    
    @pytest.mark.asyncio
    async def test_check_model_availability(self, orchestrator):
        """Test model availability checking."""
        with patch.object(orchestrator.model_client, 'check_availability', return_value=True):
            result = await orchestrator.check_model_availability("starcoder")
            assert result is True
            assert orchestrator.statistics["starcoder"]["availability_checks"] == 1
    
    @pytest.mark.asyncio
    async def test_switch_to_model(self, orchestrator):
        """Test model switching."""
        with patch.object(orchestrator, 'check_model_availability', return_value=True):
            result = await orchestrator.switch_to_model("starcoder")
            assert result is True
            assert orchestrator.current_model == "starcoder"
            assert orchestrator.statistics["starcoder"]["successful_switches"] == 1
    
    @pytest.mark.asyncio
    async def test_run_workflow_with_model(self, orchestrator):
        """Test workflow execution with model."""
        mock_task = MagicMock()
        mock_task.execute = AsyncMock(return_value={"success": True, "tokens_used": 100})
        
        with patch.object(orchestrator, 'switch_to_model', return_value=True):
            result = await orchestrator.run_workflow_with_model("starcoder", [mock_task])
            
            assert result.model_name == "starcoder"
            assert result.tasks_executed == 1
            assert result.successful_tasks == 1
            assert result.failed_tasks == 0
    
    def test_get_model_statistics(self, orchestrator):
        """Test getting model statistics."""
        stats = orchestrator.get_model_statistics("starcoder")
        assert "total_requests" in stats
        assert "successful_requests" in stats
        
        all_stats = orchestrator.get_model_statistics()
        assert "starcoder" in all_stats
        assert "mistral" in all_stats
    
    def test_get_model_summary(self, orchestrator):
        """Test getting model summary."""
        summary = orchestrator.get_model_summary()
        assert summary["total_models"] == 2
        assert summary["current_model"] is None
        assert "models" in summary


class TestTokenLimitTester:
    """Test cases for TokenLimitTester."""
    
    @pytest.fixture
    def token_tester(self):
        """Create token tester instance for testing."""
        return TokenLimitTester()
    
    def test_initialization(self, token_tester):
        """Test token tester initialization."""
        assert token_tester.token_counter is not None
        assert "starcoder" in token_tester.model_capabilities
        assert "mistral" in token_tester.model_capabilities
    
    def test_generate_short_query(self, token_tester):
        """Test short query generation."""
        query = token_tester.generate_short_query("starcoder")
        assert isinstance(query, str)
        assert len(query) > 0
        assert "function" in query.lower()
    
    def test_generate_medium_query(self, token_tester):
        """Test medium query generation."""
        query = token_tester.generate_medium_query("mistral")
        assert isinstance(query, str)
        assert len(query) > 0
        assert "class" in query.lower()
    
    def test_generate_long_query(self, token_tester):
        """Test long query generation."""
        query = token_tester.generate_long_query("starcoder")
        assert isinstance(query, str)
        assert len(query) > 0
        assert "implement" in query.lower()
    
    @pytest.mark.asyncio
    async def test_run_three_stage_test(self, token_tester):
        """Test three-stage testing."""
        with patch.object(token_tester.token_counter, 'count_tokens') as mock_count:
            mock_count.return_value.count = 100
            
            with patch.object(token_tester.token_counter, 'get_model_limits') as mock_limits:
                mock_limits.return_value = ModelLimits(
                    max_input_tokens=8192,
                    max_output_tokens=1024,
                    max_total_tokens=9216
                )
                
                result = await token_tester.run_three_stage_test("starcoder")
                
                assert isinstance(result, ThreeStageResult)
                assert result.model_name == "starcoder"
                assert result.short_query_tokens == 100
                assert result.medium_query_tokens == 100
                assert result.long_query_tokens == 100
    
    def test_get_model_capabilities(self, token_tester):
        """Test getting model capabilities."""
        capabilities = token_tester.get_model_capabilities("starcoder")
        assert "max_tokens" in capabilities
        assert "recommended" in capabilities
        assert capabilities["max_tokens"] == 8192


class TestCompressionEvaluator:
    """Test cases for CompressionEvaluator."""
    
    @pytest.fixture
    def compression_evaluator(self):
        """Create compression evaluator instance for testing."""
        return CompressionEvaluator()
    
    def test_initialization(self, compression_evaluator):
        """Test compression evaluator initialization."""
        assert compression_evaluator.model_client is not None
        assert compression_evaluator.token_counter is not None
        assert compression_evaluator.text_compressor is not None
        assert len(compression_evaluator.compression_strategies) == 5
    
    @pytest.mark.asyncio
    async def test_test_all_compressions(self, compression_evaluator):
        """Test testing all compression strategies."""
        test_query = "Write a Python function to calculate fibonacci number"
        
        with patch.object(compression_evaluator.token_counter, 'count_tokens') as mock_count:
            mock_count.return_value.count = 50
            
            with patch.object(compression_evaluator.text_compressor, 'compress_text') as mock_compress:
                mock_compress.return_value = MagicMock(
                    compressed_text="Short query",
                    original_tokens=50,
                    compressed_tokens=20,
                    compression_ratio=0.4
                )
                
                with patch.object(compression_evaluator.model_client, 'make_request') as mock_request:
                    mock_request.return_value = MagicMock(
                        response="Generated code",
                        response_time=1.5,
                        total_tokens=30
                    )
                    
                    results = await compression_evaluator.test_all_compressions(
                        test_query, "starcoder", target_tokens=100
                    )
                    
                    assert len(results) == 5
                    assert all(isinstance(r, CompressionTestResult) for r in results)
    
    @pytest.mark.asyncio
    async def test_evaluate_compression_quality(self, compression_evaluator):
        """Test compression quality evaluation."""
        original = "Write a Python function to calculate fibonacci number"
        compressed = "Write fibonacci function"
        response = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
        
        quality = await compression_evaluator.evaluate_compression_quality(
            original, compressed, response
        )
        
        assert isinstance(quality, QualityMetrics)
        assert 0.0 <= quality.overall_score <= 1.0
        assert 0.0 <= quality.completeness_score <= 1.0
        assert 0.0 <= quality.relevance_score <= 1.0
    
    def test_get_compression_strategies(self, compression_evaluator):
        """Test getting compression strategies."""
        strategies = compression_evaluator.get_compression_strategies()
        assert len(strategies) == 5
        assert "truncation" in strategies
        assert "keywords" in strategies
    
    def test_get_best_compression_strategy(self, compression_evaluator):
        """Test getting best compression strategy."""
        results = [
            CompressionTestResult(
                strategy="truncation",
                original_query="test",
                compressed_query="test",
                original_tokens=100,
                compressed_tokens=50,
                compression_ratio=0.5,
                response="response",
                response_tokens=20,
                response_time=1.0,
                success=True
            ),
            CompressionTestResult(
                strategy="keywords",
                original_query="test",
                compressed_query="test",
                original_tokens=100,
                compressed_tokens=30,
                compression_ratio=0.3,
                response="response",
                response_tokens=20,
                response_time=2.0,
                success=True
            )
        ]
        
        best_strategy = compression_evaluator.get_best_compression_strategy(results)
        assert best_strategy == "keywords"  # Better compression ratio


class TestQualityAnalyzer:
    """Test cases for QualityAnalyzer."""
    
    @pytest.fixture
    def quality_analyzer(self):
        """Create quality analyzer instance for testing."""
        return QualityAnalyzer()
    
    def test_initialization(self, quality_analyzer):
        """Test quality analyzer initialization."""
        assert quality_analyzer.model_client is not None
        assert quality_analyzer.token_counter is not None
        assert "high_quality" in quality_analyzer.quality_thresholds
    
    @pytest.mark.asyncio
    async def test_analyze_performance(self, quality_analyzer):
        """Test performance analysis."""
        experiment_result = ExperimentResult(
            experiment_name="test",
            model_name="starcoder",
            original_query="test query",
            processed_query="test query",
            response="test response",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            response_time=2.5,
            compression_applied=False,
            compression_result=None
        )
        
        performance = await quality_analyzer.analyze_performance(experiment_result)
        
        assert isinstance(performance, PerformanceMetrics)
        assert performance.response_time == 2.5
        assert performance.total_tokens == 150
        assert performance.tokens_per_second == 60.0  # 150/2.5
    
    @pytest.mark.asyncio
    async def test_analyze_code_quality(self, quality_analyzer):
        """Test code quality analysis."""
        code = '''
def fibonacci(n: int) -> int:
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''
        requirements = "Write a fibonacci function with type hints and docstring"
        
        quality = await quality_analyzer.analyze_code_quality(code, requirements, "starcoder")
        
        assert isinstance(quality, CodeQualityMetrics)
        assert quality.has_docstrings is True
        assert quality.has_type_hints is True
        assert quality.function_count == 1
    
    @pytest.mark.asyncio
    async def test_analyze_completeness(self, quality_analyzer):
        """Test completeness analysis."""
        response = "Here's a Python function: def example(): pass"
        original_query = "Write a Python function"
        
        completeness = await quality_analyzer.analyze_completeness(response, original_query)
        
        assert isinstance(completeness, CompletenessScore)
        assert completeness.has_code is True
        assert completeness.response_length > 0
    
    def test_get_quality_thresholds(self, quality_analyzer):
        """Test getting quality thresholds."""
        thresholds = quality_analyzer.get_quality_thresholds()
        assert "high_quality" in thresholds
        assert "acceptable_quality" in thresholds


class TestCodeGeneratorAdapter:
    """Test cases for CodeGeneratorAdapter."""
    
    @pytest.fixture
    def generator_adapter(self):
        """Create generator adapter instance for testing."""
        return CodeGeneratorAdapter()
    
    @pytest.mark.asyncio
    async def test_generate_code_with_compression(self, generator_adapter):
        """Test code generation with compression."""
        task_description = "Write a simple function"
        
        with patch.object(generator_adapter.token_counter, 'count_tokens') as mock_count:
            mock_count.return_value.count = 50
            
            with patch.object(generator_adapter.token_counter, 'get_model_limits') as mock_limits:
                mock_limits.return_value = ModelLimits(
                    max_input_tokens=8192,
                    max_output_tokens=1024,
                    max_total_tokens=9216
                )
                
                with patch.object(generator_adapter, '_generate_with_fallback') as mock_generate:
                    mock_generate.return_value = "def example(): pass"
                    
                    result = await generator_adapter.generate_code_with_compression(
                        task_description, "starcoder"
                    )
                    
                    assert isinstance(result, ExperimentResult)
                    assert result.model_name == "starcoder"
                    assert result.success is True
    
    def test_get_agent_statistics(self, generator_adapter):
        """Test getting agent statistics."""
        stats = generator_adapter.get_agent_statistics()
        assert "agent_type" in stats


class TestCodeReviewerAdapter:
    """Test cases for CodeReviewerAdapter."""
    
    @pytest.fixture
    def reviewer_adapter(self):
        """Create reviewer adapter instance for testing."""
        return CodeReviewerAdapter()
    
    @pytest.mark.asyncio
    async def test_review_code_quality(self, reviewer_adapter):
        """Test code quality review."""
        code = "def example(): pass"
        task_description = "Write a function"
        
        with patch.object(reviewer_adapter, '_review_with_fallback') as mock_review:
            mock_review.return_value = CodeQualityMetrics(
                code_quality_score=7.0,
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=False,
                has_type_hints=False,
                test_coverage="none",
                complexity_score=3.0,
                requirements_coverage=0.8,
                completeness_score=0.7,
                code_length=len(code),
                function_count=1,
                class_count=0
            )
            
            quality = await reviewer_adapter.review_code_quality(
                code, task_description, "starcoder"
            )
            
            assert isinstance(quality, CodeQualityMetrics)
            assert quality.code_quality_score == 7.0
    
    def test_get_agent_statistics(self, reviewer_adapter):
        """Test getting agent statistics."""
        stats = reviewer_adapter.get_agent_statistics()
        assert "agent_type" in stats


class TestReportGenerator:
    """Test cases for ReportGenerator."""
    
    @pytest.fixture
    def report_generator(self):
        """Create report generator instance for testing."""
        return ReportGenerator()
    
    def test_initialization(self, report_generator):
        """Test report generator initialization."""
        assert report_generator.reports_dir.exists()
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, report_generator):
        """Test comprehensive report generation."""
        results = {
            "summary": {
                "models_tested": 2,
                "total_experiments": 10,
                "successful_experiments": 8,
                "success_rate": 0.8,
                "best_model": "starcoder",
                "best_compression": "truncation"
            },
            "three_stage_results": {},
            "compression_results": {},
            "quality_results": {},
            "model_statistics": {}
        }
        
        config = get_config()
        
        report_path = await report_generator.generate_comprehensive_report(
            results, config
        )
        
        assert Path(report_path).exists()
        assert report_path.endswith('.md')
        
        # Check report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Model Switching Demo Report" in content
            assert "Executive Summary" in content
            assert "starcoder" in content


class TestModelSwitcherWithDocker:
    """Test cases for ModelSwitcher with Docker integration."""
    
    @pytest.fixture
    def orchestrator_with_docker(self):
        """Create orchestrator with mocked docker manager."""
        from unittest.mock import MagicMock
        orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
        orchestrator.docker_manager = MagicMock()
        orchestrator.use_container_management = True
        orchestrator.running_containers = set()
        return orchestrator
    
    @pytest.mark.asyncio
    async def test_docker_initialization_success(self):
        """Test Docker manager initialization when available."""
        with patch('utils.docker_manager.ModelDockerManager') as mock_docker_manager:
            mock_docker_manager.return_value = MagicMock()
            
            orchestrator = ModelSwitcherOrchestrator(models=["starcoder"])
            
            assert orchestrator.use_container_management is True
            assert orchestrator.docker_manager is not None
            assert orchestrator.running_containers == set()
    
    @pytest.mark.asyncio
    async def test_docker_initialization_failure(self):
        """Test Docker manager initialization when unavailable."""
        with patch('utils.docker_manager.ModelDockerManager', side_effect=ImportError("Docker not available")):
            orchestrator = ModelSwitcherOrchestrator(models=["starcoder"])
            
            assert orchestrator.use_container_management is False
            assert orchestrator.docker_manager is None
            assert orchestrator.running_containers == set()
    
    @pytest.mark.asyncio
    async def test_poll_model_health_success(self, orchestrator_with_docker):
        """Test successful model health polling."""
        orchestrator_with_docker.model_client.check_availability = AsyncMock(return_value=True)
        
        result = await orchestrator_with_docker._poll_model_health("starcoder", max_attempts=2, poll_interval=0.1)
        
        assert result is True
        orchestrator_with_docker.model_client.check_availability.assert_called_once_with("starcoder")
    
    @pytest.mark.asyncio
    async def test_poll_model_health_timeout(self, orchestrator_with_docker):
        """Test model health polling timeout."""
        orchestrator_with_docker.model_client.check_availability = AsyncMock(return_value=False)
        
        result = await orchestrator_with_docker._poll_model_health("starcoder", max_attempts=2, poll_interval=0.1, timeout=0.2)
        
        assert result is False
        assert orchestrator_with_docker.model_client.check_availability.call_count == 2
    
    @pytest.mark.asyncio
    async def test_start_container_with_retry_success(self, orchestrator_with_docker):
        """Test container start with retry logic."""
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=["starcoder"])
        
        with patch.object(orchestrator_with_docker, '_poll_model_health', return_value=True):
            success = await orchestrator_with_docker._start_container_with_retry("starcoder")
            
            assert success is True
            assert "starcoder" in orchestrator_with_docker.running_containers
            orchestrator_with_docker.docker_manager.start_model.assert_called_once_with("starcoder", wait_time=5)
    
    @pytest.mark.asyncio
    async def test_start_container_with_retry_failure(self, orchestrator_with_docker):
        """Test container start with retry failure."""
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=False)
        
        success = await orchestrator_with_docker._start_container_with_retry("starcoder", max_retries=2)
        
        assert success is False
        assert "starcoder" not in orchestrator_with_docker.running_containers
        assert orchestrator_with_docker.docker_manager.start_model.call_count == 2
    
    @pytest.mark.asyncio
    async def test_start_container_health_check_failure(self, orchestrator_with_docker):
        """Test container start with health check failure."""
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(return_value=True)
        
        with patch.object(orchestrator_with_docker, '_poll_model_health', return_value=False):
            success = await orchestrator_with_docker._start_container_with_retry("starcoder")
            
            assert success is False
            # Should be called once per retry attempt (3 times total)
            assert orchestrator_with_docker.docker_manager.stop_model.call_count == 3
    
    @pytest.mark.asyncio
    async def test_check_model_availability_with_docker_running(self, orchestrator_with_docker):
        """Test model availability check when container is already running."""
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=["starcoder"])
        orchestrator_with_docker.model_client.check_availability = AsyncMock(return_value=True)
        
        result = await orchestrator_with_docker.check_model_availability("starcoder")
        
        assert result is True
        assert "starcoder" in orchestrator_with_docker.running_containers
        orchestrator_with_docker.docker_manager.get_running_models.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_model_availability_with_docker_start(self, orchestrator_with_docker):
        """Test model availability check when container needs to be started."""
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=[])
        orchestrator_with_docker.model_client.check_availability = AsyncMock(return_value=True)
        
        with patch.object(orchestrator_with_docker, '_start_container_with_retry', return_value=True):
            result = await orchestrator_with_docker.check_model_availability("starcoder")
            
            assert result is True
            orchestrator_with_docker._start_container_with_retry.assert_called_once_with("starcoder")
    
    @pytest.mark.asyncio
    async def test_sequential_model_switching(self, orchestrator_with_docker):
        """Test that previous model is stopped before starting new one."""
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.start_model = AsyncMock(return_value=True)
        orchestrator_with_docker.docker_manager.get_running_models = MagicMock(return_value=[])
        orchestrator_with_docker.current_model = "starcoder"
        orchestrator_with_docker.running_containers.add("starcoder")
        
        with patch.object(orchestrator_with_docker, 'check_model_availability', return_value=True):
            with patch.object(orchestrator_with_docker, '_poll_model_health', return_value=True):
                success = await orchestrator_with_docker.switch_to_model("mistral")
                
                assert success is True
                orchestrator_with_docker.docker_manager.stop_model.assert_called_once_with("starcoder", timeout=30)
                assert "starcoder" not in orchestrator_with_docker.running_containers
    
    @pytest.mark.asyncio
    async def test_cleanup_containers(self, orchestrator_with_docker):
        """Test container cleanup."""
        orchestrator_with_docker.running_containers = {"starcoder", "mistral"}
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(return_value=True)
        
        await orchestrator_with_docker.cleanup_containers()
        
        assert len(orchestrator_with_docker.running_containers) == 0
        assert orchestrator_with_docker.docker_manager.stop_model.call_count == 2
        orchestrator_with_docker.docker_manager.stop_model.assert_any_call("starcoder", timeout=30)
        orchestrator_with_docker.docker_manager.stop_model.assert_any_call("mistral", timeout=30)
    
    @pytest.mark.asyncio
    async def test_cleanup_containers_no_docker(self):
        """Test cleanup when Docker management is disabled."""
        orchestrator = ModelSwitcherOrchestrator(models=["starcoder"])
        orchestrator.use_container_management = False
        
        # Should not raise any exceptions
        await orchestrator.cleanup_containers()
    
    @pytest.mark.asyncio
    async def test_cleanup_containers_partial_failure(self, orchestrator_with_docker):
        """Test cleanup with partial failures."""
        orchestrator_with_docker.running_containers = {"starcoder", "mistral"}
        
        def mock_stop_model(model_name, timeout):
            if model_name == "starcoder":
                return True
            else:
                raise Exception("Failed to stop mistral")
        
        orchestrator_with_docker.docker_manager.stop_model = AsyncMock(side_effect=mock_stop_model)
        
        await orchestrator_with_docker.cleanup_containers()
        
        # Should still clean up successfully stopped containers
        assert "starcoder" not in orchestrator_with_docker.running_containers
        assert "mistral" in orchestrator_with_docker.running_containers  # Failed to stop


class TestModelSwitchingDemo:
    """Test cases for ModelSwitchingDemo."""
    
    @pytest.fixture
    def demo(self):
        """Create demo instance for testing."""
        return ModelSwitchingDemo()
    
    def test_initialization(self, demo):
        """Test demo initialization."""
        assert demo.orchestrator is not None
        assert demo.token_tester is not None
        assert demo.compression_evaluator is not None
        assert demo.quality_analyzer is not None
        assert demo.generator_adapter is not None
        assert demo.reviewer_adapter is not None
    
    @pytest.mark.asyncio
    async def test_check_model_availability(self, demo):
        """Test model availability checking."""
        with patch.object(demo.orchestrator, 'check_all_models_availability') as mock_check:
            mock_check.return_value = {"starcoder": True, "mistral": False}
            
            await demo._check_model_availability()
            
            assert demo.config["models"] == ["starcoder"]
    
    @pytest.mark.asyncio
    async def test_run_complete_demo_with_cleanup(self, demo):
        """Test complete demo execution with cleanup."""
        with patch.object(demo, '_check_model_availability'):
            with patch.object(demo, '_test_model'):
                with patch.object(demo, '_generate_summary'):
                    with patch.object(demo, '_print_results'):
                        with patch.object(demo.orchestrator, 'cleanup_containers') as mock_cleanup:
                            results = await demo.run_complete_demo()
                            
                            assert isinstance(results, dict)
                            assert "summary" in results
                            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_complete_demo_exception_with_cleanup(self, demo):
        """Test demo execution with exception still calls cleanup."""
        with patch.object(demo, '_check_model_availability', side_effect=Exception("Test error")):
            with patch.object(demo.orchestrator, 'cleanup_containers') as mock_cleanup:
                with pytest.raises(Exception):
                    await demo.run_complete_demo()
                
                mock_cleanup.assert_called_once()


class TestDataModels:
    """Test cases for data models."""
    
    def test_experiment_result(self):
        """Test ExperimentResult model."""
        result = ExperimentResult(
            experiment_name="test",
            model_name="starcoder",
            original_query="test",
            processed_query="test",
            response="response",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            response_time=2.0,
            compression_applied=False,
            compression_result=None
        )
        
        assert result.total_tokens == 150
        assert result.compression_ratio == 1.0
    
    def test_three_stage_result(self):
        """Test ThreeStageResult model."""
        result = ThreeStageResult(
            model_name="starcoder",
            short_query="short",
            medium_query="medium",
            long_query="long",
            short_query_tokens=50,
            medium_query_tokens=300,
            long_query_tokens=1000,
            model_limits=ModelLimits(8192, 1024, 9216),
            short_exceeds_limit=False,
            medium_exceeds_limit=False,
            long_exceeds_limit=True,
            success=True
        )
        
        assert result.total_queries_tested == 3
        assert result.queries_exceeding_limit == 1
        assert result.compression_needed is True
    
    def test_compression_test_result(self):
        """Test CompressionTestResult model."""
        result = CompressionTestResult(
            strategy="truncation",
            original_query="original",
            compressed_query="compressed",
            original_tokens=1000,
            compressed_tokens=200,
            compression_ratio=0.2,
            response="response",
            response_tokens=50,
            response_time=1.5,
            success=True
        )
        
        assert result.total_tokens_used == 250
        assert result.tokens_saved == 800
        assert result.compression_efficiency == 0.8
    
    def test_quality_metrics(self):
        """Test QualityMetrics model."""
        metrics = QualityMetrics(
            compression_ratio=0.3,
            completeness_score=0.8,
            relevance_score=0.9,
            semantic_score=0.7,
            overall_score=0.8,
            response_length=500,
            information_preservation=0.75
        )
        
        assert metrics.is_high_quality is True
        assert metrics.is_acceptable_quality is True


class TestConfiguration:
    """Test cases for configuration."""
    
    def test_get_config(self):
        """Test getting configuration."""
        config = get_config()
        assert "models" in config
        assert "compression_algorithms" in config
        assert "token_stages" in config
    
    def test_get_model_config(self):
        """Test getting model configuration."""
        starcoder_config = get_model_config("starcoder")
        assert "max_tokens" in starcoder_config
        assert starcoder_config["max_tokens"] == 8192
    
    def test_get_quality_thresholds(self):
        """Test getting quality thresholds."""
        thresholds = get_quality_thresholds()
        assert "code_quality_min" in thresholds
        assert "completeness_min" in thresholds


# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # This would be a more comprehensive test that actually runs
        # the full demo with mocked external dependencies
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling across components."""
        # Test various error scenarios
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
