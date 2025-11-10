"""Domain interface for log analysis via LLM.

Following Clean Architecture: protocol definition in domain layer.
"""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.value_objects.log_analysis import LogAnalysisResult, LogGroup


class LogAnalyzer(Protocol):
    """Protocol for analyzing log groups via LLM.

    Purpose:
        Defines interface for analyzing grouped log entries using language models.
        Implementations use UnifiedModelClient or other LLM providers.

    Example:
        analyzer = LLMLogAnalyzer(unified_client=client)
        result = await analyzer.analyze_log_group(log_group)
    """

    async def analyze_log_group(
        self, log_group: LogGroup
    ) -> Optional[LogAnalysisResult]:
        """Analyze log group and return structured result.

        Purpose:
            Send log group sample to LLM for analysis, classification, and
            recommendations. Returns None if analysis fails after retries.

        Args:
            log_group: Group of similar log entries to analyze

        Returns:
            LogAnalysisResult with classification and recommendations, or None if failed

        Raises:
            ValueError: If log_group is invalid
            TimeoutError: If LLM request times out (after retries)

        Example:
            result = await analyzer.analyze_log_group(
                log_group=LogGroup(component="checker", ...)
            )
            if result:
                print(result.classification)  # "critical"
        """
        ...
