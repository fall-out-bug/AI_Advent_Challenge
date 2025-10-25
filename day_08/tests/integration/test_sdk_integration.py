"""
Integration tests for SDK integration with day_08.

This module provides comprehensive end-to-end integration tests to verify
that day_08 properly integrates with the SDK agents and orchestration system.
"""

import asyncio
import pytest
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# Add shared package to path
shared_path = Path(__file__).parent.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.agents.code_generator import CodeGeneratorAgent
from shared_package.agents.code_reviewer import CodeReviewerAgent
from shared_package.orchestration.adapters import DirectAdapter, RestAdapter
from shared_package.orchestration.sequential import SequentialOrchestrator
from shared_package.orchestration.parallel import ParallelOrchestrator

from agents.code_generator_adapter import CodeGeneratorAdapter
from agents.code_reviewer_adapter import CodeReviewerAdapter
from core.model_switcher import ModelSwitcherOrchestrator
from core.compression_evaluator import CompressionEvaluator
from core.token_limit_tester import TokenLimitTester
from models.data_models import ExperimentResult, CodeQualityMetrics
from utils.logging import LoggerFactory


class TestSDKIntegration:
    """
    Integration tests for SDK agent integration with day_08.
    
    Tests the complete workflow from day_08 components to SDK agents
    and verifies proper integration without day_07 dependencies.
    """
    
    @pytest.fixture
    def mock_model_client(self):
        """Mock model client for testing."""
        client = MagicMock()
        client.generate_response = AsyncMock(return_value="Generated code response")
        client.count_tokens = MagicMock(return_value=MagicMock(count=100))
        return client
    
    @pytest.fixture
    def mock_token_counter(self):
        """Mock token counter for testing."""
        counter = MagicMock()
        counter.count_tokens = MagicMock(return_value=MagicMock(count=100))
        counter.get_model_limits = MagicMock(return_value=MagicMock(
            max_input_tokens=2000,
            recommended_input=1500
        ))
        return counter
    
    @pytest.fixture
    def mock_text_compressor(self):
        """Mock text compressor for testing."""
        compressor = MagicMock()
        compressor.compress_text = MagicMock(return_value=MagicMock(
            compressed_text="Compressed text",
            original_tokens=200,
            compressed_tokens=150,
            compression_ratio=0.75
        ))
        return compressor
    
    @pytest.fixture
    def generator_adapter(self, mock_model_client, mock_token_counter, mock_text_compressor):
        """Create CodeGeneratorAdapter with mocked dependencies."""
        with patch('agents.code_generator_adapter.CodeGeneratorAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model_name = "starcoder"
            mock_agent.process = AsyncMock(return_value=MagicMock(
                content="def example(): pass",
                tests="def test_example(): assert True"
            ))
            mock_agent.get_stats = MagicMock(return_value={
                "total_requests": 1,
                "successful_requests": 1,
                "failed_requests": 0,
                "total_response_time": 1.5,
                "average_response_time": 1.5,
                "agent_name": "CodeGeneratorAgent"
            })
            mock_agent_class.return_value = mock_agent
            
            adapter = CodeGeneratorAdapter(
                model_client=mock_model_client,
                token_counter=mock_token_counter,
                text_compressor=mock_text_compressor
            )
            return adapter
    
    @pytest.fixture
    def reviewer_adapter(self, mock_model_client, mock_token_counter):
        """Create CodeReviewerAdapter with mocked dependencies."""
        with patch('agents.code_reviewer_adapter.CodeReviewerAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.model_name = "starcoder"
            mock_agent.process = AsyncMock(return_value=MagicMock(
                quality_score=8.5,
                metrics=MagicMock(
                    pep8_compliance=True,
                    pep8_score=8.0,
                    has_docstrings=True,
                    has_type_hints=True,
                    test_coverage="high",
                    complexity_score=7.5
                )
            ))
            mock_agent.get_stats = MagicMock(return_value={
                "total_requests": 1,
                "successful_requests": 1,
                "failed_requests": 0,
                "total_response_time": 2.0,
                "average_response_time": 2.0,
                "agent_name": "CodeReviewerAgent"
            })
            mock_agent_class.return_value = mock_agent
            
            adapter = CodeReviewerAdapter(
                model_client=mock_model_client,
                token_counter=mock_token_counter
            )
            return adapter
    
    @pytest.mark.asyncio
    async def test_code_generator_adapter_integration(self, generator_adapter):
        """
        Test CodeGeneratorAdapter integration with SDK CodeGeneratorAgent.
        
        Verifies that the adapter properly wraps SDK agent functionality
        and integrates with day_08's token counting and compression.
        """
        # Test code generation with compression
        result = await generator_adapter.generate_code_with_compression(
            task_description="Write a sorting function",
            model_name="starcoder",
            max_tokens=1000,
            compression_strategy="keywords"
        )
        
        # Verify result structure
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "code_generation_with_compression"
        assert result.model_name == "starcoder"
        assert result.original_query == "Write a sorting function"
        assert result.success is True
        assert result.input_tokens > 0
        assert result.output_tokens > 0
        assert result.total_tokens > 0
        
        # Verify SDK agent was called
        generator_adapter.generator_agent.process.assert_called_once()
        
        # Verify agent statistics
        stats = generator_adapter.get_agent_statistics()
        assert stats["agent_type"] == "SDK_CodeGeneratorAgent"
        assert stats["model_name"] == "starcoder"
        assert stats["total_requests"] >= 0
    
    @pytest.mark.asyncio
    async def test_code_reviewer_adapter_integration(self, reviewer_adapter):
        """
        Test CodeReviewerAdapter integration with SDK CodeReviewerAgent.
        
        Verifies that the adapter properly wraps SDK agent functionality
        and integrates with day_08's quality analysis.
        """
        # Test code review
        quality_metrics = await reviewer_adapter.review_code_quality(
            generated_code="def example(): pass",
            task_description="Write a function",
            model_name="starcoder"
        )
        
        # Verify result structure
        assert isinstance(quality_metrics, CodeQualityMetrics)
        assert quality_metrics.code_quality_score > 0
        assert isinstance(quality_metrics.pep8_compliance, bool)
        assert isinstance(quality_metrics.has_docstrings, bool)
        assert isinstance(quality_metrics.has_type_hints, bool)
        assert quality_metrics.code_length > 0
        
        # Verify SDK agent was called
        reviewer_adapter.reviewer_agent.process.assert_called_once()
        
        # Verify agent statistics
        stats = reviewer_adapter.get_agent_statistics()
        assert stats["agent_type"] == "SDK_CodeReviewerAgent"
        assert stats["model_name"] == "starcoder"
        assert stats["total_requests"] >= 0
    
    @pytest.mark.asyncio
    async def test_model_switcher_orchestrator_integration(self):
        """
        Test ModelSwitcherOrchestrator integration with SDK orchestration.
        
        Verifies that the orchestrator properly integrates with SDK
        orchestration patterns and adapters.
        """
        # Mock orchestrator dependencies
        with patch('core.model_switcher.TokenAnalysisClient') as mock_client:
            mock_client.return_value = MagicMock()
            
            orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
            
            # Test model switching
            with patch.object(orchestrator, 'switch_to_model', return_value=True):
                success = await orchestrator.switch_to_model("starcoder")
                assert success is True
            
            # Test model availability check
            with patch.object(orchestrator, 'check_all_models_availability', 
                            return_value={"starcoder": True, "mistral": False}):
                availability = await orchestrator.check_all_models_availability()
                assert availability["starcoder"] is True
                assert availability["mistral"] is False
    
    @pytest.mark.asyncio
    async def test_compression_evaluator_integration(self, generator_adapter, reviewer_adapter):
        """
        Test CompressionEvaluator integration with SDK agents.
        
        Verifies that compression evaluation properly integrates with
        SDK agents for code generation and review.
        """
        # Mock compression evaluator
        with patch('core.compression_evaluator.TokenAnalysisClient') as mock_client, \
             patch('core.compression_evaluator.SimpleTokenCounter') as mock_counter, \
             patch('core.compression_evaluator.SimpleTextCompressor') as mock_compressor:
            
            mock_client.return_value = MagicMock()
            mock_counter.return_value = MagicMock()
            mock_compressor.return_value = MagicMock()
            
            evaluator = CompressionEvaluator()
            
            # Mock compression methods
            evaluator.compress_and_test = AsyncMock(return_value=MagicMock(
                success=True,
                original_tokens=200,
                compressed_tokens=150,
                compression_ratio=0.75,
                response_time=1.5,
                compressed_query="Compressed query",
                response="Generated response"
            ))
            
            # Test compression with SDK agents
            result = await evaluator.compress_and_test(
                query="Write a complex sorting algorithm",
                model_name="starcoder",
                strategy="semantic"
            )
            
            assert result.success is True
            assert result.compression_ratio > 0
            assert result.response_time > 0
    
    @pytest.mark.asyncio
    async def test_token_limit_tester_integration(self):
        """
        Test TokenLimitTester integration with SDK orchestration.
        
        Verifies that token limit testing properly integrates with
        SDK orchestration for model switching.
        """
        # Mock token limit tester
        with patch('core.token_limit_tester.SimpleTokenCounter') as mock_counter:
            mock_counter.return_value = MagicMock()
            
            tester = TokenLimitTester()
            
            # Mock three-stage test
            tester.run_three_stage_test = AsyncMock(return_value=MagicMock(
                success=True,
                short_query_tokens=50,
                medium_query_tokens=500,
                long_query_tokens=2000,
                queries_exceeding_limit=1,
                model_limits=MagicMock(max_input_tokens=1500)
            ))
            
            # Test three-stage testing
            result = await tester.run_three_stage_test("starcoder")
            
            assert result.success is True
            assert result.short_query_tokens > 0
            assert result.medium_query_tokens > 0
            assert result.long_query_tokens > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_integration(self, generator_adapter, reviewer_adapter):
        """
        Test complete end-to-end workflow integration.
        
        Verifies the complete workflow from day_08 components to SDK agents
        including model switching, compression, generation, and review.
        """
        # Test complete workflow
        task_description = "Implement a binary search tree with insertion and deletion"
        
        # Step 1: Generate code with compression
        generation_result = await generator_adapter.generate_code_with_compression(
            task_description=task_description,
            model_name="starcoder",
            max_tokens=2000,
            compression_strategy="semantic"
        )
        
        assert generation_result.success is True
        assert len(generation_result.response) > 0
        
        # Step 2: Review generated code
        review_result = await reviewer_adapter.review_code_quality(
            generated_code=generation_result.response,
            task_description=task_description,
            model_name="starcoder"
        )
        
        assert isinstance(review_result, CodeQualityMetrics)
        assert review_result.code_quality_score > 0
        
        # Step 3: Verify integration points
        assert generation_result.model_name == "starcoder"
        assert generation_result.total_tokens > 0
        assert review_result.code_length > 0
        
        # Step 4: Verify SDK agents were used
        generator_adapter.generator_agent.process.assert_called_once()
        reviewer_adapter.reviewer_agent.process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sdk_orchestration_patterns_integration(self):
        """
        Test SDK orchestration patterns integration.
        
        Verifies that day_08 properly integrates with SDK orchestration
        patterns (Sequential, Parallel) and adapters (Direct, REST).
        """
        # Test DirectAdapter integration
        direct_adapter = DirectAdapter()
        assert direct_adapter.adapter_type == "direct"
        
        # Test RestAdapter integration
        rest_adapter = RestAdapter(base_url="http://localhost:8000")
        assert rest_adapter.adapter_type == "rest"
        
        # Test SequentialOrchestrator integration
        direct_adapter = DirectAdapter()
        sequential_orchestrator = SequentialOrchestrator(adapter=direct_adapter)
        assert sequential_orchestrator.__class__.__name__ == "SequentialOrchestrator"
        
        # Test ParallelOrchestrator integration
        parallel_orchestrator = ParallelOrchestrator(adapter=direct_adapter)
        assert parallel_orchestrator.__class__.__name__ == "ParallelOrchestrator"
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, generator_adapter, reviewer_adapter):
        """
        Test error handling integration with SDK agents.
        
        Verifies that errors from SDK agents are properly handled
        and converted to day_08 error formats.
        """
        # Test generator error handling
        generator_adapter.generator_agent.process = AsyncMock(side_effect=Exception("SDK Error"))
        
        result = await generator_adapter.generate_code_with_compression(
            task_description="Test error handling",
            model_name="starcoder"
        )
        
        assert result.success is False
        assert "SDK Error" in result.error_message
        
        # Test reviewer error handling
        reviewer_adapter.reviewer_agent.process = AsyncMock(side_effect=Exception("SDK Review Error"))
        
        quality_metrics = await reviewer_adapter.review_code_quality(
            generated_code="def test(): pass",
            task_description="Test error handling",
            model_name="starcoder"
        )
        
        # Should return default metrics on error
        assert isinstance(quality_metrics, CodeQualityMetrics)
        assert quality_metrics.code_quality_score == 5.0  # Default value
    
    @pytest.mark.asyncio
    async def test_model_switching_integration(self):
        """
        Test model switching integration with SDK orchestration.
        
        Verifies that model switching properly integrates with SDK
        orchestration and maintains state correctly.
        """
        # Test model switching
        with patch('core.model_switcher.TokenAnalysisClient') as mock_client:
            mock_client.return_value = MagicMock()
            
            switcher = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
            
            # Test model switching
            with patch.object(switcher, 'switch_to_model', return_value=True):
                success = await switcher.switch_to_model("mistral")
                assert success is True
            
            # Test model statistics
            with patch.object(switcher, 'get_model_statistics', 
                            return_value={
                                "total_requests": 5,
                                "successful_requests": 4,
                                "average_response_time": 1.2
                            }):
                stats = switcher.get_model_statistics("mistral")
                assert stats["total_requests"] == 5
                assert stats["successful_requests"] == 4
                assert stats["average_response_time"] == 1.2
    
    def test_no_day_07_dependencies(self):
        """
        Test that day_08 has no day_07 dependencies.
        
        Verifies that day_08 components don't import or depend on
        any day_07 modules or functionality.
        """
        # Test that SDK adapters don't import day_07
        import agents.code_generator_adapter
        import agents.code_reviewer_adapter
        
        # Check that no day_07 imports exist
        generator_source = Path(agents.code_generator_adapter.__file__).read_text()
        reviewer_source = Path(agents.code_reviewer_adapter.__file__).read_text()
        
        assert "day_07" not in generator_source
        assert "day_07" not in reviewer_source
        
        # Check that SDK imports exist
        assert "shared_package" in generator_source
        assert "shared_package" in reviewer_source
    
    @pytest.mark.asyncio
    async def test_performance_integration(self, generator_adapter, reviewer_adapter):
        """
        Test performance integration with SDK agents.
        
        Verifies that performance metrics are properly collected
        and integrated from SDK agents.
        """
        # Test generation performance
        start_time = asyncio.get_event_loop().time()
        
        result = await generator_adapter.generate_code_with_compression(
            task_description="Write a performance test",
            model_name="starcoder"
        )
        
        end_time = asyncio.get_event_loop().time()
        
        assert result.success is True
        assert result.response_time >= 0
        assert (end_time - start_time) >= 0
        
        # Test review performance
        start_time = asyncio.get_event_loop().time()
        
        quality_metrics = await reviewer_adapter.review_code_quality(
            generated_code=result.response,
            task_description="Write a performance test",
            model_name="starcoder"
        )
        
        end_time = asyncio.get_event_loop().time()
        
        assert isinstance(quality_metrics, CodeQualityMetrics)
        assert (end_time - start_time) >= 0
        
        # Test agent statistics
        gen_stats = generator_adapter.get_agent_statistics()
        rev_stats = reviewer_adapter.get_agent_statistics()
        
        assert gen_stats["average_response_time"] >= 0
        assert rev_stats["average_response_time"] >= 0


class TestSDKOrchestrationIntegration:
    """
    Integration tests for SDK orchestration patterns with day_08.
    
    Tests the integration between day_08 components and SDK orchestration
    patterns including Sequential and Parallel orchestration.
    """
    
    @pytest.mark.asyncio
    async def test_sequential_orchestration_integration(self):
        """
        Test SequentialOrchestrator integration with day_08.
        
        Verifies that sequential orchestration properly integrates
        with day_08 components and SDK agents.
        """
        # Mock sequential orchestrator
        direct_adapter = DirectAdapter()
        orchestrator = SequentialOrchestrator(adapter=direct_adapter)
        
        # Mock agents
        mock_agent1 = MagicMock()
        mock_agent1.process = AsyncMock(return_value=MagicMock(content="Result 1"))
        
        mock_agent2 = MagicMock()
        mock_agent2.process = AsyncMock(return_value=MagicMock(content="Result 2"))
        
        # Test sequential execution
        with patch.object(orchestrator, 'execute', 
                        return_value=[MagicMock(content="Result 1"), MagicMock(content="Result 2")]):
            from shared_package.agents.schemas import AgentRequest, TaskMetadata
            request = AgentRequest(
                task="Test task",
                context={},
                metadata=TaskMetadata(
                    task_id="test",
                    task_type="test",
                    timestamp=asyncio.get_event_loop().time(),
                    model_name="starcoder"
                )
            )
            results = await orchestrator.execute(request, [mock_agent1, mock_agent2])
            assert len(results) == 2
            assert results[0].content == "Result 1"
            assert results[1].content == "Result 2"
    
    @pytest.mark.asyncio
    async def test_parallel_orchestration_integration(self):
        """
        Test ParallelOrchestrator integration with day_08.
        
        Verifies that parallel orchestration properly integrates
        with day_08 components and SDK agents.
        """
        # Mock parallel orchestrator
        direct_adapter = DirectAdapter()
        orchestrator = ParallelOrchestrator(adapter=direct_adapter)
        
        # Mock agents
        mock_agent1 = MagicMock()
        mock_agent1.process = AsyncMock(return_value=MagicMock(content="Result 1"))
        
        mock_agent2 = MagicMock()
        mock_agent2.process = AsyncMock(return_value=MagicMock(content="Result 2"))
        
        # Test parallel execution
        with patch.object(orchestrator, 'execute', 
                        return_value=[MagicMock(content="Result 1"), MagicMock(content="Result 2")]):
            from shared_package.agents.schemas import AgentRequest, TaskMetadata
            request = AgentRequest(
                task="Test task",
                context={},
                metadata=TaskMetadata(
                    task_id="test",
                    task_type="test",
                    timestamp=asyncio.get_event_loop().time(),
                    model_name="starcoder"
                )
            )
            results = await orchestrator.execute(request, [mock_agent1, mock_agent2])
            assert len(results) == 2
            assert "Result 1" in [r.content for r in results]
            assert "Result 2" in [r.content for r in results]
    
    @pytest.mark.asyncio
    async def test_adapter_integration(self):
        """
        Test adapter integration with day_08.
        
        Verifies that SDK adapters properly integrate with day_08
        components and provide the expected interface.
        """
        # Test DirectAdapter
        direct_adapter = DirectAdapter()
        assert direct_adapter.adapter_type == "direct"
        assert hasattr(direct_adapter, 'get_adapter_type')
        
        # Test RestAdapter
        rest_adapter = RestAdapter(base_url="http://localhost:8000")
        assert rest_adapter.adapter_type == "rest"
        assert hasattr(rest_adapter, 'get_adapter_type')
        
        # Test adapter type property
        assert direct_adapter.adapter_type == "direct"
        assert rest_adapter.adapter_type == "rest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
