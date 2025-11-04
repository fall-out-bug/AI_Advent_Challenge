"""Component deep-dive pass (Pass 2) for multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.agents.passes.base_pass import BaseReviewPass
from src.domain.models.code_review_models import (
    PassFindings,
    Finding,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class ComponentDeepDivePass(BaseReviewPass):
    """Component-specific deep-dive pass (Pass 2).

    Purpose:
        Performs detailed analysis for specific component types:
        - Docker/Docker Compose configurations
        - Apache Airflow DAGs
        - Spark jobs
        - MLflow tracking

    Example:
        pass_instance = ComponentDeepDivePass(unified_client, session_manager)
        findings = await pass_instance.run(code, component_type="docker")
    """

    async def run(
        self,
        code: str,
        component_type: str,
        context_from_pass_1: Optional[Dict[str, Any]] = None,
    ) -> PassFindings:
        """Execute Pass 2: Component Deep-Dive.

        Purpose:
            Performs detailed component-specific analysis.

        Args:
            code: Code to analyze
            component_type: Type of component ("docker", "airflow", "spark", "mlflow")
            context_from_pass_1: Optional context from Pass 1

        Returns:
            PassFindings with component-specific findings

        Raises:
            Exception: If analysis fails
        """
        self.logger.info(f"Starting Pass 2: Component Deep-Dive for {component_type}")

        # Log pass start
        pass_name = f"pass_2_{component_type}"
        if self.review_logger:
            self.review_logger.log_review_pass(
                pass_name,
                "started",
                {"component_type": component_type, "code_length": len(code)},
            )

        # 1. Load context from Pass 1
        pass_1_context = context_from_pass_1 or self.session.load_findings("pass_1")
        context_summary = self.session.get_context_summary_for_next_pass()

        # 2. Extract relevant code for this component
        component_code = self._extract_component_code(code, component_type)

        # 3. Load specialized prompt template
        prompt_name = f"pass_2_{component_type}"
        try:
            prompt_template = self._load_prompt_template(prompt_name)
        except (ValueError, FileNotFoundError):
            self.logger.warning(f"Prompt template '{prompt_name}' not found, using fallback")
            prompt_template = self._build_fallback_prompt(component_type)

        # 4. Prepare prompt with context from Pass 1
        prompt = prompt_template.format(
            code_snippet=component_code[:5000],  # Limit to 5K chars for component analysis
            context_from_pass_1=context_summary,
            component_type=component_type,
        )

        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.6,
            max_tokens=3000,  # Increased for thorough component analysis
        )

        # Log full response for debugging (first 1000 and last 500 chars)
        response_preview = (
            f"{response[:1000]}...\n...{response[-500:]}"
            if len(response) > 1500
            else response
        )
        self.logger.info(
            f"Pass 2 ({component_type}) model response (length: {len(response)}):\n{response_preview}"
        )

        # 6. Parse response
        parsed_findings = self._parse_response(response)

        # 7. Convert to Finding objects
        # Safely extract findings - handle both dict and string errors
        findings_data = parsed_findings.get("findings", {})
        if not isinstance(findings_data, dict):
            self.logger.error(
                f"Invalid findings format: expected dict, got {type(findings_data)}. "
                f"Value: {str(findings_data)[:200]}"
            )
            findings_data = {}
        
        try:
            findings_list = self._convert_to_findings(findings_data)
        except Exception as e:
            self.logger.error(f"Failed to convert findings: {e}. Findings data: {findings_data}")
            findings_list = []

        # 8. Save findings
        pass_name = f"pass_2_{component_type}"
        pass_findings = PassFindings(
            pass_name=pass_name,
            timestamp=datetime.now(),
            findings=findings_list,
            recommendations=parsed_findings.get("recommendations", []),
            summary=parsed_findings.get("summary"),
            metadata={
                "component_type": component_type,
                "token_estimate": self._estimate_tokens(prompt),
            },
        )

        self.session.save_findings(pass_name, pass_findings.to_dict())

        # Log pass completion
        if self.review_logger:
            self.review_logger.log_review_pass(
                pass_name,
                "completed",
                {
                    "findings_count": len(findings_list),
                    "component_type": component_type,
                },
            )

        self.logger.info(
            f"Pass 2 complete for {component_type}. Found {len(findings_list)} findings."
        )
        return pass_findings

    def _extract_component_code(self, code: str, component_type: str) -> str:
        """Extract code relevant to specific component type.

        Purpose:
            Attempts to extract component-specific code sections.

        Args:
            code: Full codebase
            component_type: Type of component to extract

        Returns:
            Extracted component code or full code if extraction fails
        """
        code_lower = code.lower()

        if component_type == "docker":
            # Extract docker-compose or Dockerfile content
            docker_compose_match = re.search(
                r"(version:[\s\S]*?services:[\s\S]*?)(?=\n\w|\Z)", code, re.IGNORECASE
            )
            if docker_compose_match:
                return docker_compose_match.group(1)

            dockerfile_match = re.search(r"(FROM[\s\S]*?)(?=\nFROM|\Z)", code, re.IGNORECASE)
            if dockerfile_match:
                return dockerfile_match.group(1)

            # If contains docker keywords, return relevant lines
            docker_lines = [
                line for line in code.split("\n") if "docker" in line.lower()
            ]
            if docker_lines:
                return "\n".join(docker_lines[:100])  # Limit to 100 lines

        elif component_type == "airflow":
            # Extract DAG definitions
            dag_patterns = [
                r"(@dag[\s\S]*?)(?=\n@dag|\n\ndef|\Z)",
                r"(from airflow[\s\S]*?DAG\([\s\S]*?)(?=\nclass|\ndef\s+(?!.*dag)|\Z)",
            ]

            for pattern in dag_patterns:
                matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
                if matches:
                    return "\n".join(matches)

            # Extract lines with airflow keywords
            airflow_lines = [
                line for line in code.split("\n") if "airflow" in line.lower() or "dag" in line.lower()
            ]
            if airflow_lines:
                return "\n".join(airflow_lines[:150])

        elif component_type == "spark":
            # Extract Spark-related code
            spark_patterns = [
                r"(from pyspark[\s\S]*?)(?=\nfrom|\ndef\s+(?!.*spark)|\Z)",
                r"(SparkSession[\s\S]*?)(?=\nclass|\ndef\s+(?!.*spark)|\Z)",
            ]

            for pattern in spark_patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    return "\n".join(matches)

            spark_lines = [
                line for line in code.split("\n")
                if "spark" in line.lower() or "pyspark" in line.lower()
            ]
            if spark_lines:
                return "\n".join(spark_lines[:150])

        elif component_type == "mlflow":
            # Extract MLflow tracking code
            mlflow_patterns = [
                r"(import mlflow[\s\S]*?)(?=\nimport|\ndef\s+(?!.*mlflow)|\Z)",
                r"(mlflow\.[\s\S]*?)(?=\n\w|\Z)",
            ]

            for pattern in mlflow_patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    return "\n".join(matches)

            mlflow_lines = [
                line
                for line in code.split("\n")
                if "mlflow" in line.lower()
                or "log_metric" in line.lower()
                or "log_param" in line.lower()
            ]
            if mlflow_lines:
                return "\n".join(mlflow_lines[:150])

        # Return full code if can't extract
        return code

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse model response into structured findings.

        Purpose:
            Parses JSON or text response into findings structure using
            improved JSON extraction from base class.

        Args:
            response: Raw response from model

        Returns:
            Dictionary with findings structure
        """
        # Log response for debugging (first 500 chars)
        self.logger.debug(f"Parsing response (length: {len(response)}, preview: {response[:500]})")
        
        # Try to extract JSON using improved method from base class
        try:
            parsed_json = self._extract_json_from_response(response)
            if parsed_json:
                self.logger.debug(f"Successfully parsed JSON: {list(parsed_json.keys())}")
                return parsed_json
        except Exception as e:
            self.logger.warning(f"JSON extraction raised exception: {e}, using fallback text parsing")
            # Log the problematic part of response
            if len(response) > 200:
                self.logger.debug(f"Response excerpt around error: ...{response[max(0, len(response)-200):]}")

        # Fallback: extract sections manually - support both English and Russian
        self.logger.warning("JSON parsing failed, using fallback text parsing")
        # Support both English and Russian section names
        critical_items = self._extract_section(response, ["CRITICAL", "КРИТИЧЕСКИЕ", "КРИТИЧНЫЕ"])
        major_items = self._extract_section(response, ["MAJOR", "ЗНАЧИТЕЛЬНЫЕ", "СЕРЬЁЗНЫЕ"])
        minor_items = self._extract_section(response, ["MINOR", "НЕЗНАЧИТЕЛЬНЫЕ", "МЕЛКИЕ"])
        rec_items = self._extract_section(response, ["RECOMMENDATIONS", "РЕКОМЕНДАЦИИ"])
        
        # If no structured sections found, try to extract from plain text recommendations
        if not critical_items and not major_items and not minor_items:
            self.logger.debug("No structured sections found, extracting from plain text")
            # Extract bullet points and numbered lists from response
            text_items = self._extract_text_recommendations(response)
            if text_items:
                # Classify as major issues (since model didn't specify severity)
                major_items = text_items[:10]  # Limit to 10 items
                self.logger.info(f"Extracted {len(major_items)} recommendations from plain text")
        
        # Log what was extracted
        self.logger.debug(f"Fallback extraction: critical={len(critical_items)}, major={len(major_items)}, minor={len(minor_items)}")
        
        return {
            "findings": {
                "critical": critical_items,
                "major": major_items,
                "minor": minor_items,
            },
            "recommendations": rec_items if rec_items else major_items[:5],  # Use major items as recommendations if no explicit recommendations
            "summary": self._extract_summary(response),
        }

    def _extract_section(self, text: str, section_names) -> List[str]:
        """Extract bullet points from a section. Supports both English and Russian."""
        items = []
        if isinstance(section_names, str):
            section_names = [section_names]
        
        for section_name in section_names:
            patterns = [
                rf"{section_name}[\s:]*\n((?:[-*]\s*.*\n?)*)",
                rf"##?\s*{section_name}[\s:]*\n((?:[-*]\s*.*\n?)*)",
            ]

            for pattern in patterns:
                section_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if section_match:
                    section_text = section_match.group(1)
                    item_pattern = r"[-*]\s*(.+?)(?=\n[-*]|\n\n|\Z)"
                    matches = re.findall(item_pattern, section_text, re.DOTALL)
                    items.extend([match.strip() for match in matches if match.strip()])
                    if items:
                        return items[:10]

        return items[:10]

    def _extract_summary(self, text: str) -> str:
        """Extract summary from response. Supports both English and Russian."""
        summary_patterns = [
            r"SUMMARY[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"Summary[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"Резюме[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]

        # If no explicit summary, use first paragraph
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.strip() and len(line.strip()) > 50:
                return line.strip()[:500]

        return ""

    def _extract_text_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from plain text response.
        
        Extracts bullet points, numbered items, and recommendations
        from unstructured text responses.
        """
        items = []
        
        # Pattern 1: Bullet points (-, *, •)
        bullet_pattern = r"[-*•]\s+(.+?)(?=\n[-*•]|\n\n|\n\d+\.|\Z)"
        bullet_matches = re.findall(bullet_pattern, text, re.MULTILINE | re.DOTALL)
        items.extend([m.strip() for m in bullet_matches if m.strip() and len(m.strip()) > 10])
        
        # Pattern 2: Numbered lists (1., 2., a., b.)
        numbered_pattern = r"\d+\.\s+([A-Z].+?)(?=\n\d+\.|\n[a-z]\.|\n\n|\Z)"
        numbered_matches = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)
        items.extend([m.strip() for m in numbered_matches if m.strip() and len(m.strip()) > 10])
        
        # Pattern 3: Lettered sub-items (a., b., c.)
        lettered_pattern = r"[a-z]\.\s+(.+?)(?=\n[a-z]\.|\n\d+\.|\n\n|\Z)"
        lettered_matches = re.findall(lettered_pattern, text, re.MULTILINE | re.DOTALL)
        items.extend([m.strip() for m in lettered_matches if m.strip() and len(m.strip()) > 10])
        
        # Pattern 4: "It's recommended", "should", "consider" patterns
        recommendation_patterns = [
            r"It's recommended that (.+?)(?=\.|;|\n)",
            r"It's good that (.+?)(?=\.|;|\n)",
            r"should (.+?)(?=\.|;|\n)",
            r"consider (.+?)(?=\.|;|\n)",
            r"recommended to (.+?)(?=\.|;|\n)",
        ]
        for pattern in recommendation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            items.extend([m.strip() for m in matches if m.strip() and len(m.strip()) > 10])
        
        # Remove duplicates and limit
        seen = set()
        unique_items = []
        for item in items:
            # Normalize: lowercase, remove extra spaces
            normalized = re.sub(r'\s+', ' ', item.lower().strip())
            if normalized not in seen and len(item.strip()) > 15:
                seen.add(normalized)
                unique_items.append(item.strip())
        
        return unique_items[:15]  # Return top 15 unique recommendations

    def _convert_to_findings(self, findings_dict: Dict[str, List[str]]) -> List[Finding]:
        """Convert findings dictionary to Finding objects."""
        findings_list = []

        # Validate input
        if not isinstance(findings_dict, dict):
            self.logger.error(
                f"_convert_to_findings: expected dict, got {type(findings_dict)}: {findings_dict}"
            )
            return findings_list

        for severity_str, items in findings_dict.items():
            # Validate items is a list
            if not isinstance(items, list):
                self.logger.warning(
                    f"_convert_to_findings: severity '{severity_str}' has non-list items: {type(items)}"
                )
                continue

            try:
                severity = SeverityLevel(severity_str.lower())
            except ValueError:
                severity = SeverityLevel.MINOR

            for item in items:
                if isinstance(item, str):
                    title = item[:100] if len(item) > 100 else item
                    description = item
                    findings_list.append(
                        Finding(severity=severity, title=title[:80], description=description)
                    )
                elif isinstance(item, dict):
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

    def _build_fallback_prompt(self, component_type: str) -> str:
        """Build fallback prompt if template not found."""
        # Use double braces {{ }} to escape them in .format()
        return f"""# System Prompt
You are a {component_type.upper()} expert reviewing {component_type} configuration/code.

# Context from Pass 1 (Architecture Overview)
{{context_from_pass_1}}

# Task
Perform detailed review of {component_type} configuration:
- Best practices compliance
- Security issues
- Performance optimization opportunities
- Error handling
- Configuration correctness

# {component_type.upper()} Code
{{code_snippet}}

# Output Format
Return as JSON:
{{{{
  "findings": {{{{
    "critical": [...],
    "major": [...],
    "minor": [...]
  }}}},
  "recommendations": [...],
  "summary": "..."
}}}}
"""

