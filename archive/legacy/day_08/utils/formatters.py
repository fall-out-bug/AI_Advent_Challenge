"""
Text formatting utilities for console output.

This module provides formatting utilities for displaying
experiment results and analysis in a readable format.
"""

import textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from models.data_models import CompressionResult, ExperimentResult


@dataclass
class FormatConfig:
    """Configuration for text formatting."""

    max_width: int = 80
    indent_size: int = 2
    table_padding: int = 2
    decimal_places: int = 2
    use_colors: bool = True


class TextFormatter:
    """Text formatter for console output."""

    def __init__(self, config: Optional[FormatConfig] = None):
        """Initialize text formatter."""
        self.config = config or FormatConfig()

    def format_title(self, title: str, char: str = "=") -> str:
        """Format title with border."""
        border = char * len(title)
        return f"\n{border}\n{title}\n{border}\n"

    def format_section(self, title: str, char: str = "-") -> str:
        """Format section header."""
        return f"\n{title}\n{char * len(title)}\n"

    def format_key_value(self, key: str, value: Any, indent: int = 0) -> str:
        """Format key-value pair."""
        indent_str = " " * (indent * self.config.indent_size)
        return f"{indent_str}{key}: {value}\n"

    def format_percentage(self, value: float) -> str:
        """Format percentage value."""
        return f"{value:.{self.config.decimal_places}%}"

    def format_number(self, value: float, suffix: str = "") -> str:
        """Format number with suffix."""
        return f"{value:.{self.config.decimal_places}f}{suffix}"

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds."""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"

    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Format data as table."""
        if not headers or not rows:
            return ""

        # Calculate column widths
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + self.config.table_padding)

        # Format table
        result = []

        # Header
        header_line = "|"
        separator_line = "|"
        for i, header in enumerate(headers):
            header_line += f" {header:<{col_widths[i]-1}}|"
            separator_line += f"{'-' * (col_widths[i]-1)}|"

        result.append(header_line)
        result.append(separator_line)

        # Rows
        for row in rows:
            row_line = "|"
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    row_line += f" {str(cell):<{col_widths[i]-1}}|"
            result.append(row_line)

        return "\n".join(result)

    def format_list(self, items: List[str], bullet: str = "•") -> str:
        """Format list of items."""
        if not items:
            return ""

        result = []
        for item in items:
            result.append(f"{bullet} {item}")

        return "\n".join(result)

    def wrap_text(self, text: str, width: Optional[int] = None) -> str:
        """Wrap text to specified width."""
        width = width or self.config.max_width
        return textwrap.fill(text, width=width)

    def format_experiment_result(self, result: ExperimentResult) -> str:
        """Format single experiment result."""
        lines = []

        lines.append(f"Experiment: {result.experiment_name}")
        lines.append(f"Model: {result.model_name}")
        lines.append(f"Success: {'✓' if result.success else '✗'}")

        if result.response_time is not None:
            lines.append(f"Response Time: {self.format_duration(result.response_time)}")

        lines.append(f"Total Tokens: {result.total_tokens}")
        lines.append(f"Output Tokens: {result.output_tokens}")

        if result.estimated_cost > 0:
            lines.append(
                f"Estimated Cost: ${self.format_number(result.estimated_cost)}"
            )

        if result.compression_result:
            comp = result.compression_result
            lines.append(f"Compression Strategy: {comp.strategy_used}")
            lines.append(
                f"Compression Ratio: {self.format_percentage(comp.compression_ratio)}"
            )
            lines.append(
                f"Tokens Saved: {comp.original_tokens - comp.compressed_tokens}"
            )

        if result.error_message:
            lines.append(f"Error: {result.error_message}")

        return "\n".join(lines)

    def format_compression_result(self, result: CompressionResult) -> str:
        """Format compression result."""
        lines = []

        lines.append(f"Strategy: {result.strategy_used}")
        lines.append(f"Original Tokens: {result.original_tokens}")
        lines.append(f"Compressed Tokens: {result.compressed_tokens}")
        lines.append(
            f"Compression Ratio: {self.format_percentage(result.compression_ratio)}"
        )
        lines.append(
            f"Tokens Saved: {result.original_tokens - result.compressed_tokens}"
        )

        return "\n".join(lines)


class ConsoleFormatter:
    """Console-specific formatter with colors and styling."""

    def __init__(self, config: Optional[FormatConfig] = None):
        """Initialize console formatter."""
        self.config = config or FormatConfig()
        self.formatter = TextFormatter(config)
        self.colors = self._init_colors()

    def _init_colors(self) -> Dict[str, str]:
        """Initialize color codes."""
        if not self.config.use_colors:
            return {
                key: ""
                for key in [
                    "reset",
                    "bold",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "cyan",
                    "magenta",
                ]
            }

        return {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "cyan": "\033[36m",
            "magenta": "\033[35m",
        }

    def colorize(self, text: str, color: str) -> str:
        """Add color to text."""
        if color not in self.colors:
            return text
        return f"{self.colors[color]}{text}{self.colors['reset']}"

    def format_success(self, text: str) -> str:
        """Format success message."""
        return self.colorize(text, "green")

    def format_error(self, text: str) -> str:
        """Format error message."""
        return self.colorize(text, "red")

    def format_warning(self, text: str) -> str:
        """Format warning message."""
        return self.colorize(text, "yellow")

    def format_info(self, text: str) -> str:
        """Format info message."""
        return self.colorize(text, "blue")

    def format_highlight(self, text: str) -> str:
        """Format highlighted text."""
        return self.colorize(text, "bold")

    def format_title(self, title: str, char: str = "=") -> str:
        """Format title with colors."""
        colored_title = self.colorize(title, "bold")
        return self.formatter.format_title(colored_title, char)

    def format_section(self, title: str, char: str = "-") -> str:
        """Format section with colors."""
        colored_title = self.colorize(title, "cyan")
        return self.formatter.format_section(colored_title, char)

    def format_key_value(self, key: str, value: Any, indent: int = 0) -> str:
        """Format key-value with colors."""
        colored_key = self.colorize(key, "bold")
        return self.formatter.format_key_value(colored_key, value, indent)

    def format_experiment_summary(self, results: List[ExperimentResult]) -> str:
        """Format experiment summary."""
        if not results:
            return self.format_error("No experiment results to display")

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        lines = []
        lines.append(self.format_title("Experiment Summary"))

        lines.append(self.format_key_value("Total Experiments", len(results)))
        lines.append(self.format_key_value("Successful", len(successful)))
        lines.append(self.format_key_value("Failed", len(failed)))

        if results:
            success_rate = len(successful) / len(results)
            lines.append(
                self.format_key_value(
                    "Success Rate", self.format_percentage(success_rate)
                )
            )

            avg_time = sum(
                r.response_time for r in results if r.response_time is not None
            ) / len(results)
            lines.append(
                self.format_key_value(
                    "Average Response Time", self.formatter.format_duration(avg_time)
                )
            )

        return "\n".join(lines)

    def format_compression_summary(self, results: List[CompressionResult]) -> str:
        """Format compression summary."""
        if not results:
            return self.format_error("No compression results to display")

        lines = []
        lines.append(self.format_title("Compression Summary"))

        avg_ratio = sum(r.compression_ratio for r in results) / len(results)
        total_saved = sum(r.original_tokens - r.compressed_tokens for r in results)

        lines.append(
            self.format_key_value(
                "Average Compression Ratio", self.format_percentage(avg_ratio)
            )
        )
        lines.append(self.format_key_value("Total Tokens Saved", total_saved))

        # Strategy breakdown
        strategies = {}
        for result in results:
            strategy = result.strategy_used
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(result)

        lines.append(self.format_section("Strategy Breakdown"))
        for strategy, strategy_results in strategies.items():
            strategy_avg = sum(r.compression_ratio for r in strategy_results) / len(
                strategy_results
            )
            lines.append(
                self.format_key_value(
                    f"{strategy.title()} Strategy",
                    f"{len(strategy_results)} experiments, "
                    f"avg ratio: {self.format_percentage(strategy_avg)}",
                )
            )

        return "\n".join(lines)

    def format_recommendations(self, results: List[ExperimentResult]) -> str:
        """Format recommendations based on results."""
        if not results:
            return self.format_error("No results to generate recommendations")

        lines = []
        lines.append(self.format_title("Recommendations"))

        # Analyze results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if len(failed) > len(successful):
            lines.append(
                self.format_warning("⚠️  High failure rate detected. Consider:")
            )
            lines.append("  • Checking model availability")
            lines.append("  • Reducing query complexity")
            lines.append("  • Increasing timeout values")

        # Compression recommendations
        compression_results = [
            r.compression_result for r in results if r.compression_result
        ]
        if compression_results:
            avg_ratio = sum(r.compression_ratio for r in compression_results) / len(
                compression_results
            )
            if avg_ratio < 0.5:
                lines.append(
                    self.format_info("💡 Good compression achieved. Consider:")
                )
                lines.append("  • Using more aggressive compression strategies")
                lines.append("  • Optimizing for specific use cases")
            elif avg_ratio > 0.8:
                lines.append(self.format_warning("⚠️  Low compression ratio. Consider:"))
                lines.append("  • Using different compression strategies")
                lines.append("  • Adjusting compression parameters")

        # Performance recommendations
        response_times = [
            r.response_time for r in results if r.response_time is not None
        ]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            if avg_time > 10:
                lines.append(
                    self.format_warning("⚠️  Slow response times detected. Consider:")
                )
                lines.append("  • Using faster models")
                lines.append("  • Implementing caching")
                lines.append("  • Optimizing queries")

        return "\n".join(lines)
