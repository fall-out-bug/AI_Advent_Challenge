"""
Demo Report Generator Module.

This module provides a comprehensive report generator for demo results with
detailed markdown formatting including collapsible sections for long content.

Following Python Zen principles:
- Beautiful is better than ugly
- Readability counts
- Simple is better than complex
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from config.demo_config import get_model_config


class DemoReportGenerator:
    """
    Generate comprehensive markdown reports for demo results.
    
    This class creates detailed, human-readable markdown reports with complete
    model information, prompts, test results, and full compression outputs.
    Uses collapsible sections to handle long content without overwhelming
    the reader.
    
    Attributes:
        None
        
    Example:
        ```python
        from utils.demo_report_generator import DemoReportGenerator
        
        generator = DemoReportGenerator()
        report = generator.generate_report(results_dict)
        
        # Save to file
        Path("report.md").write_text(report, encoding='utf-8')
        ```
    """
    
    def __init__(self):
        """Initialize the demo report generator."""
        pass
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate full markdown report with comprehensive demo results.
        
        Args:
            results: Dictionary containing all demo results from enhanced demo
            
        Returns:
            Complete markdown report as string
            
        Example:
            ```python
            results = await demo.run_enhanced_demo()
            report = generator.generate_report(results)
            ```
        """
        report_lines = []
        
        # Header
        report_lines.append(self._generate_header(results))
        
        # Table of Contents
        report_lines.append(self._generate_table_of_contents())
        
        # Model Information
        report_lines.append(self._generate_model_section(results))
        
        # Test Results
        report_lines.append(self._generate_test_results_section(results))
        
        # Compression Results
        report_lines.append(self._generate_compression_section(results))
        
        # Quality Analysis
        report_lines.append(self._generate_quality_section(results))
        
        # Summary
        report_lines.append(self._generate_summary_section(results))
        
        return "\n".join(report_lines)
    
    def _generate_header(self, results: Dict[str, Any]) -> str:
        """
        Generate report header with metadata.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Header markdown section
        """
        summary = results.get("summary", {})
        timestamp = results.get("timestamp", datetime.now().isoformat())
        
        return f"""# Token Analysis Demo Report

**Generated:** {timestamp}
**Models Tested:** {', '.join(summary.get('models_tested', []))}
**Success Rate:** {summary.get('success_rate', 0.0) * 100:.1f}%

---
"""
    
    def _generate_table_of_contents(self) -> str:
        """Generate table of contents."""
        return """## Table of Contents

- [Model Information](#model-information)
- [Test Results](#test-results)
- [Compression Analysis](#compression-analysis)
- [Quality Metrics](#quality-metrics)
- [Summary & Recommendations](#summary--recommendations)

---
"""
    
    def _generate_model_section(self, results: Dict[str, Any]) -> str:
        """
        Generate model information section.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Model information markdown section
        """
        lines = ["## Model Information\n"]
        
        models_tested = results.get("three_stage_results", {}).keys()
        
        for model_name in models_tested:
            model_config = get_model_config(model_name)
            
            lines.append(f"### Model: {model_name}\n")
            lines.append(self._create_collapsible_section(
                "Model Specifications",
                self._format_model_specs(model_config)
            ))
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_model_specs(self, model_config: Dict[str, Any]) -> str:
        """
        Format model specifications.
        
        Args:
            model_config: Model configuration dictionary
            
        Returns:
            Formatted specifications
        """
        return f"""- **Max Input Tokens:** {model_config.get('max_tokens', 'Unknown')}
- **Recommended Input:** {model_config.get('recommended_input', 'Unknown')}
- **Context Window:** {model_config.get('context_window', 'Unknown')}
- **Model Type:** {model_config.get('model_type', 'Unknown')}
- **Container Image:** {model_config.get('container_image', 'Unknown')}"""
    
    def _generate_test_results_section(self, results: Dict[str, Any]) -> str:
        """
        Generate test results section with full outputs.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Test results markdown section
        """
        lines = ["## Test Results\n"]
        
        three_stage_results = results.get("three_stage_results", {})
        
        for model_name, result in three_stage_results.items():
            if not result.success:
                continue
            
            lines.append(f"### Model: {model_name}\n")
            
            # Test each stage
            for stage in ["short", "medium", "long"]:
                lines.append(self._format_stage_results(stage, result, model_name))
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_stage_results(self, stage: str, result, model_name: str) -> str:
        """
        Format results for a specific stage.
        
        Args:
            stage: Stage name (short/medium/long)
            result: ThreeStageResult object
            model_name: Name of the model
            
        Returns:
            Formatted stage results
        """
        query = getattr(result, f"{stage}_query", "")
        tokens = getattr(result, f"{stage}_query_tokens", 0)
        exceeds = getattr(result, f"{stage}_exceeds_limit", False)
        response = getattr(result, f"{stage}_response", "")
        
        lines = [f"#### {stage.capitalize()} Query Test\n"]
        
        # Query details
        lines.append(f"**Token Count:** {tokens}")
        lines.append(f"**Exceeds Limit:** {'Yes' if exceeds else 'No'}")
        lines.append("")
        
        # Full query in collapsible section
        lines.append(self._create_collapsible_section(
            f"Full Query ({tokens} tokens)",
            self._format_code_block(query)
        ))
        lines.append("")
        
        # Model response in collapsible section
        if response:
            lines.append(self._create_collapsible_section(
                "Full Model Response",
                self._format_code_block(response, "python")
            ))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_compression_section(self, results: Dict[str, Any]) -> str:
        """
        Generate compression analysis section.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Compression results markdown section
        """
        lines = ["## Compression Analysis\n"]
        
        compression_results = results.get("compression_results", {})
        
        for model_name, model_compressions in compression_results.items():
            lines.append(f"### Model: {model_name}\n")
            
            for stage, stage_compressions in model_compressions.items():
                lines.append(f"#### {stage.capitalize()} Query Compressions\n")
                
                for strategy_name, compression in stage_compressions.items():
                    if not hasattr(compression, 'success') or not compression.success:
                        continue
                    
                    lines.append(self._format_compression_result(
                        strategy_name, compression
                    ))
                    lines.append("")
        
        return "\n".join(lines)
    
    def _format_compression_result(self, strategy: str, result) -> str:
        """
        Format single compression result.
        
        Args:
            strategy: Compression strategy name
            result: CompressionResult object
            
        Returns:
            Formatted compression result
        """
        lines = [f"**Strategy:** {strategy}\n"]
        
        # Compression metrics
        original_tokens = result.original_tokens
        compressed_tokens = result.compressed_tokens
        compression_ratio = (compressed_tokens / original_tokens * 100) if original_tokens > 0 else 0
        token_savings = original_tokens - compressed_tokens
        
        lines.append(f"**Compression Metrics:**")
        lines.append(f"- Original Tokens: {original_tokens}")
        lines.append(f"- Compressed Tokens: {compressed_tokens}")
        lines.append(f"- Compression Ratio: {compression_ratio:.1f}%")
        lines.append(f"- Token Savings: {token_savings}")
        lines.append("")
        
        # Original query
        if hasattr(result, 'original_query') and result.original_query:
            lines.append(self._create_collapsible_section(
                f"Original Query ({original_tokens} tokens)",
                self._format_code_block(result.original_query)
            ))
            lines.append("")
        
        # Compressed query
        if hasattr(result, 'compressed_query') and result.compressed_query:
            lines.append(self._create_collapsible_section(
                f"Compressed Query ({compressed_tokens} tokens)",
                self._format_code_block(result.compressed_query)
            ))
            lines.append("")
        
        # Model response
        if hasattr(result, 'response') and result.response:
            lines.append(self._create_collapsible_section(
                "Full Model Response",
                self._format_code_block(result.response, "python")
            ))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_quality_section(self, results: Dict[str, Any]) -> str:
        """
        Generate quality analysis section.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Quality metrics markdown section
        """
        lines = ["## Quality Metrics\n"]
        
        # Add quality metrics if available
        summary = results.get("summary", {})
        
        lines.append(f"**Overall Success Rate:** {summary.get('success_rate', 0.0) * 100:.1f}%")
        lines.append(f"**Total Experiments:** {summary.get('total_experiments', 0)}")
        lines.append(f"**Successful Experiments:** {summary.get('successful_experiments', 0)}")
        lines.append(f"**Total Compressions:** {summary.get('total_compressions', 0)}")
        lines.append(f"**Successful Compressions:** {summary.get('successful_compressions', 0)}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_summary_section(self, results: Dict[str, Any]) -> str:
        """
        Generate summary and recommendations section.
        
        Args:
            results: Demo results dictionary
            
        Returns:
            Summary markdown section
        """
        summary = results.get("summary", {})
        
        lines = ["## Summary & Recommendations\n"]
        
        lines.append("### Performance Summary\n")
        lines.append(f"- **Best Model:** {summary.get('best_model', 'N/A')}")
        lines.append(f"- **Best Compression Strategy:** {summary.get('best_compression', 'N/A')}")
        lines.append("")
        
        lines.append("### Recommendations\n")
        lines.append("Based on the test results:")
        lines.append("")
        lines.append("1. **Model Selection:** Choose the model with the best performance for your use case")
        lines.append("2. **Compression:** Use compression strategies for queries exceeding token limits")
        lines.append("3. **Quality:** Monitor code quality metrics for production use")
        lines.append("")
        
        return "\n".join(lines)
    
    def _create_collapsible_section(self, title: str, content: str) -> str:
        """
        Create markdown collapsible section for long content.
        
        Args:
            title: Section title
            content: Section content
            
        Returns:
            Collapsible section HTML/markdown
            
        Example:
            ```python
            section = self._create_collapsible_section("Query", "Long query text...")
            ```
        """
        return f"""<details>
<summary>{title}</summary>

{content}

</details>"""
    
    def _format_code_block(self, content: str, language: str = "text") -> str:
        """
        Format content as a code block.
        
        Args:
            content: Content to format
            language: Programming language for syntax highlighting
            
        Returns:
            Formatted code block
            
        Example:
            ```python
            code = self._format_code_block("print('hello')", "python")
            ```
        """
        return f"```{language}\n{content}\n```"
