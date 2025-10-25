"""
Report Generator for comprehensive markdown reports.

This module provides the ReportGenerator class that creates comprehensive
markdown reports with tables, statistics, and recommendations for the
model switching demo results.
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.data_models import (
    ThreeStageResult,
    CompressionTestResult,
    ModelWorkflowResult
)
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class ReportGenerator:
    """
    Generator for comprehensive markdown reports.
    
    Creates detailed reports with tables, statistics, charts, and
    recommendations based on demo results.
    
    Attributes:
        logger: Logger instance for structured logging
        reports_dir: Directory to save reports
        
    Example:
        ```python
        from utils.report_generator import ReportGenerator
        
        # Initialize generator
        generator = ReportGenerator()
        
        # Generate comprehensive report
        report_path = await generator.generate_comprehensive_report(
            results=demo_results,
            config=demo_config
        )
        
        print(f"Report saved to: {report_path}")
        ```
    """
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize the report generator.

        Args:
            reports_dir: Directory to save reports
            
        Example:
            ```python
            from utils.report_generator import ReportGenerator
            
            # Initialize with default directory
            generator = ReportGenerator()
            
            # Or with custom directory
            generator = ReportGenerator("custom_reports")
            ```
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Initialized ReportGenerator with directory: {self.reports_dir}")
    
    async def generate_comprehensive_report(
        self,
        results: Dict[str, Any],
        config: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            results: Demo results dictionary
            config: Demo configuration
            filename: Optional custom filename
            
        Returns:
            Path to generated report file
            
        Example:
            ```python
            # Generate comprehensive report
            report_path = await generator.generate_comprehensive_report(
                results=demo_results,
                config=demo_config
            )
            
            print(f"Report generated: {report_path}")
            ```
        """
        try:
            self.logger.info("Generating comprehensive report...")
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"model_switching_demo_{timestamp}.md"
            
            report_path = self.reports_dir / filename
            
            # Generate report content
            report_content = self._generate_report_content(results, config)
            
            # Write report to file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Report generated: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            raise
    
    def _generate_report_content(
        self, 
        results: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> str:
        """Generate the complete report content."""
        content = []
        
        # Header
        content.append(self._generate_header())
        
        # Executive Summary
        content.append(self._generate_executive_summary(results))
        
        # Per-Model Analysis
        content.append(self._generate_per_model_analysis(results))
        
        # Compression Algorithm Comparison
        content.append(self._generate_compression_comparison(results))
        
        # Quality Assessment
        content.append(self._generate_quality_assessment(results))
        
        # Performance Analysis
        content.append(self._generate_performance_analysis(results))

            # Recommendations
        content.append(self._generate_recommendations(results, config))
        
        # Detailed Experiment Logs
        content.append(self._generate_detailed_logs(results))
        
        # Footer
        content.append(self._generate_footer())
        
        return "\n\n".join(content)
    
    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# Model Switching Demo Report

**Generated:** {timestamp}  
**Version:** Day 08 Enhanced Token Analysis System  
**Type:** Comprehensive Model Comparison and Compression Analysis

---

## Overview

This report presents the results of a comprehensive model switching demo that evaluates multiple AI models across different token limit scenarios, compression algorithms, and quality metrics. The demo tests models' capabilities with coding tasks at three complexity levels and evaluates the effectiveness of various compression strategies.

"""
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        summary = results.get("summary", {})
        
        models_tested = summary.get("models_tested", 0)
        total_experiments = summary.get("total_experiments", 0)
        successful_experiments = summary.get("successful_experiments", 0)
        success_rate = summary.get("success_rate", 0.0)
        best_model = summary.get("best_model", "N/A")
        best_compression = summary.get("best_compression", "N/A")
        
        return f"""## Executive Summary

### Key Metrics
- **Models Tested:** {models_tested}
- **Total Experiments:** {total_experiments}
- **Successful Experiments:** {successful_experiments}
- **Success Rate:** {success_rate*100:.1f}%
- **Best Performing Model:** {best_model}
- **Best Compression Strategy:** {best_compression}

### Highlights
- Comprehensive testing across multiple models and compression strategies
- Three-stage token limit evaluation (short/medium/long queries)
- Quality assessment using multiple metrics
- Performance analysis with detailed statistics
- Actionable recommendations for model selection and compression usage

"""
    
    def _generate_per_model_analysis(self, results: Dict[str, Any]) -> str:
        """Generate per-model analysis section."""
        content = ["## Per-Model Analysis"]
        
        three_stage_results = results.get("three_stage_results", {})
        model_statistics = results.get("model_statistics", {})
        
        for model_name in three_stage_results.keys():
            content.append(f"### {model_name.title()}")
            
            # Three-stage test results
            stage_results = three_stage_results[model_name]
            if isinstance(stage_results, ThreeStageResult):
                content.append(f"""
**Three-Stage Test Results:**
- Short Query: {stage_results.short_query_tokens} tokens
- Medium Query: {stage_results.medium_query_tokens} tokens  
- Long Query: {stage_results.long_query_tokens} tokens
- Queries Exceeding Limit: {stage_results.queries_exceeding_limit}/3
- Compression Needed: {'Yes' if stage_results.compression_needed else 'No'}
""")
            
            # Model statistics
            stats = model_statistics.get(model_name, {})
            if stats:
                success_rate = stats.get("successful_requests", 0) / max(1, stats.get("total_requests", 1)) * 100
                content.append(f"""
**Performance Statistics:**
- Total Requests: {stats.get("total_requests", 0)}
- Successful Requests: {stats.get("successful_requests", 0)}
- Success Rate: {success_rate:.1f}%
- Average Response Time: {stats.get("average_response_time", 0):.2f}s
- Total Tokens Used: {stats.get("total_tokens_used", 0)}
""")
            
            content.append("")
        
        return "\n".join(content)
    
    def _generate_compression_comparison(self, results: Dict[str, Any]) -> str:
        """Generate compression algorithm comparison section."""
        content = ["## Compression Algorithm Comparison"]
        
        compression_results = results.get("compression_results", {})
        
        if not compression_results:
            content.append("No compression results available.")
            return "\n".join(content)
        
        # Create comparison table
        content.append("""
| Model | Strategy | Compression Ratio | Response Time | Success | Tokens Saved |
|-------|----------|------------------|---------------|---------|--------------|""")
        
        for model_name, model_results in compression_results.items():
            if isinstance(model_results, list):
                for result in model_results:
                    if isinstance(result, CompressionTestResult):
                        success_icon = "✅" if result.success else "❌"
                        content.append(f"| {model_name} | {result.strategy} | {result.compression_ratio:.2f} | {result.response_time:.2f}s | {success_icon} | {result.tokens_saved} |")
        
        content.append("""
### Compression Strategy Analysis

**Best Performing Strategies:**
1. **Truncation** - Most reliable, preserves beginning and end
2. **Keywords** - Good for code tasks, extracts key terms
3. **Extractive** - Good for documentation, extracts important sentences
4. **Semantic** - Advanced but may fail on complex queries
5. **Summarization** - Most advanced but slowest

**Recommendations:**
- Use **truncation** for reliable compression
- Use **keywords** for code-related tasks
- Use **extractive** for documentation tasks
- Test **semantic** and **summarization** for advanced use cases

""")
        
        return "\n".join(content)
    
    def _generate_quality_assessment(self, results: Dict[str, Any]) -> str:
        """Generate quality assessment section."""
        content = ["## Quality Assessment"]
        
        quality_results = results.get("quality_results", {})
        
        if not quality_results:
            content.append("No quality assessment results available.")
            return "\n".join(content)
        
        content.append("""
| Model | Strategy | Overall Quality | Code Quality | Completeness | Performance |
|-------|----------|-----------------|--------------|--------------|-------------|""")
        
        for model_name, model_qualities in quality_results.items():
            for strategy, quality in model_qualities.items():
                if isinstance(quality, dict) and "overall_score" in quality:
                    overall_score = quality.get("overall_score", 0.0)
                    code_quality = quality.get("code_quality", {})
                    completeness = quality.get("completeness", {})
                    performance = quality.get("performance", {})
                    
                    code_score = code_quality.get("code_quality_score", 0.0) if isinstance(code_quality, dict) else 0.0
                    completeness_score = completeness.get("completeness_score", 0.0) if isinstance(completeness, dict) else 0.0
                    response_time = performance.get("response_time", 0.0) if isinstance(performance, dict) else 0.0
                    
                    content.append(f"| {model_name} | {strategy} | {overall_score:.2f} | {code_score:.2f} | {completeness_score:.2f} | {response_time:.2f}s |")
        
        content.append("""
### Quality Metrics Explanation

- **Overall Quality (0-1):** Combined score from all quality metrics
- **Code Quality (0-10):** PEP8 compliance, documentation, type hints, complexity
- **Completeness (0-1):** How well response addresses original requirements
- **Performance:** Response time in seconds

**Quality Thresholds:**
- High Quality: Overall score > 0.8
- Acceptable Quality: Overall score > 0.6
- Poor Quality: Overall score < 0.4

""")
        
        return "\n".join(content)
    
    def _generate_performance_analysis(self, results: Dict[str, Any]) -> str:
        """Generate performance analysis section."""
        content = ["## Performance Analysis"]
        
        model_statistics = results.get("model_statistics", {})
        
        if not model_statistics:
            content.append("No performance statistics available.")
            return "\n".join(content)
        
        # Performance comparison table
        content.append("""
| Model | Avg Response Time | Success Rate | Total Requests | Tokens Used |
|-------|-------------------|--------------|----------------|-------------|""")
        
        for model_name, stats in model_statistics.items():
            avg_time = stats.get("average_response_time", 0.0)
            success_rate = stats.get("successful_requests", 0) / max(1, stats.get("total_requests", 1)) * 100
            total_requests = stats.get("total_requests", 0)
            tokens_used = stats.get("total_tokens_used", 0)
            
            content.append(f"| {model_name} | {avg_time:.2f}s | {success_rate:.1f}% | {total_requests} | {tokens_used} |")
        
        content.append("""
### Performance Benchmarks

**Response Time Categories:**
- Excellent: < 2.0 seconds
- Good: 2.0 - 5.0 seconds  
- Acceptable: 5.0 - 10.0 seconds
- Poor: > 10.0 seconds

**Success Rate Categories:**
- Excellent: > 95%
- Good: 90% - 95%
- Acceptable: 80% - 90%
- Poor: < 80%

""")
        
        return "\n".join(content)
    
    def _generate_recommendations(self, results: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate recommendations section."""
        summary = results.get("summary", {})
        best_model = summary.get("best_model", "N/A")
        best_compression = summary.get("best_compression", "N/A")
        
        content = ["## Recommendations"]
        
        content.append(f"""
### Model Selection
- **Primary Recommendation:** Use **{best_model}** for best overall performance
- **Backup Option:** Consider other tested models for specific use cases
- **Model Switching:** Implement dynamic model switching based on task complexity

### Compression Strategy
- **Primary Recommendation:** Use **{best_compression}** for optimal quality/efficiency balance
- **Fallback Strategy:** Use truncation for reliable compression
- **Task-Specific:** 
  - Use keywords compression for code tasks
  - Use extractive compression for documentation
  - Test semantic/summarization for advanced use cases

### Implementation Guidelines
1. **Token Monitoring:** Implement real-time token counting and limit checking
2. **Compression Pipeline:** Set up automatic compression for queries exceeding limits
3. **Quality Assurance:** Use quality metrics to validate compression effectiveness
4. **Performance Monitoring:** Track response times and success rates
5. **Fallback Mechanisms:** Implement graceful degradation when models fail

### Best Practices
- Test compression strategies on your specific use cases
- Monitor quality metrics to ensure compression doesn't degrade results
- Implement caching for frequently used compressed queries
- Use model-specific optimizations based on capabilities
- Regular evaluation and model comparison

""")
        
        return "\n".join(content)
    
    def _generate_detailed_logs(self, results: Dict[str, Any]) -> str:
        """Generate detailed experiment logs section."""
        content = ["## Detailed Experiment Logs"]
        
        # Three-stage results
        three_stage_results = results.get("three_stage_results", {})
        if three_stage_results:
            content.append("### Three-Stage Test Results")
            for model_name, stage_results in three_stage_results.items():
                if isinstance(stage_results, ThreeStageResult):
                    content.append(f"""
**{model_name.title()} Three-Stage Test:**
- Short Query Tokens: {stage_results.short_query_tokens}
- Medium Query Tokens: {stage_results.medium_query_tokens}
- Long Query Tokens: {stage_results.long_query_tokens}
- Model Limits: {stage_results.model_limits.max_input_tokens} max input tokens
- Success: {stage_results.success}
- Timestamp: {stage_results.timestamp}
""")
        
        # Compression results
        compression_results = results.get("compression_results", {})
        if compression_results:
            content.append("### Compression Test Results")
            for model_name, model_results in compression_results.items():
                if isinstance(model_results, list):
                    content.append(f"\n**{model_name.title()} Compression Tests:**")
                    for result in model_results:
                        if isinstance(result, CompressionTestResult):
                            content.append(f"""
- Strategy: {result.strategy}
- Original Tokens: {result.original_tokens}
- Compressed Tokens: {result.compressed_tokens}
- Compression Ratio: {result.compression_ratio:.2f}
- Response Time: {result.response_time:.2f}s
- Success: {result.success}
- Tokens Saved: {result.tokens_saved}
""")
        
        return "\n".join(content)
    
    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""
---

## Report Information

**Generated by:** Day 08 Enhanced Token Analysis System  
**Report Type:** Model Switching Demo Analysis  
**Generated at:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### System Information
- **Python Version:** {sys.version.split()[0]}
- **Report Generator Version:** 1.0.0
- **Data Models:** Enhanced with compression and quality metrics

### Contact
For questions about this report or the model switching demo, please refer to the project documentation.

---
*This report was automatically generated by the Day 08 Model Switching Demo system.*
"""