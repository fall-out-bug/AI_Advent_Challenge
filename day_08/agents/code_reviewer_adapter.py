"""
Code Reviewer Adapter for integrating day_07 CodeReviewerAgent.

This module provides the CodeReviewerAdapter class that wraps the day_07
CodeReviewerAgent and integrates it with day_08's quality analysis
and metrics collection.
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add day_07 to path for importing agents
day_07_path = Path(__file__).parent.parent.parent / "day_07"
sys.path.insert(0, str(day_07_path))

try:
    from agents.core.code_reviewer import CodeReviewerAgent
    from communication.message_schema import (
        CodeReviewRequest,
        CodeReviewResponse,
        TaskMetadata
    )
except ImportError:
    # Fallback for when day_07 agents are not available
    CodeReviewerAgent = None
    CodeReviewRequest = None
    CodeReviewResponse = None
    TaskMetadata = None

from core.ml_client import TokenAnalysisClient
from core.token_analyzer import SimpleTokenCounter
from models.data_models import CodeQualityMetrics
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


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
