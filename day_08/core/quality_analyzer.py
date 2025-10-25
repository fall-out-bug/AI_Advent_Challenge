"""
Quality Analyzer for performance and code quality evaluation.

This module provides the QualityAnalyzer class that measures response quality
and performance metrics using adapted day_07 reviewer agent patterns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from core.ml_client import TokenAnalysisClient
from core.token_analyzer import SimpleTokenCounter
from models.data_models import (
    ExperimentResult, 
    CompressionTestResult, 
    PerformanceMetrics, 
    CodeQualityMetrics,
    CompletenessScore
)
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class QualityAnalyzer:
    """
    Analyzer for performance and code quality evaluation.
    
    Provides comprehensive quality analysis including performance metrics,
    code quality evaluation, and completeness assessment.
    
    Attributes:
        model_client: TokenAnalysisClient for model interactions
        token_counter: TokenCounter for token counting
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from core.quality_analyzer import QualityAnalyzer
        from core.ml_client import TokenAnalysisClient
        from core.token_analyzer import SimpleTokenCounter
        
        # Initialize analyzer
        model_client = TokenAnalysisClient()
        token_counter = SimpleTokenCounter()
        
        analyzer = QualityAnalyzer(model_client, token_counter)
        
        # Analyze performance
        perf_metrics = await analyzer.analyze_performance(experiment_result)
        
        # Analyze code quality
        quality_metrics = await analyzer.analyze_code_quality(code, requirements)
        
        # Analyze completeness
        completeness = await analyzer.analyze_completeness(response, original_query)
        ```
    """
    
    def __init__(
        self,
        model_client: Optional[TokenAnalysisClient] = None,
        token_counter: Optional[SimpleTokenCounter] = None
    ):
        """
        Initialize the quality analyzer.
        
        Args:
            model_client: Optional TokenAnalysisClient instance
            token_counter: Optional TokenCounter instance
            
        Example:
            ```python
            from core.quality_analyzer import QualityAnalyzer
            
            # Initialize with default components
            analyzer = QualityAnalyzer()
            
            # Or with custom components
            analyzer = QualityAnalyzer(
                model_client=custom_client,
                token_counter=custom_counter
            )
            ```
        """
        self.model_client = model_client or TokenAnalysisClient()
        self.token_counter = token_counter or SimpleTokenCounter()
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Quality thresholds
        self.quality_thresholds = {
            "high_quality": 0.8,
            "acceptable_quality": 0.6,
            "poor_quality": 0.4,
            "fast_response": 2.0,  # seconds
            "slow_response": 10.0,  # seconds
            "good_compression_ratio": 0.3,
            "poor_compression_ratio": 0.7
        }
        
        self.logger.info("Initialized QualityAnalyzer")
    
    async def analyze_performance(self, result: ExperimentResult) -> PerformanceMetrics:
        """
        Analyze performance metrics from experiment result.
        
        Args:
            result: ExperimentResult to analyze
            
        Returns:
            PerformanceMetrics containing performance analysis
            
        Example:
            ```python
            # Analyze performance of an experiment
            perf_metrics = await analyzer.analyze_performance(experiment_result)
            
            print(f"Response time: {perf_metrics.response_time:.2f}s")
            print(f"Tokens per second: {perf_metrics.tokens_per_second:.2f}")
            print(f"Performance rating: {perf_metrics.performance_rating}")
            ```
        """
        try:
            self.logger.info("Analyzing performance metrics...")
            
            # Calculate tokens per second
            tokens_per_second = result.total_tokens / result.response_time if result.response_time > 0 else 0
            
            # Determine performance rating
            performance_rating = self._calculate_performance_rating(
                result.response_time, tokens_per_second, result.total_tokens
            )
            
            # Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(result)
            
            # Determine if compression was beneficial
            compression_beneficial = self._evaluate_compression_benefit(result)
            
            return PerformanceMetrics(
                response_time=result.response_time,
                total_tokens=result.total_tokens,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                tokens_per_second=tokens_per_second,
                performance_rating=performance_rating,
                efficiency_score=efficiency_score,
                compression_beneficial=compression_beneficial,
                compression_ratio=result.compression_ratio if result.compression_result else 1.0,
                success=result.success
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {e}")
            
            # Return default metrics on error
            return PerformanceMetrics(
                response_time=0.0,
                total_tokens=0,
                input_tokens=0,
                output_tokens=0,
                tokens_per_second=0.0,
                performance_rating="unknown",
                efficiency_score=0.0,
                compression_beneficial=False,
                compression_ratio=1.0,
                success=False
            )
    
    async def analyze_code_quality(
        self, 
        code: str, 
        requirements: str,
        model_name: str = "starcoder"
    ) -> CodeQualityMetrics:
        """
        Analyze code quality using adapted reviewer patterns.
        
        Args:
            code: Generated code to analyze
            requirements: Original requirements
            model_name: Name of the model used
            
        Returns:
            CodeQualityMetrics containing quality analysis
            
        Example:
            ```python
            # Analyze code quality
            quality_metrics = await analyzer.analyze_code_quality(
                generated_code, 
                original_requirements,
                "starcoder"
            )
            
            print(f"Code quality score: {quality_metrics.code_quality_score:.2f}")
            print(f"PEP8 compliance: {quality_metrics.pep8_compliance}")
            print(f"Has docstrings: {quality_metrics.has_docstrings}")
            ```
        """
        try:
            self.logger.info("Analyzing code quality...")
            
            # Basic code analysis
            has_docstrings = self._check_docstrings(code)
            has_type_hints = self._check_type_hints(code)
            pep8_compliance = self._check_pep8_compliance(code)
            complexity_score = self._calculate_complexity_score(code)
            
            # Requirements coverage
            requirements_coverage = self._calculate_requirements_coverage(code, requirements)
            
            # Code completeness
            completeness_score = self._calculate_code_completeness(code, requirements)
            
            # Overall code quality score
            code_quality_score = self._calculate_overall_quality_score(
                pep8_compliance, has_docstrings, has_type_hints, 
                complexity_score, requirements_coverage, completeness_score
            )
            
            # Test coverage estimation
            test_coverage = self._estimate_test_coverage(code)
            
            return CodeQualityMetrics(
                code_quality_score=code_quality_score,
                pep8_compliance=pep8_compliance,
                pep8_score=8.0 if pep8_compliance else 5.0,
                has_docstrings=has_docstrings,
                has_type_hints=has_type_hints,
                test_coverage=test_coverage,
                complexity_score=complexity_score,
                requirements_coverage=requirements_coverage,
                completeness_score=completeness_score,
                code_length=len(code),
                function_count=self._count_functions(code),
                class_count=self._count_classes(code)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze code quality: {e}")
            
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
                code_length=len(code),
                function_count=0,
                class_count=0
            )
    
    async def analyze_completeness(
        self, 
        response: str, 
        original_query: str
    ) -> CompletenessScore:
        """
        Analyze completeness of response relative to original query.
        
        Args:
            response: Model response text
            original_query: Original query text
            
        Returns:
            CompletenessScore containing completeness analysis
            
        Example:
            ```python
            # Analyze response completeness
            completeness = await analyzer.analyze_completeness(
                model_response, 
                original_query
            )
            
            print(f"Completeness score: {completeness.completeness_score:.2f}")
            print(f"Requirements met: {completeness.requirements_met}")
            print(f"Missing elements: {completeness.missing_elements}")
            ```
        """
        try:
            self.logger.info("Analyzing response completeness...")
            
            # Extract requirements from original query
            requirements = self._extract_requirements(original_query)
            
            # Check which requirements are met
            requirements_met = self._check_requirements_met(response, requirements)
            
            # Calculate completeness score
            completeness_score = len(requirements_met) / len(requirements) if requirements else 0.5
            
            # Identify missing elements
            missing_elements = [req for req in requirements if req not in requirements_met]
            
            # Check for code presence
            has_code = self._check_code_presence(response)
            
            # Check for examples
            has_examples = self._check_examples_presence(response)
            
            # Check for documentation
            has_documentation = self._check_documentation_presence(response)
            
            return CompletenessScore(
                completeness_score=completeness_score,
                requirements_met=requirements_met,
                missing_elements=missing_elements,
                has_code=has_code,
                has_examples=has_examples,
                has_documentation=has_documentation,
                response_length=len(response),
                query_length=len(original_query),
                coverage_ratio=len(response) / len(original_query) if original_query else 0
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze completeness: {e}")
            
            # Return default score on error
            return CompletenessScore(
                completeness_score=0.5,
                requirements_met=[],
                missing_elements=[],
                has_code=False,
                has_examples=False,
                has_documentation=False,
                response_length=len(response),
                query_length=len(original_query),
                coverage_ratio=0.0
            )
    
    def _calculate_performance_rating(
        self, 
        response_time: float, 
        tokens_per_second: float, 
        total_tokens: int
    ) -> str:
        """Calculate performance rating based on metrics."""
        if response_time <= self.quality_thresholds["fast_response"] and tokens_per_second > 50:
            return "excellent"
        elif response_time <= self.quality_thresholds["slow_response"] and tokens_per_second > 20:
            return "good"
        elif response_time <= self.quality_thresholds["slow_response"]:
            return "acceptable"
        else:
            return "poor"
    
    def _calculate_efficiency_score(self, result: ExperimentResult) -> float:
        """Calculate efficiency score based on compression and performance."""
        # Base efficiency on compression ratio and response time
        compression_efficiency = 1.0 - result.compression_ratio if result.compression_result else 1.0
        time_efficiency = 1.0 / (result.response_time + 0.1)  # Faster is better
        
        # Combine metrics
        return (compression_efficiency * 0.6 + time_efficiency * 0.4)
    
    def _evaluate_compression_benefit(self, result: ExperimentResult) -> bool:
        """Evaluate if compression was beneficial."""
        if not result.compression_result:
            return True  # No compression needed
        
        # Compression is beneficial if ratio is good and response is successful
        return (result.compression_result.compression_ratio < 
                self.quality_thresholds["good_compression_ratio"] and 
                result.success)
    
    def _check_docstrings(self, code: str) -> bool:
        """Check if code has docstrings."""
        return '"""' in code or "'''" in code
    
    def _check_type_hints(self, code: str) -> bool:
        """Check if code has type hints."""
        return ": " in code or " -> " in code
    
    def _check_pep8_compliance(self, code: str) -> bool:
        """Basic PEP8 compliance check."""
        lines = code.split('\n')
        
        # Check for common PEP8 violations
        for line in lines:
            # Check line length (simplified)
            if len(line) > 120:
                return False
            # Check for mixed tabs and spaces
            if '\t' in line and '    ' in line:
                return False
        
        return True
    
    def _calculate_complexity_score(self, code: str) -> float:
        """Calculate complexity score (0-10, lower is better)."""
        score = 0.0
        
        # Check nesting depth
        max_indent = 0
        for line in code.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        if max_indent > 12:  # 3+ levels
            score += 3.0
        elif max_indent > 8:  # 2+ levels
            score += 1.5
        
        # Check for complex constructs
        complex_patterns = ["for.*if", "try.*except.*finally", "lambda.*lambda"]
        for pattern in complex_patterns:
            if pattern in code:
                score += 1.0
        
        # Check function/class count
        function_count = code.count("def ")
        class_count = code.count("class ")
        
        if function_count > 10:
            score += 2.0
        elif function_count > 5:
            score += 1.0
        
        if class_count > 5:
            score += 1.0
        
        return min(10.0, score)
    
    def _calculate_requirements_coverage(self, code: str, requirements: str) -> float:
        """Calculate how well code covers requirements."""
        # Extract key terms from requirements
        req_terms = set(requirements.lower().split())
        code_terms = set(code.lower().split())
        
        # Calculate overlap
        if not req_terms:
            return 0.5
        
        overlap = len(req_terms.intersection(code_terms))
        return overlap / len(req_terms)
    
    def _calculate_code_completeness(self, code: str, requirements: str) -> float:
        """Calculate code completeness score."""
        # Check for essential Python elements
        essential_elements = ["def ", "import ", "return "]
        present_elements = sum(1 for elem in essential_elements if elem in code)
        
        # Check for requirements keywords
        req_keywords = ["function", "class", "method", "return", "import"]
        req_present = sum(1 for keyword in req_keywords if keyword in requirements.lower())
        
        if req_present == 0:
            return 0.5
        
        return present_elements / len(essential_elements)
    
    def _calculate_overall_quality_score(
        self, 
        pep8_compliance: bool, 
        has_docstrings: bool, 
        has_type_hints: bool,
        complexity_score: float, 
        requirements_coverage: float, 
        completeness_score: float
    ) -> float:
        """Calculate overall code quality score."""
        # Convert boolean to numeric
        pep8_score = 8.0 if pep8_compliance else 5.0
        docstring_score = 8.0 if has_docstrings else 5.0
        type_hint_score = 8.0 if has_type_hints else 5.0
        
        # Normalize complexity (lower is better)
        complexity_normalized = max(0, 10 - complexity_score)
        
        # Weighted average
        weights = [0.2, 0.15, 0.15, 0.2, 0.15, 0.15]
        scores = [pep8_score, docstring_score, type_hint_score, 
                 complexity_normalized, requirements_coverage * 10, completeness_score * 10]
        
        return sum(w * s for w, s in zip(weights, scores)) / 10
    
    def _estimate_test_coverage(self, code: str) -> str:
        """Estimate test coverage based on code analysis."""
        if "test" in code.lower() or "pytest" in code.lower():
            return "good"
        elif "def test_" in code:
            return "basic"
        else:
            return "none"
    
    def _count_functions(self, code: str) -> int:
        """Count number of functions in code."""
        return code.count("def ")
    
    def _count_classes(self, code: str) -> int:
        """Count number of classes in code."""
        return code.count("class ")
    
    def _extract_requirements(self, query: str) -> List[str]:
        """Extract requirements from query text."""
        # Simple keyword extraction
        keywords = ["function", "class", "method", "implement", "create", "write", "build"]
        requirements = []
        
        for keyword in keywords:
            if keyword in query.lower():
                requirements.append(keyword)
        
        return requirements
    
    def _check_requirements_met(self, response: str, requirements: List[str]) -> List[str]:
        """Check which requirements are met in response."""
        met = []
        response_lower = response.lower()
        
        for req in requirements:
            if req in response_lower:
                met.append(req)
        
        return met
    
    def _check_code_presence(self, response: str) -> bool:
        """Check if response contains code."""
        return "```" in response or "def " in response or "class " in response
    
    def _check_examples_presence(self, response: str) -> bool:
        """Check if response contains examples."""
        return "example" in response.lower() or "usage" in response.lower()
    
    def _check_documentation_presence(self, response: str) -> bool:
        """Check if response contains documentation."""
        return "docstring" in response.lower() or '"""' in response
    
    def get_quality_thresholds(self) -> Dict[str, Any]:
        """Get current quality thresholds."""
        return self.quality_thresholds.copy()
    
    def update_quality_thresholds(self, new_thresholds: Dict[str, Any]) -> None:
        """Update quality thresholds."""
        self.quality_thresholds.update(new_thresholds)
        self.logger.info(f"Updated quality thresholds: {new_thresholds}")
