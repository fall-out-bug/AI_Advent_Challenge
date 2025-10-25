"""
Code review agent.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import logging
import re
from typing import Optional

from .base_agent import BaseAgent
from ..clients.unified_client import UnifiedModelClient
from .schemas import AgentRequest, AgentResponse, QualityMetrics


logger = logging.getLogger(__name__)


class CodeReviewerAgent(BaseAgent):
    """
    Code review agent for analyzing code quality.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This agent reviews code for quality, correctness,
    and adherence to best practices.
    """
    
    def __init__(
        self, 
        client: UnifiedModelClient,
        model_name: str = "gpt-4",
        max_tokens: int = 1500,
        temperature: float = 0.3
    ):
        """
        Initialize code reviewer agent.
        
        Args:
            client: UnifiedModelClient instance
            model_name: Model to use for review
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        """
        super().__init__(client, "code_reviewer")
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def _process_impl(self, request: AgentRequest) -> AgentResponse:
        """
        Review code and provide quality analysis.
        
        Args:
            request: Agent request with code to review
            
        Returns:
            AgentResponse: Review results with quality metrics
            
        Raises:
            Exception: If review fails
        """
        code = request.task
        prompt = self._build_prompt(code)
        
        model_response = await self._call_model(
            prompt=prompt,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        review_text = model_response.response
        quality_metrics = self._analyze_quality(code, review_text)
        
        metadata = self._create_metadata(
            task_type="code_review",
            model_name=self.model_name
        )
        
        return AgentResponse(
            result=review_text,
            success=True,
            error=None,
            metadata=metadata,
            quality=quality_metrics
        )
    
    def _build_prompt(self, code: str) -> str:
        """
        Build prompt for code review.
        
        Args:
            code: Code to review
            
        Returns:
            str: Formatted prompt
        """
        prompt = f"""Review the following code for quality, correctness, and best practices:
        
```python
{code}
```

Provide a comprehensive review covering:
1. Code quality and readability
2. Correctness and potential bugs
3. Performance and efficiency
4. Maintainability and style
5. Suggestions for improvement

Be specific and constructive in your feedback:"""
        
        return prompt
    
    def _analyze_quality(self, code: str, review_text: str) -> QualityMetrics:
        """
        Analyze code quality and create metrics.
        
        Args:
            code: Code being reviewed
            review_text: Review text from model
            
        Returns:
            QualityMetrics: Quality metrics
        """
        # Count issues found
        issues_found = self._count_issues(review_text)
        
        # Calculate basic quality scores
        readability = self._assess_readability(code)
        efficiency = self._assess_efficiency(code)
        correctness = self._assess_correctness(code)
        maintainability = self._assess_maintainability(code)
        
        # Overall score (weighted average)
        overall_score = (
            readability * 0.3 +
            efficiency * 0.2 +
            correctness * 0.3 +
            maintainability * 0.2
        )
        
        return QualityMetrics(
            score=overall_score,
            readability=readability,
            efficiency=efficiency,
            correctness=correctness,
            maintainability=maintainability,
            issues_found=issues_found
        )
    
    def _count_issues(self, review_text: str) -> int:
        """
        Count issues mentioned in review.
        
        Args:
            review_text: Review text
            
        Returns:
            int: Number of issues
        """
        issue_keywords = [
            "issue", "problem", "error", "bug", "warning",
            "concern", "improvement", "suggestion", "should"
        ]
        
        count = 0
        for keyword in issue_keywords:
            count += review_text.lower().count(keyword)
        
        return min(count, 20)  # Cap at 20 for reasonable scores
    
    def _assess_readability(self, code: str) -> float:
        """
        Assess code readability.
        
        Args:
            code: Code to assess
            
        Returns:
            float: Readability score (0-1)
        """
        lines = code.split("\n")
        if not lines:
            return 0.5
        
        score = 1.0
        
        # Check for long lines (should be <= 100 chars)
        for line in lines:
            if len(line) > 100:
                score -= 0.05
        
        # Check for long functions (approximate)
        if lines.count("def ") > 0:
            function_density = len(lines) / max(lines.count("def "), 1)
            if function_density > 50:  # Very long functions
                score -= 0.2
        
        # Check for comments
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        comment_ratio = comment_lines / len(lines) if lines else 0
        if comment_ratio < 0.1:  # Too few comments
            score -= 0.1
        elif comment_ratio > 0.3:  # Too many comments
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def _assess_efficiency(self, code: str) -> float:
        """
        Assess code efficiency.
        
        Args:
            code: Code to assess
            
        Returns:
            float: Efficiency score (0-1)
        """
        score = 1.0
        code_lower = code.lower()
        
        # Check for inefficient patterns
        inefficient_patterns = [
            ("for i in range(len(", 0.1),
            (".append(", 0.05),
            ("import *", 0.1),
        ]
        
        for pattern, penalty in inefficient_patterns:
            if pattern in code_lower:
                score -= penalty
        
        # Check for efficient patterns
        efficient_patterns = [
            "list comprehension",
            "generator",
            "f-string",
            "enumerate",
        ]
        
        for pattern in efficient_patterns:
            if pattern in code_lower:
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _assess_correctness(self, code: str) -> float:
        """
        Assess code correctness (basic checks).
        
        Args:
            code: Code to assess
            
        Returns:
            float: Correctness score (0-1)
        """
        score = 1.0
        
        # Check for common mistakes
        error_patterns = [
            ("= ", 0.01),  # Assignment vs comparison
            ("return None", 0.05),
        ]
        
        # Check for proper structure
        open_parens = code.count("(")
        close_parens = code.count(")")
        open_braces = code.count("[")
        close_braces = code.count("]")
        
        if abs(open_parens - close_parens) > 2:
            score -= 0.2
        if abs(open_braces - close_braces) > 2:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _assess_maintainability(self, code: str) -> float:
        """
        Assess code maintainability.
        
        Args:
            code: Code to assess
            
        Returns:
            float: Maintainability score (0-1)
        """
        score = 1.0
        lines = code.split("\n")
        
        # Check for magic numbers
        magic_numbers = re.findall(r'\b\d{2,}\b', code)
        if len(magic_numbers) > 5:
            score -= 0.2
        
        # Check for hardcoded strings (basic check)
        if code.count('"') > 20:
            score -= 0.1
        
        # Check for descriptive names
        if len([line for line in lines if "def " in line and len(line.split("def ")[1].split("(")[0]) < 3]) > 0:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def set_model(self, model_name: str) -> None:
        """
        Set model for code review.
        
        Args:
            model_name: Model name
        """
        self.model_name = model_name
        logger.info(f"CodeReviewerAgent model set to: {model_name}")
    
    def set_parameters(
        self, 
        max_tokens: Optional[int] = None, 
        temperature: Optional[float] = None
    ) -> None:
        """
        Set review parameters.
        
        Args:
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        """
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
        logger.info(f"CodeReviewerAgent parameters updated: max_tokens={self.max_tokens}, temperature={self.temperature}")
