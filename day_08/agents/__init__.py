"""
Agent adapters for integrating day_07 agents with day_08 system.

This module provides adapters that wrap day_07 CodeGeneratorAgent and 
CodeReviewerAgent for seamless integration with the day_08 token analysis
and compression system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add day_07 to path for importing agents
day_07_path = Path(__file__).parent.parent.parent / "day_07"
sys.path.insert(0, str(day_07_path))

# Try to import day_07 agents with silent fallback
_DAY_07_AVAILABLE = False
CodeGeneratorAgent = None
CodeReviewerAgent = None
CodeGenerationRequest = None
CodeGenerationResponse = None
CodeReviewRequest = None
CodeReviewResponse = None
TaskMetadata = None

try:
    from agents.core.code_generator import CodeGeneratorAgent
    from agents.core.code_reviewer import CodeReviewerAgent
    from communication.message_schema import (
        CodeGenerationRequest,
        CodeGenerationResponse,
        CodeReviewRequest,
        CodeReviewResponse,
        TaskMetadata
    )
    _DAY_07_AVAILABLE = True
except ImportError:
    # Day_07 agents not available - this is expected in some environments
    # The adapters will use fallback methods instead
    pass

from core.ml_client import TokenAnalysisClient
from core.token_analyzer import SimpleTokenCounter
from core.text_compressor import SimpleTextCompressor
from models.data_models import (
    ExperimentResult,
    CompressionResult,
    CodeQualityMetrics,
    PerformanceMetrics
)
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class CodeGeneratorAdapter:
    """
    Adapter for day_07 CodeGeneratorAgent with day_08 integration.
    
    Wraps the day_07 CodeGeneratorAgent and integrates it with day_08's
    token counting, compression, and analysis capabilities.
    
    Attributes:
        generator_agent: day_07 CodeGeneratorAgent instance
        model_client: TokenAnalysisClient for model interactions
        token_counter: TokenCounter for token counting
        text_compressor: TextCompressor for compression
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from agents.code_generator_adapter import CodeGeneratorAdapter
        from core.ml_client import TokenAnalysisClient
        from core.token_analyzer import SimpleTokenCounter
        from core.text_compressor import SimpleTextCompressor
        
        # Initialize adapter
        model_client = TokenAnalysisClient()
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)
        
        adapter = CodeGeneratorAdapter(
            model_client=model_client,
            token_counter=token_counter,
            text_compressor=text_compressor
        )
        
        # Generate code with compression
        result = await adapter.generate_code_with_compression(
            task_description="Write a sorting function",
            model_name="starcoder",
            max_tokens=1000
        )
        ```
    """
    
    def __init__(
        self,
        model_client: Optional[TokenAnalysisClient] = None,
        token_counter: Optional[SimpleTokenCounter] = None,
        text_compressor: Optional[SimpleTextCompressor] = None,
        model_name: str = "starcoder"
    ):
        """
        Initialize the code generator adapter.
        
        Args:
            model_client: Optional TokenAnalysisClient instance
            token_counter: Optional TokenCounter instance
            text_compressor: Optional TextCompressor instance
            model_name: Default model name to use
            
        Example:
            ```python
            from agents.code_generator_adapter import CodeGeneratorAdapter
            
            # Initialize with default components
            adapter = CodeGeneratorAdapter()
            
            # Or with custom components
            adapter = CodeGeneratorAdapter(
                model_client=custom_client,
                token_counter=custom_counter,
                text_compressor=custom_compressor,
                model_name="mistral"
            )
            ```
        """
        self.model_client = model_client or TokenAnalysisClient()
        self.token_counter = token_counter or SimpleTokenCounter()
        self.text_compressor = text_compressor or SimpleTextCompressor(self.token_counter)
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Initialize day_07 generator agent if available
        if CodeGeneratorAgent:
            try:
                self.generator_agent = CodeGeneratorAgent(
                    model_name=model_name,
                    max_tokens=2000,
                    temperature=0.7
                )
                self.logger.info(f"Initialized CodeGeneratorAgent with {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CodeGeneratorAgent: {e}")
                self.generator_agent = None
        else:
            self.generator_agent = None
            self.logger.warning("CodeGeneratorAgent not available")
        
        self.logger.info("Initialized CodeGeneratorAdapter")
    
    async def generate_code_with_compression(
        self,
        task_description: str,
        model_name: str,
        max_tokens: int = 1000,
        compression_strategy: str = "truncation",
        language: str = "python",
        requirements: Optional[List[str]] = None
    ) -> ExperimentResult:
        """
        Generate code with automatic compression if needed.
        
        Args:
            task_description: Description of the coding task
            model_name: Name of the model to use
            max_tokens: Maximum tokens for generation
            compression_strategy: Compression strategy to use if needed
            language: Programming language
            requirements: Additional requirements
            
        Returns:
            ExperimentResult containing generation results
            
        Example:
            ```python
            # Generate code with compression
            result = await adapter.generate_code_with_compression(
                task_description="Implement a binary search tree",
                model_name="starcoder",
                max_tokens=1500,
                compression_strategy="keywords"
            )
            
            print(f"Success: {result.success}")
            print(f"Tokens used: {result.total_tokens}")
            if result.compression_result:
                print(f"Compression ratio: {result.compression_result.compression_ratio}")
            ```
        """
        try:
            self.logger.info(f"Generating code for: {task_description[:50]}...")
            
            # Check if task exceeds token limits
            model_limits = self.token_counter.get_model_limits(model_name)
            task_tokens = self.token_counter.count_tokens(task_description, model_name).count
            
            processed_query = task_description
            compression_result = None
            
            # Apply compression if needed
            if task_tokens > model_limits.max_input_tokens:
                self.logger.info(f"Task exceeds limit ({task_tokens} > {model_limits.max_input_tokens}), applying compression...")
                
                compression_result = self.text_compressor.compress_text(
                    text=task_description,
                    max_tokens=model_limits.recommended_input or model_limits.max_input_tokens,
                    model_name=model_name,
                    strategy=compression_strategy
                )
                
                processed_query = compression_result.compressed_text
                self.logger.info(f"Compressed from {compression_result.original_tokens} to {compression_result.compressed_tokens} tokens")
            
            # Generate code using day_07 agent or fallback
            if self.generator_agent:
                response = await self._generate_with_day_07_agent(
                    processed_query, model_name, max_tokens, language, requirements
                )
            else:
                response = await self._generate_with_fallback(
                    processed_query, model_name, max_tokens
                )
            
            # Count tokens
            input_tokens = self.token_counter.count_tokens(processed_query, model_name).count
            output_tokens = self.token_counter.count_tokens(response, model_name).count
            
            return ExperimentResult(
                experiment_name="code_generation_with_compression",
                model_name=model_name,
                original_query=task_description,
                processed_query=processed_query,
                response=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                response_time=0.0,  # Will be updated by caller
                compression_applied=compression_result is not None,
                compression_result=compression_result
            )
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            
            return ExperimentResult(
                experiment_name="code_generation_with_compression",
                model_name=model_name,
                original_query=task_description,
                processed_query=task_description,
                response="",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=0.0,
                compression_applied=False,
                compression_result=None,
                success=False,
                error_message=str(e)
            )
    
    async def _generate_with_day_07_agent(
        self,
        query: str,
        model_name: str,
        max_tokens: int,
        language: str,
        requirements: Optional[List[str]]
    ) -> str:
        """Generate code using day_07 CodeGeneratorAgent."""
        try:
            # Create request for day_07 agent
            request = CodeGenerationRequest(
                task_description=query,
                language=language,
                requirements=requirements or [],
                model_name=model_name
            )
            
            # Generate code
            response = await self.generator_agent.process(request)
            
            # Extract code from response
            generated_code = response.generated_code
            tests = response.tests
            
            # Combine code and tests
            full_response = f"{generated_code}\n\n# Tests\n{tests}" if tests else generated_code
            
            return full_response
            
        except Exception as e:
            self.logger.error(f"Day_07 agent generation failed: {e}")
            raise
    
    async def _generate_with_fallback(
        self,
        query: str,
        model_name: str,
        max_tokens: int
    ) -> str:
        """Fallback code generation using direct model client."""
        try:
            # Create a simple prompt for code generation
            prompt = f"""Write Python code for the following task:

{query}

Requirements:
- Include proper docstrings
- Add type hints
- Follow PEP8 style
- Include error handling
- Provide example usage

Code:"""
            
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.response
            
        except Exception as e:
            self.logger.error(f"Fallback generation failed: {e}")
            raise
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics from the underlying generator agent."""
        if self.generator_agent:
            return {
                "agent_type": "CodeGeneratorAgent",
                "model_name": self.generator_agent.model_name,
                "total_requests": self.generator_agent.stats["total_requests"],
                "successful_requests": self.generator_agent.stats["successful_requests"],
                "failed_requests": self.generator_agent.stats["failed_requests"],
                "total_tokens_used": self.generator_agent.stats["total_tokens_used"],
                "average_response_time": self.generator_agent.get_average_response_time(),
                "uptime": self.generator_agent.get_uptime()
            }
        else:
            return {
                "agent_type": "FallbackGenerator",
                "status": "day_07 agent not available"
            }


class CodeReviewerAdapter:
    """
    Adapter for day_07 CodeReviewerAgent with day_08 integration.
    
    Wraps the day_07 CodeReviewerAgent and integrates it with day_08's
    quality analysis and metrics collection.
    
    Attributes:
        reviewer_agent: day_07 CodeReviewerAgent instance
        model_client: TokenAnalysisClient for model interactions
        token_counter: TokenCounter for token counting
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from agents.code_reviewer_adapter import CodeReviewerAdapter
        from core.ml_client import TokenAnalysisClient
        from core.token_analyzer import SimpleTokenCounter
        
        # Initialize adapter
        model_client = TokenAnalysisClient()
        token_counter = SimpleTokenCounter()
        
        adapter = CodeReviewerAdapter(
            model_client=model_client,
            token_counter=token_counter
        )
        
        # Review code quality
        quality_metrics = await adapter.review_code_quality(
            generated_code="def example(): pass",
            task_description="Write a function",
            model_name="starcoder"
        )
        ```
    """
    
    def __init__(
        self,
        model_client: Optional[TokenAnalysisClient] = None,
        token_counter: Optional[SimpleTokenCounter] = None,
        model_name: str = "starcoder"
    ):
        """
        Initialize the code reviewer adapter.
        
        Args:
            model_client: Optional TokenAnalysisClient instance
            token_counter: Optional TokenCounter instance
            model_name: Default model name to use
            
        Example:
            ```python
            from agents.code_reviewer_adapter import CodeReviewerAdapter
            
            # Initialize with default components
            adapter = CodeReviewerAdapter()
            
            # Or with custom components
            adapter = CodeReviewerAdapter(
                model_client=custom_client,
                token_counter=custom_counter,
                model_name="mistral"
            )
            ```
        """
        self.model_client = model_client or TokenAnalysisClient()
        self.token_counter = token_counter or SimpleTokenCounter()
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Initialize day_07 reviewer agent if available
        if CodeReviewerAgent:
            try:
                self.reviewer_agent = CodeReviewerAgent(
                    model_name=model_name,
                    max_tokens=1500,
                    temperature=0.2
                )
                self.logger.info(f"Initialized CodeReviewerAgent with {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize CodeReviewerAgent: {e}")
                self.reviewer_agent = None
        else:
            self.reviewer_agent = None
            self.logger.warning("CodeReviewerAgent not available")
        
        self.logger.info("Initialized CodeReviewerAdapter")
    
    async def review_code_quality(
        self,
        generated_code: str,
        task_description: str,
        model_name: str,
        tests: Optional[str] = None
    ) -> CodeQualityMetrics:
        """
        Review code quality using day_07 reviewer agent.
        
        Args:
            generated_code: Generated code to review
            task_description: Original task description
            model_name: Name of the model used
            tests: Optional test code
            
        Returns:
            CodeQualityMetrics containing quality assessment
            
        Example:
            ```python
            # Review code quality
            quality_metrics = await adapter.review_code_quality(
                generated_code="def example(): pass",
                task_description="Write a function",
                model_name="starcoder",
                tests="def test_example(): assert example() is None"
            )
            
            print(f"Quality score: {quality_metrics.code_quality_score:.2f}")
            print(f"PEP8 compliant: {quality_metrics.pep8_compliance}")
            ```
        """
        try:
            self.logger.info("Reviewing code quality...")
            
            # Use day_07 agent or fallback
            if self.reviewer_agent:
                quality_metrics = await self._review_with_day_07_agent(
                    generated_code, task_description, tests
                )
            else:
                quality_metrics = await self._review_with_fallback(
                    generated_code, task_description, model_name
                )
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Code review failed: {e}")
            
            # Return default metrics on error
            return CodeQualityMetrics(
                code_quality_score=5.0,
                pep8_compliance=False,
                pep8_score=5.0,
                has_docstrings=False,
                has_type_hints=False,
                test_coverage="unknown",
                complexity_score=5.0,
                requirements_coverage=0.5,
                completeness_score=0.5,
                code_length=len(generated_code),
                function_count=generated_code.count("def "),
                class_count=generated_code.count("class ")
            )
    
    async def _review_with_day_07_agent(
        self,
        generated_code: str,
        task_description: str,
        tests: Optional[str]
    ) -> CodeQualityMetrics:
        """Review code using day_07 CodeReviewerAgent."""
        try:
            # Create request for day_07 agent
            request = CodeReviewRequest(
                task_description=task_description,
                generated_code=generated_code,
                tests=tests or "",
                metadata=TaskMetadata(
                    complexity="medium",
                    lines_of_code=len(generated_code.split('\n')),
                    estimated_time="5 minutes",
                    dependencies=[]
                )
            )
            
            # Review code
            response = await self.reviewer_agent.process(request)
            
            # Convert to CodeQualityMetrics
            return CodeQualityMetrics(
                code_quality_score=response.code_quality_score,
                pep8_compliance=response.metrics.pep8_compliance,
                pep8_score=response.metrics.pep8_score,
                has_docstrings=response.metrics.has_docstrings,
                has_type_hints=response.metrics.has_type_hints,
                test_coverage=response.metrics.test_coverage,
                complexity_score=response.metrics.complexity_score,
                requirements_coverage=0.8,  # Default value
                completeness_score=0.8,    # Default value
                code_length=len(generated_code),
                function_count=generated_code.count("def "),
                class_count=generated_code.count("class ")
            )
            
        except Exception as e:
            self.logger.error(f"Day_07 agent review failed: {e}")
            raise
    
    async def _review_with_fallback(
        self,
        generated_code: str,
        task_description: str,
        model_name: str
    ) -> CodeQualityMetrics:
        """Fallback code review using direct model client."""
        try:
            # Create a simple prompt for code review
            prompt = f"""Review the following Python code for quality:

Task: {task_description}

Code:
{generated_code}

Please evaluate:
1. PEP8 compliance
2. Documentation (docstrings)
3. Type hints
4. Code complexity
5. Overall quality (0-10 scale)

Provide a brief assessment."""
            
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=prompt,
                max_tokens=500,
                temperature=0.2
            )
            
            # Parse response for basic metrics
            response_text = response.response.lower()
            
            pep8_compliance = "pep8" in response_text and "compliant" in response_text
            has_docstrings = '"""' in generated_code or "'''" in generated_code
            has_type_hints = ": " in generated_code or " -> " in generated_code
            
            # Extract quality score
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)', response_text)
            quality_score = float(score_match.group(1)) if score_match else 5.0
            
            return CodeQualityMetrics(
                code_quality_score=min(10.0, max(0.0, quality_score)),
                pep8_compliance=pep8_compliance,
                pep8_score=8.0 if pep8_compliance else 5.0,
                has_docstrings=has_docstrings,
                has_type_hints=has_type_hints,
                test_coverage="unknown",
                complexity_score=5.0,
                requirements_coverage=0.7,
                completeness_score=0.7,
                code_length=len(generated_code),
                function_count=generated_code.count("def "),
                class_count=generated_code.count("class ")
            )
            
        except Exception as e:
            self.logger.error(f"Fallback review failed: {e}")
            raise
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics from the underlying reviewer agent."""
        if self.reviewer_agent:
            return {
                "agent_type": "CodeReviewerAgent",
                "model_name": self.reviewer_agent.model_name,
                "total_requests": self.reviewer_agent.stats["total_requests"],
                "successful_requests": self.reviewer_agent.stats["successful_requests"],
                "failed_requests": self.reviewer_agent.stats["failed_requests"],
                "total_tokens_used": self.reviewer_agent.stats["total_tokens_used"],
                "average_response_time": self.reviewer_agent.get_average_response_time(),
                "uptime": self.reviewer_agent.get_uptime()
            }
        else:
            return {
                "agent_type": "FallbackReviewer",
                "status": "day_07 agent not available"
            }
