"""Code reviewer agent implementation."""

import logging
import re
from datetime import datetime
from typing import List, Optional

from agents.core.base_agent import BaseAgent
from communication.message_schema import (
    CodeQualityMetrics,
    CodeReviewRequest,
    CodeReviewResponse,
)
from prompts.reviewer_prompts import ReviewerPrompts

# Configure logging
logger = logging.getLogger(__name__)


class CodeReviewerAgent(BaseAgent):
    """Agent responsible for reviewing and analyzing Python code."""

    def __init__(
        self,
        model_name: str = "starcoder",
        max_tokens: int = 1200,
        temperature: float = 0.2,
        external_provider: Optional[str] = None,
    ):
        """Initialize the code reviewer agent.

        Args:
            model_name: Name of the model to use (starcoder, mistral, qwen, tinyllama)
            max_tokens: Maximum tokens for analysis
            temperature: Temperature for analysis (lower for more consistent reviews)
            external_provider: External API provider name (if using external API)
        """
        super().__init__(
            model_name=model_name,
            agent_type="reviewer",
            max_tokens=max_tokens,
            temperature=temperature,
            external_provider=external_provider,
        )
        self.prompts = ReviewerPrompts()

    async def process(self, request: CodeReviewRequest) -> CodeReviewResponse:
        """Process a code review request.

        Args:
            request: Code review request

        Returns:
            Code review response

        Raises:
            Exception: If model request fails
            ValueError: If response parsing fails
        """
        try:
            logger.info(
                f"Processing code review request for: {request.task_description}"
            )

            # Prepare prompt and call model
            prompt = self._prepare_review_prompt(request)
            response = await self._call_model_for_review(prompt)

            # Parse and validate response
            review_data = self._parse_review_response(response)
            metrics = self._create_quality_metrics(review_data)

            return CodeReviewResponse(
                code_quality_score=float(review_data.get("overall_score", 5.0)),
                metrics=metrics,
                issues=review_data.get("issues", []),
                recommendations=review_data.get("recommendations", []),
                review_time=datetime.now(),
                tokens_used=response.get("total_tokens", 0),
            )

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Code review failed: {str(e)}")
            raise e

    def _prepare_review_prompt(self, request: CodeReviewRequest) -> str:
        """Prepare the review prompt.

        Args:
            request: Code review request

        Returns:
            Formatted prompt string
        """
        return self.prompts.get_code_review_prompt(
            task_description=request.task_description,
            generated_code=request.generated_code,
            tests=request.tests,
            metadata=request.metadata.model_dump(),
        )

    async def _call_model_for_review(self, prompt: str) -> dict:
        """Call the model for code review.

        Args:
            prompt: Input prompt

        Returns:
            Model response

        Raises:
            Exception: If model call fails
        """
        return await self._call_model(prompt=prompt, max_tokens=self.max_tokens)

    def _parse_review_response(self, response: dict) -> dict:
        """Parse the review response from the model.

        Args:
            response: Model response

        Returns:
            Parsed review data

        Raises:
            ValueError: If parsing fails
        """
        response_text = response.get("response", "")

        # Try to parse JSON response
        try:
            return self._parse_json_response(response_text)
        except ValueError:
            logger.warning("JSON parsing failed, falling back to text parsing")
            return self._parse_text_response(response_text)

    def _create_quality_metrics(self, review_data: dict) -> CodeQualityMetrics:
        """Create quality metrics from review data.

        Args:
            review_data: Parsed review data

        Returns:
            Code quality metrics
        """
        metrics_data = review_data.get("metrics", {})

        return CodeQualityMetrics(
            pep8_compliance=metrics_data.get("pep8_compliance", False),
            pep8_score=float(metrics_data.get("pep8_score", 5.0)),
            has_docstrings=metrics_data.get("has_docstrings", False),
            has_type_hints=metrics_data.get("has_type_hints", False),
            test_coverage=metrics_data.get("test_coverage", "unknown"),
            complexity_score=float(metrics_data.get("complexity_score", 5.0)),
        )

    def _parse_text_response(self, response_text: str) -> dict:
        """Parse text response when JSON parsing fails.

        Args:
            response_text: Raw response text

        Returns:
            Parsed review data
        """
        # Extract overall score
        score_match = re.search(
            r"overall_score[:\s]*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE
        )
        overall_score = float(score_match.group(1)) if score_match else 5.0

        # Extract PEP8 compliance
        pep8_match = re.search(
            r"pep8_compliance[:\s]*(true|false)", response_text, re.IGNORECASE
        )
        pep8_compliance = pep8_match.group(1).lower() == "true" if pep8_match else False

        # Extract PEP8 score
        pep8_score_match = re.search(
            r"pep8_score[:\s]*(\d+(?:\.\d+)?)", response_text, re.IGNORECASE
        )
        pep8_score = float(pep8_score_match.group(1)) if pep8_score_match else 5.0

        # Extract docstrings
        docstrings_match = re.search(
            r"has_docstrings[:\s]*(true|false)", response_text, re.IGNORECASE
        )
        has_docstrings = (
            docstrings_match.group(1).lower() == "true" if docstrings_match else False
        )

        # Extract type hints
        type_hints_match = re.search(
            r"has_type_hints[:\s]*(true|false)", response_text, re.IGNORECASE
        )
        has_type_hints = (
            type_hints_match.group(1).lower() == "true" if type_hints_match else False
        )

        # Extract issues and recommendations
        issues = self._extract_list_items(response_text, "issues")
        recommendations = self._extract_list_items(response_text, "recommendations")

        return {
            "overall_score": overall_score,
            "metrics": {
                "pep8_compliance": pep8_compliance,
                "pep8_score": pep8_score,
                "has_docstrings": has_docstrings,
                "has_type_hints": has_type_hints,
                "test_coverage": "unknown",
                "complexity_score": 5.0,
            },
            "issues": issues,
            "recommendations": recommendations,
        }

    def _extract_list_items(self, text: str, section_name: str) -> List[str]:
        """Extract list items from a specific section.

        Args:
            text: Text to search
            section_name: Name of the section

        Returns:
            List of items
        """
        items = []

        # Look for section with bullet points
        section_pattern = rf"{section_name}[:\s]*\n((?:[-*]\s*.*\n?)*)"
        section_match = re.search(section_pattern, text, re.IGNORECASE | re.MULTILINE)

        if section_match:
            section_text = section_match.group(1)
            item_pattern = r"[-*]\s*(.+?)(?=\n[-*]|\n\n|\Z)"
            matches = re.findall(item_pattern, section_text, re.DOTALL)
            items = [match.strip() for match in matches if match.strip()]

        return items

    async def analyze_pep8_compliance(self, code: str) -> dict:
        """Analyze PEP8 compliance of code.

        Args:
            code: Code to analyze

        Returns:
            PEP8 analysis results
        """
        try:
            prompt = self.prompts.get_pep8_analysis_prompt(code)

            response = await self._call_model(prompt=prompt, max_tokens=500)

            response_text = response.get("response", "")

            # Parse PEP8 analysis
            compliance_match = re.search(r"PEP8 COMPLIANCE[:\s]*(\w+)", response_text)
            compliance = (
                compliance_match.group(1).lower() == "compliant"
                if compliance_match
                else False
            )

            score_match = re.search(r"SCORE[:\s]*(\d+(?:\.\d+)?)", response_text)
            score = float(score_match.group(1)) if score_match else 5.0

            violations = self._extract_list_items(response_text, "VIOLATIONS")
            recommendations = self._extract_list_items(response_text, "RECOMMENDATIONS")

            return {
                "compliant": compliance,
                "score": score,
                "violations": violations,
                "recommendations": recommendations,
            }

        except Exception:
            return {
                "compliant": False,
                "score": 5.0,
                "violations": ["Unable to analyze PEP8 compliance"],
                "recommendations": ["Run flake8 or black for detailed analysis"],
            }

    async def analyze_test_coverage(self, function_code: str, test_code: str) -> dict:
        """Analyze test coverage.

        Args:
            function_code: Function being tested
            test_code: Test code

        Returns:
            Test coverage analysis
        """
        try:
            prompt = self.prompts.get_test_coverage_prompt(
                function_code=function_code, test_code=test_code
            )

            response = await self._call_model(prompt=prompt, max_tokens=500)

            response_text = response.get("response", "")

            # Parse test coverage analysis
            coverage_match = re.search(r"COVERAGE ASSESSMENT[:\s]*(\w+)", response_text)
            coverage = coverage_match.group(1).lower() if coverage_match else "unknown"

            covered_scenarios = self._extract_list_items(
                response_text, "COVERED SCENARIOS"
            )
            missing_scenarios = self._extract_list_items(
                response_text, "MISSING SCENARIOS"
            )
            recommendations = self._extract_list_items(response_text, "RECOMMENDATIONS")

            return {
                "coverage": coverage,
                "covered_scenarios": covered_scenarios,
                "missing_scenarios": missing_scenarios,
                "recommendations": recommendations,
            }

        except Exception:
            return {
                "coverage": "unknown",
                "covered_scenarios": [],
                "missing_scenarios": ["Unable to analyze test coverage"],
                "recommendations": ["Add more comprehensive tests"],
            }

    def calculate_complexity_score(self, code: str) -> float:
        """Calculate basic complexity score for code.

        Args:
            code: Code to analyze

        Returns:
            Complexity score (0-10, lower is better)
        """
        score = 0.0  # Start from 0, add complexity points

        # Check function length
        lines = code.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        if len(non_empty_lines) > 20:
            score += 2.0
        elif len(non_empty_lines) > 10:
            score += 1.0

        # Check nesting depth
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent > 12:  # 3+ levels of nesting
            score += 2.0
        elif max_indent > 8:  # 2+ levels of nesting
            score += 1.0

        # Check for complex constructs
        if "for" in code and "if" in code:
            score += 2.0
        if "try" in code and "except" in code:
            score += 2.0
        if "lambda" in code:
            score += 1.0
        if "while" in code:
            score += 1.0
        if "if" in code and "else" in code:
            score += 1.0

        # Check for good practices (reduce complexity)
        if "def " in code and ": " in code:  # Type hints
            score -= 1.0
        if '"""' in code or "'''" in code:  # Docstrings
            score -= 1.0
        if "import" in code:  # Proper imports
            score -= 0.5

        return max(0.0, min(10.0, score))
