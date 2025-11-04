"""Synthesis pass (Pass 3) for multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Set

from src.domain.agents.passes.base_pass import BaseReviewPass
from src.domain.models.code_review_models import (
    PassFindings,
    Finding,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class SynthesisPass(BaseReviewPass):
    """Synthesis and integration pass (Pass 3).

    Purpose:
        Synthesizes findings from all previous passes:
        - Consolidates duplicate findings
        - Prioritizes by severity and impact
        - Validates cross-component integration
        - Creates final actionable recommendations

    Example:
        pass_instance = SynthesisPass(unified_client, session_manager)
        findings = await pass_instance.run()
    """

    async def run(self, code: str = "") -> PassFindings:
        """Execute Pass 3: Synthesis & Integration Check.

        Purpose:
            Synthesizes all findings and generates final report.

        Args:
            code: Optional code (not typically used in synthesis)

        Returns:
            PassFindings with synthesized findings

        Raises:
            Exception: If synthesis fails
        """
        self.logger.info("Starting Pass 3: Synthesis & Integration Check")

        # Log pass start
        if self.review_logger:
            self.review_logger.log_review_pass(
                "pass_3",
                "started",
                {},
            )

        # 1. Load all findings from previous passes
        all_findings = self.session.load_all_findings()

        if not all_findings:
            self.logger.warning("No previous findings found for synthesis")
            return PassFindings(
                pass_name="pass_3",
                timestamp=datetime.now(),
                findings=[],
                recommendations=[],
                summary="No previous findings available for synthesis",
            )

        # 2. Build comprehensive context (with automatic compression if needed)
        synthesis_context = self._build_synthesis_context(all_findings)

        # 3. Load synthesis prompt template
        try:
            prompt_template = self._load_prompt_template("pass_3_synthesis")
        except (ValueError, FileNotFoundError):
            self.logger.warning("Synthesis prompt template not found, using fallback")
            prompt_template = self._build_fallback_prompt()

        # 4. Prepare prompt
        prompt = prompt_template.format(
            all_findings_summary=synthesis_context,
            pass_1_findings=str(all_findings.get("pass_1", {})),
            pass_2_findings=str(all_findings.get("pass_2", {})),
        )

        # 5. Call Mistral
        response = await self._call_mistral(
            prompt=prompt,
            temperature=0.5,
            max_tokens=3000,  # Increased for comprehensive synthesis
        )

        # 6. Parse and structure response
        parsed_findings = self._parse_response(response)

        # 7. Merge findings with previous passes
        merged_findings = self._merge_findings(parsed_findings, all_findings)

        # 8. Save final findings
        pass_findings = PassFindings(
            pass_name="pass_3",
            timestamp=datetime.now(),
            findings=merged_findings["findings"],
            recommendations=merged_findings["recommendations"],
            summary=merged_findings.get("summary", "Synthesis complete"),
            metadata={
                "passes_merged": list(all_findings.keys()),
                "token_estimate": self._estimate_tokens(prompt),
                "total_findings_count": len(merged_findings["findings"]),
            },
        )

        self.session.save_findings("pass_3", pass_findings.to_dict())

        # Log pass completion
        if self.review_logger:
            self.review_logger.log_review_pass(
                "pass_3",
                "completed",
                {
                    "findings_count": len(merged_findings["findings"]),
                    "passes_merged": list(all_findings.keys()),
                },
            )

        self.logger.info(
            f"Pass 3 complete. Synthesized {len(merged_findings['findings'])} findings."
        )
        return pass_findings

    def _build_synthesis_context(self, all_findings: Dict[str, Any]) -> str:
        """Build comprehensive summary of all findings with compression.

        Purpose:
            Creates detailed context for synthesis pass.
            Automatically compresses if context exceeds token limits.

        Args:
            all_findings: Dictionary of all findings from previous passes

        Returns:
            Formatted context string (compressed if needed)
        """
        context_parts = []
        context_parts.append("# Findings Summary from All Passes\n\n")

        # First pass: Build full context
        for pass_name, findings in sorted(all_findings.items()):
            context_parts.append(f"## {pass_name.upper()}\n\n")

            if isinstance(findings, dict):
                # Extract findings counts
                findings_data = findings.get("findings", {})
                if isinstance(findings_data, dict):
                    critical = len(findings_data.get("critical", []))
                    major = len(findings_data.get("major", []))
                    minor = len(findings_data.get("minor", []))
                    context_parts.append(
                        f"Findings: {critical} critical, {major} major, {minor} minor\n\n"
                    )

                # Extract summary
                if findings.get("summary"):
                    context_parts.append(f"Summary: {findings['summary']}\n\n")

                # Extract key recommendations
                recommendations = findings.get("recommendations", [])
                if recommendations:
                    context_parts.append("Key Recommendations:\n")
                    for rec in recommendations[:5]:
                        context_parts.append(f"- {rec}\n")
                    context_parts.append("\n")

        full_context = "".join(context_parts)

        # Check if compression needed (32K tokens ≈ 24K words ≈ 150K chars)
        MAX_CONTEXT_CHARS = 150000  # Conservative limit
        if len(full_context) > MAX_CONTEXT_CHARS:
            self.logger.warning(
                f"Synthesis context too large ({len(full_context)} chars). Compressing..."
            )
            return self._compress_context(full_context, all_findings)

        return full_context

    def _compress_context(
        self, context: str, all_findings: Dict[str, Any]
    ) -> str:
        """Compress context by prioritizing critical findings.

        Purpose:
            Reduces context size while preserving most important information.
            Priority: Critical > Major > Minor findings.

        Args:
            context: Full context string
            all_findings: Original findings dictionary

        Returns:
            Compressed context string
        """
        compressed_parts = []
        compressed_parts.append("# Findings Summary from All Passes (Compressed)\n\n")
        compressed_parts.append(
            "*Note: Context compressed due to size limits. Focusing on critical and major issues.\n\n"
        )

        # Build priority-based summary
        total_critical = 0
        total_major = 0
        critical_items = []
        major_items = []

        for pass_name, findings in sorted(all_findings.items()):
            if not isinstance(findings, dict):
                continue

            findings_data = findings.get("findings", {})
            if isinstance(findings_data, dict):
                critical_list = findings_data.get("critical", [])
                major_list = findings_data.get("major", [])

                total_critical += len(critical_list)
                total_major += len(major_list)

                # Collect top critical issues per pass
                for item in critical_list[:3]:  # Top 3 per pass
                    critical_items.append((pass_name, item))

                # Collect top major issues per pass
                for item in major_list[:2]:  # Top 2 per pass
                    major_items.append((pass_name, item))

            # Include summary if available
            summary = findings.get("summary")
            if summary:
                compressed_parts.append(f"### {pass_name.upper()}\n")
                compressed_parts.append(f"Summary: {summary[:200]}...\n\n")  # Truncate summary

        # Add aggregated statistics
        compressed_parts.append("## Aggregated Statistics\n\n")
        compressed_parts.append(
            f"- Total Critical Issues: {total_critical}\n"
            f"- Total Major Issues: {total_major}\n\n"
        )

        # Add top critical issues
        if critical_items:
            compressed_parts.append("## Top Critical Issues\n\n")
            for pass_name, item in critical_items[:10]:  # Top 10 overall
                item_text = item[:150] + "..." if len(item) > 150 else item
                compressed_parts.append(f"- [{pass_name}] {item_text}\n")

        # Add top major issues
        if major_items:
            compressed_parts.append("\n## Top Major Issues\n\n")
            for pass_name, item in major_items[:10]:  # Top 10 overall
                item_text = item[:150] + "..." if len(item) > 150 else item
                compressed_parts.append(f"- [{pass_name}] {item_text}\n")

        compressed_context = "".join(compressed_parts)
        self.logger.info(
            f"Compressed context: {len(context)} → {len(compressed_context)} chars "
            f"({len(compressed_context)/len(context)*100:.1f}% of original)"
        )

        return compressed_context

    def _merge_findings(
        self,
        synthesis_findings: Dict[str, Any],
        all_findings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge findings, remove duplicates, prioritize.

        Purpose:
            Combines findings from synthesis pass and previous passes,
            removing duplicates and prioritizing by severity.

        Args:
            synthesis_findings: Findings from synthesis pass
            all_findings: All findings from previous passes

        Returns:
            Merged findings dictionary
        """
        # Start with synthesis findings
        merged_findings: List[Finding] = []
        seen_titles: Set[str] = set()

        # Convert synthesis findings
        synthesis_findings_list = self._convert_to_findings(
            synthesis_findings.get("findings", {})
        )
        for finding in synthesis_findings_list:
            title_key = finding.title.lower().strip()
            if title_key not in seen_titles:
                merged_findings.append(finding)
                seen_titles.add(title_key)

        # Add unique findings from previous passes (prioritize critical)
        for pass_name, findings_data in all_findings.items():
            if pass_name == "pass_3":
                continue

            if isinstance(findings_data, dict):
                findings_dict = findings_data.get("findings", {})
                if isinstance(findings_dict, dict):
                    # Process by severity (critical first)
                    for severity in ["critical", "major", "minor"]:
                        items = findings_dict.get(severity, [])
                        for item in items:
                            if isinstance(item, str):
                                title_key = item[:80].lower().strip()
                                if title_key not in seen_titles:
                                    try:
                                        severity_level = SeverityLevel(severity)
                                    except ValueError:
                                        severity_level = SeverityLevel.MINOR

                                    merged_findings.append(
                                        Finding(
                                            severity=severity_level,
                                            title=item[:80],
                                            description=item,
                                        )
                                    )
                                    seen_titles.add(title_key)

        # Sort by severity (critical > major > minor)
        severity_order = {SeverityLevel.CRITICAL: 0, SeverityLevel.MAJOR: 1, SeverityLevel.MINOR: 2}
        merged_findings.sort(key=lambda f: severity_order.get(f.severity, 3))

        # Merge recommendations (remove duplicates)
        all_recommendations = synthesis_findings.get("recommendations", [])
        for findings_data in all_findings.values():
            if isinstance(findings_data, dict):
                recs = findings_data.get("recommendations", [])
                for rec in recs:
                    if rec not in all_recommendations:
                        all_recommendations.append(rec)

        return {
            "findings": merged_findings,
            "recommendations": all_recommendations[:20],  # Limit to top 20
            "summary": synthesis_findings.get("summary", "Synthesis complete"),
        }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse model response into structured findings.
        
        Purpose:
            Parses JSON or text response into findings structure using
            improved JSON extraction from base class.

        Args:
            response: Raw response from model

        Returns:
            Dictionary with findings structure including priority roadmap
        """
        # Try to extract JSON using improved method from base class
        parsed_json = self._extract_json_from_response(response)
        if parsed_json:
            return parsed_json

        # Fallback: extract sections manually - support both English and Russian
        self.logger.warning("JSON parsing failed, using fallback text parsing")
        # Support both English and Russian section names
        critical_items = self._extract_section(response, ["CRITICAL", "КРИТИЧЕСКИЕ", "КРИТИЧНЫЕ"])
        major_items = self._extract_section(response, ["MAJOR", "ЗНАЧИТЕЛЬНЫЕ", "СЕРЬЁЗНЫЕ"])
        minor_items = self._extract_section(response, ["MINOR", "НЕЗНАЧИТЕЛЬНЫЕ", "МЕЛКИЕ"])
        rec_items = self._extract_section(response, ["RECOMMENDATIONS", "РЕКОМЕНДАЦИИ"])
        roadmap_items = self._extract_section(response, ["ROADMAP", "ДОРОЖНАЯ КАРТА", "ПРИОРИТЕТЫ"])
        
        return {
            "findings": {
                "critical": critical_items,
                "major": major_items,
                "minor": minor_items,
            },
            "recommendations": rec_items,
            "summary": self._extract_summary(response),
            "priority_roadmap": roadmap_items,
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
                        return items[:15]

        return items[:15]

    def _extract_summary(self, text: str) -> str:
        """Extract summary from response. Supports both English and Russian."""
        summary_patterns = [
            r"EXECUTIVE\s+SUMMARY[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"SUMMARY[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
            r"Резюме[\s:]*\n(.+?)(?=\n##|\n[A-ZА-Я]+:|\Z)",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]

        return ""

    def _convert_to_findings(self, findings_dict: Dict[str, List[str]]) -> List[Finding]:
        """Convert findings dictionary to Finding objects."""
        findings_list = []

        for severity_str, items in findings_dict.items():
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

    def _build_fallback_prompt(self) -> str:
        """Build fallback prompt if template not found."""
        return """# System Prompt
You are a senior software architect synthesizing findings from multiple analysis passes.

# Task
Synthesize findings from all passes:
1. Consolidate duplicate/related findings
2. Prioritize by severity and impact
3. Cross-component validation
4. Identify systemic issues
5. Create actionable recommendations

# Findings from Pass 1 (Architecture Overview)
{pass_1_findings}

# Findings from Pass 2 (Component Analysis)
{pass_2_findings}

# Output Format
Provide final report as JSON:
{{
  "summary": "...",
  "findings": {{
    "critical": [...],
    "major": [...],
    "minor": [...]
  }},
  "recommendations": [...],
  "priority_roadmap": [...]
}}
"""

