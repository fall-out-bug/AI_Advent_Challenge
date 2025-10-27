"""
Smoke tests for day_08 demos and basic functionality.

This module provides smoke tests to verify that all demo scripts
and basic functionality work correctly with SDK integration.
"""

import asyncio
import pytest
import sys
import subprocess
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


class TestDemoSmokeTests:
    """
    Smoke tests for demo scripts and basic functionality.
    
    Tests that all demo scripts can be imported and initialized
    without errors, and that basic functionality works.
    """
    
    def test_demo_enhanced_import(self):
        """Test that demo_enhanced.py can be imported successfully."""
        try:
            from demo_enhanced import EnhancedModelSwitchingDemo
            assert EnhancedModelSwitchingDemo is not None
        except ImportError as e:
            pytest.fail(f"Failed to import demo_enhanced: {e}")
    
    def test_demo_model_switching_import(self):
        """Test that demo_model_switching.py can be imported successfully."""
        try:
            from demo_model_switching import ModelSwitchingDemo
            assert ModelSwitchingDemo is not None
        except ImportError as e:
            pytest.fail(f"Failed to import demo_model_switching: {e}")
    
    def test_demo_enhanced_initialization(self):
        """Test that EnhancedModelSwitchingDemo can be initialized."""
        try:
            from demo_enhanced import EnhancedModelSwitchingDemo
            
            # Mock dependencies to avoid actual model calls
            with patch('demo_enhanced.ModelSwitcherOrchestrator') as mock_orchestrator, \
                 patch('demo_enhanced.TokenLimitTester') as mock_tester, \
                 patch('demo_enhanced.CompressionEvaluator') as mock_evaluator, \
                 patch('demo_enhanced.CodeGeneratorAdapter') as mock_generator, \
                 patch('demo_enhanced.CodeReviewerAdapter') as mock_reviewer:
                
                demo = EnhancedModelSwitchingDemo()
                assert demo is not None
                assert hasattr(demo, 'run_enhanced_demo')
                assert hasattr(demo, 'config')
                assert hasattr(demo, 'results')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize EnhancedModelSwitchingDemo: {e}")
    
    def test_demo_model_switching_initialization(self):
        """Test that ModelSwitchingDemo can be initialized."""
        try:
            from demo_model_switching import ModelSwitchingDemo
            
            # Mock dependencies to avoid actual model calls
            with patch('demo_model_switching.ModelSwitcherOrchestrator') as mock_orchestrator, \
                 patch('demo_model_switching.TokenLimitTester') as mock_tester, \
                 patch('demo_model_switching.CompressionEvaluator') as mock_evaluator, \
                 patch('demo_model_switching.QualityAnalyzer') as mock_analyzer, \
                 patch('demo_model_switching.CodeGeneratorAdapter') as mock_generator, \
                 patch('demo_model_switching.CodeReviewerAdapter') as mock_reviewer:
                
                demo = ModelSwitchingDemo()
                assert demo is not None
                assert hasattr(demo, 'run_complete_demo')
                assert hasattr(demo, 'config')
                assert hasattr(demo, 'results')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize ModelSwitchingDemo: {e}")
    
    def test_config_loading(self):
        """Test that configuration can be loaded successfully."""
        try:
            from config.demo_config import get_config, get_model_config
            
            config = get_config()
            assert config is not None
            assert isinstance(config, dict)
            assert "models" in config
            
            model_config = get_model_config("starcoder")
            assert model_config is not None
            assert isinstance(model_config, dict)
            
        except Exception as e:
            pytest.fail(f"Failed to load configuration: {e}")
    
    def test_sdk_agents_availability(self):
        """Test that SDK agents are available and can be imported."""
        try:
            from shared_package.agents.code_generator import CodeGeneratorAgent
            from shared_package.agents.code_reviewer import CodeReviewerAgent
            
            assert CodeGeneratorAgent is not None
            assert CodeReviewerAgent is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import SDK agents: {e}")
    
    def test_sdk_orchestration_availability(self):
        """Test that SDK orchestration components are available."""
        try:
            from shared_package.orchestration.adapters import DirectAdapter, RestAdapter
            from shared_package.orchestration.sequential import SequentialOrchestrator
            from shared_package.orchestration.parallel import ParallelOrchestrator
            
            assert DirectAdapter is not None
            assert RestAdapter is not None
            assert SequentialOrchestrator is not None
            assert ParallelOrchestrator is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import SDK orchestration components: {e}")
    
    def test_agent_adapters_availability(self):
        """Test that agent adapters are available and can be imported."""
        try:
            from agents.code_generator_adapter import CodeGeneratorAdapter
            from agents.code_reviewer_adapter import CodeReviewerAdapter
            
            assert CodeGeneratorAdapter is not None
            assert CodeReviewerAdapter is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import agent adapters: {e}")
    
    def test_core_components_availability(self):
        """Test that core components are available and can be imported."""
        try:
            from core.model_switcher import ModelSwitcherOrchestrator
            from core.compression_evaluator import CompressionEvaluator
            from core.token_limit_tester import TokenLimitTester
            from core.quality_analyzer import QualityAnalyzer
            
            assert ModelSwitcherOrchestrator is not None
            assert CompressionEvaluator is not None
            assert TokenLimitTester is not None
            assert QualityAnalyzer is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import core components: {e}")
    
    def test_data_models_availability(self):
        """Test that data models are available and can be imported."""
        try:
            from models.data_models import (
                ExperimentResult,
                ThreeStageResult,
                CompressionTestResult,
                CodeQualityMetrics,
                ModelWorkflowResult
            )
            
            assert ExperimentResult is not None
            assert ThreeStageResult is not None
            assert CompressionTestResult is not None
            assert CodeQualityMetrics is not None
            assert ModelWorkflowResult is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import data models: {e}")
    
    def test_utils_availability(self):
        """Test that utility modules are available and can be imported."""
        try:
            from utils.logging import LoggerFactory
            from utils.report_generator import ReportGenerator
            
            assert LoggerFactory is not None
            assert ReportGenerator is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import utility modules: {e}")


class TestDemoScriptSmokeTests:
    """
    Smoke tests for demo script execution.
    
    Tests that demo scripts can be executed without critical errors,
    focusing on initialization and basic functionality.
    """
    
    def test_demo_enhanced_script_syntax(self):
        """Test that demo_enhanced.py has valid syntax."""
        demo_path = Path(__file__).parent.parent.parent / "demo_enhanced.py"
        
        try:
            # Check syntax by compiling the file
            with open(demo_path, 'r') as f:
                source = f.read()
            compile(source, str(demo_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in demo_enhanced.py: {e}")
        except Exception as e:
            pytest.fail(f"Error checking demo_enhanced.py syntax: {e}")
    
    def test_demo_model_switching_script_syntax(self):
        """Test that demo_model_switching.py has valid syntax."""
        demo_path = Path(__file__).parent.parent.parent / "demo_model_switching.py"
        
        try:
            # Check syntax by compiling the file
            with open(demo_path, 'r') as f:
                source = f.read()
            compile(source, str(demo_path), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in demo_model_switching.py: {e}")
        except Exception as e:
            pytest.fail(f"Error checking demo_model_switching.py syntax: {e}")
    
    def test_demo_enhanced_script_imports(self):
        """Test that demo_enhanced.py can import all required modules."""
        demo_path = Path(__file__).parent.parent.parent / "demo_enhanced.py"
        
        try:
            # Test imports by executing the file in a subprocess
            result = subprocess.run([
                sys.executable, "-c", 
                f"import sys; sys.path.insert(0, '{demo_path.parent}'); exec(open('{demo_path}').read())"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                pytest.fail(f"Import error in demo_enhanced.py: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("demo_enhanced.py import test timed out")
        except Exception as e:
            pytest.fail(f"Error testing demo_enhanced.py imports: {e}")
    
    def test_demo_model_switching_script_imports(self):
        """Test that demo_model_switching.py can import all required modules."""
        demo_path = Path(__file__).parent.parent.parent / "demo_model_switching.py"
        
        try:
            # Test imports by executing the file in a subprocess
            result = subprocess.run([
                sys.executable, "-c", 
                f"import sys; sys.path.insert(0, '{demo_path.parent}'); exec(open('{demo_path}').read())"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                pytest.fail(f"Import error in demo_model_switching.py: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("demo_model_switching.py import test timed out")
        except Exception as e:
            pytest.fail(f"Error testing demo_model_switching.py imports: {e}")
    
    def test_demo_enhanced_script_help(self):
        """Test that demo_enhanced.py can show help without errors."""
        demo_path = Path(__file__).parent.parent.parent / "demo_enhanced.py"
        
        try:
            # Test help by running with --help flag
            result = subprocess.run([
                sys.executable, str(demo_path), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Help should either succeed or fail gracefully
            if result.returncode != 0 and "error" in result.stderr.lower():
                pytest.fail(f"Help error in demo_enhanced.py: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("demo_enhanced.py help test timed out")
        except Exception as e:
            pytest.fail(f"Error testing demo_enhanced.py help: {e}")
    
    def test_demo_model_switching_script_help(self):
        """Test that demo_model_switching.py can show help without errors."""
        demo_path = Path(__file__).parent.parent.parent / "demo_model_switching.py"
        
        try:
            # Test help by running with --help flag
            result = subprocess.run([
                sys.executable, str(demo_path), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Help should either succeed or fail gracefully
            if result.returncode != 0 and "error" in result.stderr.lower():
                pytest.fail(f"Help error in demo_model_switching.py: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            pytest.fail("demo_model_switching.py help test timed out")
        except Exception as e:
            pytest.fail(f"Error testing demo_model_switching.py help: {e}")


class TestSDKIntegrationSmokeTests:
    """
    Smoke tests for SDK integration components.
    
    Tests that SDK integration components can be initialized
    and provide basic functionality without errors.
    """
    
    def test_code_generator_adapter_smoke(self):
        """Test that CodeGeneratorAdapter can be initialized."""
        try:
            from agents.code_generator_adapter import CodeGeneratorAdapter
            
            # Mock dependencies to avoid actual model calls
            with patch('agents.code_generator_adapter.CodeGeneratorAgent') as mock_agent_class, \
                 patch('agents.code_generator_adapter.TokenAnalysisClient') as mock_client, \
                 patch('agents.code_generator_adapter.SimpleTokenCounter') as mock_counter, \
                 patch('agents.code_generator_adapter.SimpleTextCompressor') as mock_compressor:
                
                mock_agent_class.return_value = MagicMock()
                mock_client.return_value = MagicMock()
                mock_counter.return_value = MagicMock()
                mock_compressor.return_value = MagicMock()
                
                adapter = CodeGeneratorAdapter()
                assert adapter is not None
                assert hasattr(adapter, 'generate_code_with_compression')
                assert hasattr(adapter, 'get_agent_statistics')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize CodeGeneratorAdapter: {e}")
    
    def test_code_reviewer_adapter_smoke(self):
        """Test that CodeReviewerAdapter can be initialized."""
        try:
            from agents.code_reviewer_adapter import CodeReviewerAdapter
            
            # Mock dependencies to avoid actual model calls
            with patch('agents.code_reviewer_adapter.CodeReviewerAgent') as mock_agent_class, \
                 patch('agents.code_reviewer_adapter.TokenAnalysisClient') as mock_client, \
                 patch('agents.code_reviewer_adapter.SimpleTokenCounter') as mock_counter:
                
                mock_agent_class.return_value = MagicMock()
                mock_client.return_value = MagicMock()
                mock_counter.return_value = MagicMock()
                
                adapter = CodeReviewerAdapter()
                assert adapter is not None
                assert hasattr(adapter, 'review_code_quality')
                assert hasattr(adapter, 'get_agent_statistics')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize CodeReviewerAdapter: {e}")
    
    def test_model_switcher_orchestrator_smoke(self):
        """Test that ModelSwitcherOrchestrator can be initialized."""
        try:
            from core.model_switcher import ModelSwitcherOrchestrator
            
            # Mock dependencies to avoid actual model calls
            with patch('core.model_switcher.ModelSwitcherOrchestrator._initialize_components'):
                orchestrator = ModelSwitcherOrchestrator(models=["starcoder"])
                assert orchestrator is not None
                assert hasattr(orchestrator, 'switch_to_model')
                assert hasattr(orchestrator, 'check_all_models_availability')
                assert hasattr(orchestrator, 'get_model_statistics')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize ModelSwitcherOrchestrator: {e}")
    
    def test_compression_evaluator_smoke(self):
        """Test that CompressionEvaluator can be initialized."""
        try:
            from core.compression_evaluator import CompressionEvaluator
            
            # Mock dependencies to avoid actual model calls
            with patch('core.compression_evaluator.CompressionEvaluator._initialize_components'):
                evaluator = CompressionEvaluator()
                assert evaluator is not None
                assert hasattr(evaluator, 'compress_and_test')
                assert hasattr(evaluator, 'test_all_compressions')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize CompressionEvaluator: {e}")
    
    def test_token_limit_tester_smoke(self):
        """Test that TokenLimitTester can be initialized."""
        try:
            from core.token_limit_tester import TokenLimitTester
            
            # Mock dependencies to avoid actual model calls
            with patch('core.token_limit_tester.TokenLimitTester._initialize_components'):
                tester = TokenLimitTester()
                assert tester is not None
                assert hasattr(tester, 'run_three_stage_test')
                assert hasattr(tester, 'test_single_query')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize TokenLimitTester: {e}")
    
    def test_quality_analyzer_smoke(self):
        """Test that QualityAnalyzer can be initialized."""
        try:
            from core.quality_analyzer import QualityAnalyzer
            
            # Mock dependencies to avoid actual model calls
            with patch('core.quality_analyzer.QualityAnalyzer._initialize_components'):
                analyzer = QualityAnalyzer()
                assert analyzer is not None
                assert hasattr(analyzer, 'analyze_completeness')
                assert hasattr(analyzer, 'analyze_quality')
                
        except Exception as e:
            pytest.fail(f"Failed to initialize QualityAnalyzer: {e}")


class TestConfigurationSmokeTests:
    """
    Smoke tests for configuration loading and validation.
    
    Tests that configuration can be loaded and validated
    without errors.
    """
    
    def test_demo_config_loading(self):
        """Test that demo configuration can be loaded."""
        try:
            from config.demo_config import get_config, get_model_config, get_quality_thresholds
            
            config = get_config()
            assert config is not None
            assert isinstance(config, dict)
            assert "models" in config
            assert isinstance(config["models"], list)
            
            model_config = get_model_config("starcoder")
            assert model_config is not None
            assert isinstance(model_config, dict)
            
            thresholds = get_quality_thresholds()
            assert thresholds is not None
            assert isinstance(thresholds, dict)
            
        except Exception as e:
            pytest.fail(f"Failed to load demo configuration: {e}")
    
    def test_model_config_validation(self):
        """Test that model configuration is valid."""
        try:
            from config.demo_config import get_model_config, is_model_supported
            
            # Test supported models
            supported_models = ["starcoder", "mistral", "qwen", "tinyllama"]
            
            for model in supported_models:
                config = get_model_config(model)
                assert config is not None
                assert isinstance(config, dict)
                
                is_supported = is_model_supported(model)
                assert isinstance(is_supported, bool)
                
        except Exception as e:
            pytest.fail(f"Failed to validate model configuration: {e}")
    
    def test_compression_algorithms_config(self):
        """Test that compression algorithms configuration is valid."""
        try:
            from config.demo_config import get_compression_algorithms
            
            algorithms = get_compression_algorithms()
            assert algorithms is not None
            assert isinstance(algorithms, list)
            assert len(algorithms) > 0
            
            # Check that all algorithms are strings
            for algorithm in algorithms:
                assert isinstance(algorithm, str)
                assert len(algorithm) > 0
                
        except Exception as e:
            pytest.fail(f"Failed to validate compression algorithms configuration: {e}")
    
    def test_task_template_config(self):
        """Test that task template configuration is valid."""
        try:
            from config.demo_config import get_task_template
            
            template = get_task_template()
            assert template is not None
            assert isinstance(template, str)
            assert len(template) > 0
            
        except Exception as e:
            pytest.fail(f"Failed to validate task template configuration: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
