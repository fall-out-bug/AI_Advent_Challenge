"""Architecture review pass (Pass 1) for multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import re
import logging
from datetime import datetime
from typing import Any, Dict, List

from src.domain.agents.passes.base_pass import BaseReviewPass
from src.domain.models.code_review_models import (
    PassFindings,
    Finding,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class ArchitectureReviewPass(BaseReviewPass):
    """Architecture overview pass (Pass 1).

    Purpose:
        Performs high-level architectural analysis:
        - Detects component types (Docker, Airflow, Spark, MLflow)
        - Analyzes project structure and dependencies
        - Identifies architectural issues

    Example:
        pass_instance = ArchitectureReviewPass(unified_client, session_manager)
        findings = await pass_instance.run(code)
    """

    async def run(self, code: str) -> PassFindings:
        """Execute Pass 1: Architecture Review.

        Purpose:
            Performs architectural analysis and component detection.

        Args:
            code: Code to analyze

        Returns:
            PassFindings with architecture findings

        Raises:
            Exception: If analysis fails
        """
        self.logger.info("Starting Pass 1: Architecture Review")

        # Log pass start
        if self.review_logger:
            self.review_logger.log_review_pass(
                "pass_1",
                "started",
                {"code_length": len(code)},
            )

        # 1. Parse code structure
        detected_components = self._detect_components(code)
        self.logger.info(f"Detected components: {detected_components}")

        # 2. Build component summary
        component_summary = self._build_component_summary(code, detected_components)

        # 3. Load prompt template
        try:
            prompt_template = self._load_prompt_template("pass_1_architecture")
        except (ValueError, FileNotFoundError):
            # Fallback to generic prompt if not found
            prompt_template = self._build_fallback_prompt()

        # 4. Prepare prompt for Mistral
        code_snippet = code[:3000] if len(code) > 3000 else code
        prompt = prompt_template.format(
            code_snippet=code_snippet,
            component_summary=component_summary,
            detected_components=", ".join(detected_components)
        )

        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.5,  # Lower temperature for architecture analysis
            max_tokens=2000  # Increased for thorough analysis
        )

        # 6. Parse response
        parsed_findings = self._parse_response(response)

        # 7. Convert to Finding objects
        findings_list = self._convert_to_findings(parsed_findings.get("findings", {}))

        # 8. Create PassFindings
        pass_findings = PassFindings(
            pass_name="pass_1",
            timestamp=datetime.now(),
            findings=findings_list,
            recommendations=parsed_findings.get("recommendations", []),
            summary=parsed_findings.get("summary"),
            metadata={
                "detected_components": detected_components,
                "token_estimate": self._estimate_tokens(prompt),
            }
        )

        # 9. Save session state
        self.session.save_findings("pass_1", pass_findings.to_dict())

        # Log pass completion
        if self.review_logger:
            self.review_logger.log_review_pass(
                "pass_1",
                "completed",
                {
                    "findings_count": len(findings_list),
                    "detected_components": detected_components,
                },
            )

        self.logger.info(f"Pass 1 complete. Found {len(findings_list)} findings.")
        return pass_findings

    def _detect_components(self, code: str) -> List[str]:
        """Detect which component types are present.

        Purpose:
            Analyzes code to identify component types using multiple
            detection strategies for robustness.

        Args:
            code: Code to analyze (may contain file paths like "# File: ...")

        Returns:
            List of detected component types
        """
        components = []
        code_lower = code.lower()

        # Docker detection - multiple strategies
        docker_indicators = [
            "# file: dockerfile" in code_lower,
            "# file: docker-compose" in code_lower,
            "from dockerfile" in code_lower,
            "dockerfile" in code_lower and ("from" in code_lower or "run" in code_lower or "copy" in code_lower),
            "docker-compose" in code_lower,
            "services:" in code_lower and ("version:" in code_lower or "image:" in code_lower),
        ]
        if any(docker_indicators):
            components.append("docker")

        # Airflow detection - multiple strategies
        airflow_indicators = [
            "from airflow" in code_lower,
            "import airflow" in code_lower,
            "DAG(" in code,
            "@dag" in code,
            "@dag(" in code_lower,
            "airflow.operators" in code_lower,
            "airflow.models" in code_lower,
            "airflow.decorators" in code_lower,
            "# file:" in code_lower and "airflow" in code_lower and ("dag" in code_lower or "dags" in code_lower),
        ]
        if any(airflow_indicators):
            components.append("airflow")

        # Spark detection - multiple strategies
        spark_indicators = [
            "from pyspark" in code_lower,
            "import pyspark" in code_lower,
            "SparkSession" in code,
            "spark.createDataFrame" in code_lower,
            "spark.sql" in code_lower,
            "spark.read" in code_lower,
            "pyspark.sql" in code_lower,
        ]
        if any(spark_indicators):
            components.append("spark")

        # MLflow detection - multiple strategies
        mlflow_indicators = [
            "from mlflow" in code_lower,
            "import mlflow" in code_lower,
            "mlflow.start_run" in code_lower,
            "mlflow.log_metric" in code_lower,
            "mlflow.log_param" in code_lower,
            "mlflow.log_artifact" in code_lower,
            "mlflow.set_experiment" in code_lower,
            "mlflow.tracking" in code_lower,
            "# file:" in code_lower and "mlflow" in code_lower,
        ]
        if any(mlflow_indicators):
            components.append("mlflow")

        return components if components else ["generic"]

    def _build_component_summary(self, code: str, components: List[str]) -> str:
        """Build summary of detected components.

        Purpose:
            Creates human-readable summary of detected components.

        Args:
            code: Code being analyzed
            components: List of detected component types

        Returns:
            Summary string
        """
        summary_lines = []

        for comp in components:
            if comp == "docker":
                services = re.findall(r"^\s+(\w+):", code, re.MULTILINE)
                if services:
                    summary_lines.append(f"Docker services: {', '.join(services[:5])}")
                else:
                    summary_lines.append("Docker configuration detected")

            elif comp == "airflow":
                dags = re.findall(r"(?:@dag|DAG)\(dag_id=[\'\"](\w+)[\'\"]", code)
                if dags:
                    summary_lines.append(f"Airflow DAGs: {', '.join(dags[:5])}")
                else:
                    summary_lines.append("Airflow DAGs detected")

            elif comp == "spark":
                spark_ops = len(re.findall(r"(?:SparkSession|spark\.)", code))
                summary_lines.append(f"Spark operations: {spark_ops} detected")

            elif comp == "mlflow":
                mlflow_calls = len(re.findall(r"(?:mlflow|log_metric|log_param)", code))
                summary_lines.append(f"MLflow tracking: {mlflow_calls} calls detected")

            elif comp == "generic":
                summary_lines.append("Generic Python code detected")

        return "\n".join(summary_lines) if summary_lines else "No specific components detected"

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral response into structured findings.

        Purpose:
            Attempts to parse JSON response using improved extraction,
            falls back to text parsing if JSON not found.

        Args:
            response: Raw response from model

        Returns:
            Dictionary with findings structure
        """
        # Try to extract JSON using improved method from base class
        parsed_json = self._extract_json_from_response(response)
        if parsed_json:
            return parsed_json

        # Fallback: extract sections manually - support both English and Russian
        self.logger.warning("JSON parsing failed, using fallback text parsing")
        # Combine English and Russian section names
        critical_items = self._extract_section(response, ["CRITICAL", "КРИТИЧЕСКИЕ", "КРИТИЧНЫЕ"])
        major_items = self._extract_section(response, ["MAJOR", "ЗНАЧИТЕЛЬНЫЕ", "СЕРЬЁЗНЫЕ"])
        minor_items = self._extract_section(response, ["MINOR", "НЕЗНАЧИТЕЛЬНЫЕ", "МЕЛКИЕ"])
        rec_items = self._extract_section(response, ["RECOMMENDATIONS", "РЕКОМЕНДАЦИИ"])
        
        return {
            "findings": {
                "critical": critical_items,
                "major": major_items,
                "minor": minor_items
            },
            "recommendations": rec_items,
            "summary": self._extract_summary(response)
        }

    def _extract_section(self, text: str, section_names) -> List[str]:
        """Extract bullet points from a section.

        Purpose:
            Extracts list items from a specific section in text response.
            Supports both English and Russian section names.

        Args:
            text: Text to search
            section_names: Name(s) of section to extract (string or list)

        Returns:
            List of extracted items
        """
        items = []
        # Convert single string to list for uniform processing
        if isinstance(section_names, str):
            section_names = [section_names]
        
        for section_name in section_names:
            patterns = [
                rf"{section_name}[\s:]*\n((?:[-*]\s*.*\n?)*)",
                rf"##?\s*{section_name}[\s:]*\n((?:[-*]\s*.*\n?)*)",
                rf"{section_name}[\s:]*\n((?:\d+[.)]\s*.*\n?)*)",
            ]

            for pattern in patterns:
                section_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if section_match:
                    section_text = section_match.group(1)
                    # Extract bullet points
                    item_pattern = r"[-*]\s*(.+?)(?=\n[-*]|\n\n|\Z)"
                    matches = re.findall(item_pattern, section_text, re.DOTALL)
                    items.extend([match.strip() for match in matches if match.strip()])
                    if items:
                        return items[:10]  # Limit to 10 items

        return items[:10]  # Limit to 10 items

    def _extract_summary(self, text: str) -> str:
        """Extract summary from response.

        Purpose:
            Attempts to extract summary paragraph from response.
            Supports both English and Russian.

        Args:
            text: Response text

        Returns:
            Summary string or empty string
        """
        summary_patterns = [
            r"SUMMARY[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"Summary[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"Резюме[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]  # Limit length

        return ""

    def _convert_to_findings(self, findings_dict: Dict[str, List[str]]) -> List[Finding]:
        """Convert findings dictionary to Finding objects.

        Purpose:
            Converts parsed findings into structured Finding objects.

        Args:
            findings_dict: Dictionary with severity keys and list values

        Returns:
            List of Finding objects
        """
        findings_list = []

        for severity_str, items in findings_dict.items():
            try:
                severity = SeverityLevel(severity_str.lower())
            except ValueError:
                # Default to minor if severity unknown
                severity = SeverityLevel.MINOR

            for item in items:
                if isinstance(item, str):
                    # Try to parse structured finding
                    title = item[:100] if len(item) > 100 else item
                    description = item
                    findings_list.append(
                        Finding(
                            severity=severity,
                            title=title[:80],
                            description=description,
                        )
                    )
                elif isinstance(item, dict):
                    # Structured finding with title/description
                    findings_list.append(
                        Finding(
                            severity=severity,
                            title=item.get("title", "Issue")[:80],
                            description=item.get("description", ""),
                            location=item.get("location"),
                            recommendation=item.get("recommendation"),
                            effort_estimate=item.get("effort_estimate"),
                        )
                    )

        return findings_list

    def _build_fallback_prompt(self) -> str:
        """Build fallback prompt if template not found.

        Purpose:
            Provides a default prompt structure if prompt file missing.

        Returns:
            Prompt template string
        """
        return """# System Prompt
You are an expert software architect reviewing a codebase for architectural issues and structure.

# Task
Analyze the provided code for:
1. Overall architecture and design patterns
2. Component types detected: {detected_components}
3. High-level dependencies and integrations
4. Potential architectural issues

# Code Structure Summary
{component_summary}

# Code to Analyze
{code_snippet}

# Output Format
Return a structured analysis with:
- CRITICAL: Architectural problems that block functionality
- MAJOR: Design issues that impact scalability/maintainability
- MINOR: Code quality suggestions
- RECOMMENDATIONS: Suggested improvements

Return as JSON with keys: findings (object with critical/major/minor arrays), recommendations (array), summary (string).
"""
