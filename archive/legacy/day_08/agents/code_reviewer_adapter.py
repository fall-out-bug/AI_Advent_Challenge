"""
Code Reviewer Adapter for integrating SDK CodeReviewerAgent.

This module provides the CodeReviewerAdapter class that wraps the SDK
CodeReviewerAgent and integrates it with day_08's quality analysis
and metrics collection.
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add shared SDK to path for importing agents
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.agents.code_reviewer import CodeReviewerAgent
from shared_package.agents.schemas import (
    AgentRequest,
    AgentResponse,
    TaskMetadata
)
from shared_package.orchestration.adapters import DirectAdapter

from core.ml_client import TokenAnalysisClient
from core.token_analyzer import SimpleTokenCounter
from models.data_models import CodeQualityMetrics
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class CodeReviewerAdapter:
    """
    Adapter for SDK CodeReviewerAgent with day_08 integration.
    
    Wraps the SDK CodeReviewerAgent and integrates it with day_08's
    quality analysis and metrics collection.
    
    Attributes:
        reviewer_agent: SDK CodeReviewerAgent instance
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
        
        # Initialize SDK reviewer agent
        try:
            # Create UnifiedModelClient for SDK agent
            from shared_package.clients.unified_client import UnifiedModelClient
            client = UnifiedModelClient()
            
            # Initialize SDK agent with client
            self.reviewer_agent = CodeReviewerAgent(
                client=client,
                model_name=model_name,
                max_tokens=1500,
                temperature=0.2
            )
            self.logger.info(f"Initialized SDK CodeReviewerAgent with {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SDK CodeReviewerAgent: {e}")
            raise
        
        self.logger.info("Initialized CodeReviewerAdapter")
    
    async def review_code_quality(
        self,
        generated_code: str,
        task_description: str,
        model_name: str,
        tests: Optional[str] = None
    ) -> CodeQualityMetrics:
        """
        Review code quality using SDK CodeReviewerAgent.
        
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
            
            # Set the correct model for the SDK agent
            self.reviewer_agent.set_model(model_name)
            
            # Use SDK agent for code review
            quality_metrics = await self._review_with_sdk_agent(
                generated_code, task_description, tests, model_name
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
    
    async def _review_with_sdk_agent(
        self,
        generated_code: str,
        task_description: str,
        tests: Optional[str],
        model_name: str
    ) -> CodeQualityMetrics:
        """Review code using SDK CodeReviewerAgent."""
        try:
            # Create request for SDK agent
            request = AgentRequest(
                task=f"Review code quality for: {task_description}",
                context={
                    "generated_code": generated_code,
                    "tests": tests or "",
                    "model_name": model_name
                },
                metadata=TaskMetadata(
                    task_id=f"rev_{hash(generated_code)}",
                    task_type="code_review",
                    timestamp=asyncio.get_event_loop().time(),
                    model_name=model_name
                )
            )
            
            # Review code using SDK agent
            response = await self.reviewer_agent.process(request)
            
            # Convert to CodeQualityMetrics
            return CodeQualityMetrics(
                code_quality_score=response.quality.score if response.quality else 5.0,
                pep8_compliance=response.quality.readability > 0.7 if response.quality else False,
                pep8_score=response.quality.readability * 10 if response.quality else 5.0,
                has_docstrings=response.quality.maintainability > 0.7 if response.quality else False,
                has_type_hints=response.quality.correctness > 0.7 if response.quality else False,
                test_coverage="unknown",
                complexity_score=response.quality.efficiency * 10 if response.quality else 5.0,
                requirements_coverage=response.quality.score if response.quality else 0.5,
                completeness_score=response.quality.score if response.quality else 0.5,
                code_length=len(generated_code),
                function_count=generated_code.count("def "),
                class_count=generated_code.count("class ")
            )
            
        except Exception as e:
            self.logger.error(f"SDK agent review failed: {e}")
            raise
    
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics from the underlying reviewer agent."""
        stats = self.reviewer_agent.get_stats()
        return {
            "agent_type": "SDK_CodeReviewerAgent",
            "model_name": self.reviewer_agent.model_name,
            "total_requests": stats["total_requests"],
            "successful_requests": stats["successful_requests"],
            "failed_requests": stats["failed_requests"],
            "total_response_time": stats["total_response_time"],
            "average_response_time": stats["average_response_time"],
            "agent_name": stats["agent_name"]
        }
