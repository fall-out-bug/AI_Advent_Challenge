"""
Report generator for testing local models.

Creates Markdown reports with model testing results on riddles.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .constants import REPORT_FILENAME_PREFIX, REPORT_TIMESTAMP_FORMAT, DISPLAY_TIMESTAMP_FORMAT

# Use absolute imports for script execution
try:
    from .model_client import ModelTestResult
    from .riddles import RiddleAnalyzer
except ImportError:
    # If relative imports don't work, use absolute imports
    from model_client import ModelTestResult
    from riddles import RiddleAnalyzer


@dataclass
class ComparisonResult:
    """Model response comparison result."""
    riddle_title: str
    model_name: str
    direct_answer: str
    stepwise_answer: str
    word_difference: int
    direct_analysis: Dict[str, Any]
    stepwise_analysis: Dict[str, Any]
    direct_response_time: float
    stepwise_response_time: float
    riddle_text: str = ""


class ReportGenerator:
    """Report generator for model testing."""
    
    def __init__(self):
        """Initialize report generator."""
        self.analyzer = RiddleAnalyzer()
    
    def generate_comparison_results(
        self, 
        test_results: List[ModelTestResult],
        riddle_titles: List[str],
        riddle_texts: List[str] = None
    ) -> List[ComparisonResult]:
        """
        Generate comparison results.
        
        Args:
            test_results: Test results
            riddle_titles: Riddle titles
            riddle_texts: Riddle texts (optional)
            
        Returns:
            List[ComparisonResult]: Comparison results
        """
        comparison_results = []
        
        for i, result in enumerate(test_results):
            # Analyze direct answer
            direct_analysis = self.analyzer.analyze_response(result.direct_answer)
            
            # Analyze stepwise answer
            stepwise_analysis = self.analyzer.analyze_response(result.stepwise_answer)
            
            # Calculate word difference
            word_difference = stepwise_analysis["word_count"] - direct_analysis["word_count"]
            
            # Get riddle text if available
            riddle_text = ""
            if riddle_texts and i < len(riddle_texts):
                riddle_text = riddle_texts[i % len(riddle_texts)]
            
            comparison_result = ComparisonResult(
                riddle_title=riddle_titles[i % len(riddle_titles)],
                model_name=result.model_name,
                direct_answer=result.direct_answer,
                stepwise_answer=result.stepwise_answer,
                word_difference=word_difference,
                direct_analysis=direct_analysis,
                stepwise_analysis=stepwise_analysis,
                direct_response_time=result.direct_response_time,
                stepwise_response_time=result.stepwise_response_time,
                riddle_text=riddle_text
            )
            
            comparison_results.append(comparison_result)
        
        return comparison_results
    
    def generate_markdown_report(
        self, 
        comparison_results: List[ComparisonResult]
    ) -> str:
        """
        Generate Markdown report.
        
        Args:
            comparison_results: Comparison results
            
        Returns:
            str: Markdown report
        """
        timestamp = datetime.now().strftime(DISPLAY_TIMESTAMP_FORMAT)
        
        report = f"""# Model Testing on Logical Riddles

**Testing Date:** {timestamp}

## General Statistics

- **Total Tests:** {len(comparison_results)}
- **Number of Models:** {len(set(r.model_name for r in comparison_results))}
- **Number of Riddles:** {len(set(r.riddle_title for r in comparison_results))}

"""
        
        # Add detailed analysis
        report += self._generate_detailed_analysis(comparison_results)
        
        # Add statistics
        report += self._generate_statistics(comparison_results)
        
        return report
    
    def _generate_detailed_analysis(self, results: List[ComparisonResult]) -> str:
        """
        Generate detailed analysis.
        
        Following Python Zen: "Flat is better than nested"
        and "Simple is better than complex".
        """
        analysis = "\n## Detailed Analysis\n\n"
        
        for result in results:
            analysis += self._generate_single_result_analysis(result)
        
        return analysis
    
    def _generate_single_result_analysis(self, result: ComparisonResult) -> str:
        """
        Generate analysis for a single result.
        
        Args:
            result: Comparison result to analyze
            
        Returns:
            str: Analysis text for the result
        """
        analysis = f"### {result.riddle_title} - {result.model_name}\n\n"
        
        analysis += self._add_riddle_text_if_available(result)
        analysis += self._generate_direct_answer_analysis(result)
        analysis += self._generate_stepwise_answer_analysis(result)
        analysis += self._generate_full_answers_section(result)
        
        return analysis + "---\n\n"
    
    def _add_riddle_text_if_available(self, result: ComparisonResult) -> str:
        """Add riddle text if available."""
        if not result.riddle_text:
            return ""
        return f"**Riddle:**\n{result.riddle_text}\n\n"
    
    def _generate_direct_answer_analysis(self, result: ComparisonResult) -> str:
        """Generate direct answer analysis section."""
        analysis = "**Direct Answer:**\n"
        analysis += f"- Word count: {result.direct_analysis['word_count']}\n"
        analysis += f"- Logical keywords: {result.direct_analysis['logical_keywords_count']}\n"
        
        step_structure = 'Yes' if result.direct_analysis['has_step_by_step'] else 'No'
        analysis += f"- Step-by-step structure: {step_structure}\n"
        analysis += f"- Response time: {result.direct_response_time:.2f}s\n\n"
        
        return analysis
    
    def _generate_stepwise_answer_analysis(self, result: ComparisonResult) -> str:
        """Generate stepwise answer analysis section."""
        analysis = "**Stepwise Answer:**\n"
        analysis += f"- Word count: {result.stepwise_analysis['word_count']}\n"
        analysis += f"- Logical keywords: {result.stepwise_analysis['logical_keywords_count']}\n"
        
        step_structure = 'Yes' if result.stepwise_analysis['has_step_by_step'] else 'No'
        analysis += f"- Step-by-step structure: {step_structure}\n"
        analysis += f"- Response time: {result.stepwise_response_time:.2f}s\n"
        analysis += f"- Word difference: {result.word_difference:+d}\n\n"
        
        return analysis
    
    def _generate_full_answers_section(self, result: ComparisonResult) -> str:
        """Generate full answers section."""
        analysis = "**Full Answers:**\n\n"
        analysis += f"*Direct:*\n```\n{result.direct_answer}\n```\n\n"
        analysis += f"*Stepwise:*\n```\n{result.stepwise_answer}\n```\n\n"
        
        return analysis
    
    def _generate_statistics(self, results: List[ComparisonResult]) -> str:
        """Generate statistics."""
        if not results:
            return ""
        
        # Statistics by models
        models = set(result.model_name for result in results)
        model_stats = {}
        
        for model in models:
            model_results = [r for r in results if r.model_name == model]
            avg_word_diff = sum(r.word_difference for r in model_results) / len(model_results)
            avg_direct_time = sum(r.direct_response_time for r in model_results) / len(model_results)
            avg_stepwise_time = sum(r.stepwise_response_time for r in model_results) / len(model_results)
            
            model_stats[model] = {
                "avg_word_diff": avg_word_diff,
                "avg_direct_time": avg_direct_time,
                "avg_stepwise_time": avg_stepwise_time,
                "total_tests": len(model_results)
            }
        
        stats = "## Statistics\n\n"
        
        # General statistics
        total_word_diff = sum(r.word_difference for r in results)
        avg_word_diff = total_word_diff / len(results)
        avg_direct_time = sum(r.direct_response_time for r in results) / len(results)
        avg_stepwise_time = sum(r.stepwise_response_time for r in results) / len(results)
        
        stats += f"- **Total Tests:** {len(results)}\n"
        stats += f"- **Average Word Difference:** {avg_word_diff:.1f}\n"
        stats += f"- **Average Direct Response Time:** {avg_direct_time:.2f}s\n"
        stats += f"- **Average Stepwise Response Time:** {avg_stepwise_time:.2f}s\n\n"
        
        # Statistics by models
        stats += "### Statistics by Models\n\n"
        for model, stat in model_stats.items():
            stats += f"**{model}:**\n"
            stats += f"- Number of tests: {stat['total_tests']}\n"
            stats += f"- Average word difference: {stat['avg_word_diff']:.1f}\n"
            stats += f"- Average direct response time: {stat['avg_direct_time']:.2f}s\n"
            stats += f"- Average stepwise response time: {stat['avg_stepwise_time']:.2f}s\n\n"
        
        return stats
    
    def save_report(self, report: str, filename: str = None) -> str:
        """
        Save report to file.
        
        Args:
            report: Report text
            filename: Filename (optional)
            
        Returns:
            str: Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime(REPORT_TIMESTAMP_FORMAT)
            filename = f"{REPORT_FILENAME_PREFIX}{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename
