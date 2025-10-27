#!/usr/bin/env python3
"""Day 09: MCP integration demonstration with human-readable report generation."""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add root to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

from src.presentation.mcp.client import MCPClient


class ReportGenerator:
    """Generate human-readable reports for MCP demo."""
    
    def __init__(self):
        """Initialize report generator."""
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, category: str, tool: str, status: str, details: Dict[str, Any]):
        """Add test result.
        
        Args:
            category: Test category
            tool: Tool name
            status: Test status (success/failed/skipped)
            details: Additional details
        """
        self.results.append({
            "category": category,
            "tool": tool,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
    
    def add_raw_data(self, tool: str, input_data: Dict[str, Any], output_data: Any):
        """Add raw input/output data for a tool.
        
        Args:
            tool: Tool name
            input_data: Input parameters
            output_data: Output result
        """
        # Add to the most recent result
        if self.results:
            self.results[-1]["details"]["raw_input"] = input_data
            self.results[-1]["details"]["raw_output"] = output_data
    
    def generate_text_report(self) -> str:
        """Generate text report.
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append(f"  🔥 Day 09 MCP Integration - Comprehensive Test Report")
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Duration: {self._calculate_duration()}\n")
        
        # Summary
        status_counts = {}
        for result in self.results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total = len(self.results)
        success_count = status_counts.get("success", 0)
        failed_count = status_counts.get("failed", 0)
        
        lines.append(f"Total Tests: {total}")
        lines.append(f"✓ Passed: {success_count}")
        lines.append(f"✗ Failed: {failed_count}")
        lines.append(f"Success Rate: {success_count/total*100:.1f}%")
        lines.append("")
        
        # Detailed results
        lines.append("Detailed Results:")
        lines.append("-" * 80)
        
        current_category = None
        for result in self.results:
            if result["category"] != current_category:
                current_category = result["category"]
                lines.append("")
                lines.append(f"## {current_category}")
                lines.append("-" * 80)
            
            status_icon = "✓" if result["status"] == "success" else "✗"
            lines.append(f"{status_icon} {result['tool']}: {result['status']}")
            
            details = result.get("details", {})
            if details.get("error"):
                lines.append(f"  Error: {details['error']}")
            elif details.get("result"):
                lines.append(f"  Result: {details['result']}")
        
        return "\n".join(lines)
    
    def generate_markdown_report(self) -> str:
        """Generate markdown report.
        
        Returns:
            Formatted markdown report
        """
        lines = []
        lines.append(f"# 🔥 Day 09 MCP Integration - Test Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**Duration:** {self._calculate_duration()}  ")
        lines.append("")
        
        # Summary table
        status_counts = {}
        for result in self.results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total = len(self.results)
        success_count = status_counts.get("success", 0)
        failed_count = status_counts.get("failed", 0)
        
        lines.append("## 📊 Test Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tests | {total} |")
        lines.append(f"| ✅ Passed | {success_count} |")
        lines.append(f"| ❌ Failed | {failed_count} |")
        lines.append(f"| Success Rate | {success_count/total*100:.1f}% |")
        lines.append("")
        
        # Detailed results by category
        lines.append("## 📝 Detailed Results")
        lines.append("")
        
        current_category = None
        for result in self.results:
            if result["category"] != current_category:
                current_category = result["category"]
                lines.append(f"### {current_category}")
                lines.append("")
            
            status_icon = "✅" if result["status"] == "success" else "❌"
            lines.append(f"{status_icon} **{result['tool']}**: {result['status']}")
            
            details = result.get("details", {})
            if "error" in details and details.get("error"):
                lines.append(f"  - **Error**: `{details['error']}`")
            elif "result" in details and details.get("result"):
                lines.append(f"  - **Result**: `{details['result']}`")
            elif "count" in details:
                lines.append(f"  - **Count**: {details['count']}")
            elif "local_models" in details:
                lines.append(f"  - **Local Models**: {details.get('local_models', 0)}")
                lines.append(f"  - **API Models**: {details.get('api_models', 0)}")
            
            # Add raw input/output if available
            if "raw_input" in details:
                lines.append("")
                lines.append("  **Raw Input:**")
                lines.append("  ```json")
                raw_input_str = json.dumps(details['raw_input'], indent=2)
                for line in raw_input_str.split('\n'):
                    lines.append(f"  {line}")
                lines.append("  ```")
            
            if "raw_output" in details:
                lines.append("  **Raw Output:**")
                lines.append("  ```json")
                raw_output_str = json.dumps(details['raw_output'], indent=2, default=str)
                # Truncate if too long
                if len(raw_output_str) > 1000:
                    raw_output_str = raw_output_str[:1000] + "\n  ... (truncated)"
                for line in raw_output_str.split('\n'):
                    lines.append(f"  {line}")
                lines.append("  ```")
            
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON report.
        
        Returns:
            Dictionary with report data
        """
        return {
            "timestamp": self.start_time.isoformat(),
            "duration": self._calculate_duration(),
            "summary": self._generate_summary(),
            "results": self.results,
        }
    
    def save_reports(self, output_dir: Path = Path("reports")):
        """Save reports to files.
        
        Args:
            output_dir: Directory to save reports
        """
        output_dir.mkdir(exist_ok=True)
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        
        # Save markdown report
        md_report = self.generate_markdown_report()
        md_file = output_dir / f"mcp_demo_report_{timestamp}.md"
        with open(md_file, "w") as f:
            f.write(md_report)
        print(f"\n✓ Markdown report saved: {md_file}")
        
        # Save text report
        text_report = self.generate_text_report()
        text_file = output_dir / f"mcp_demo_report_{timestamp}.txt"
        with open(text_file, "w") as f:
            f.write(text_report)
        print(f"✓ Text report saved: {text_file}")
        
        # Save JSON report
        json_report = self.generate_json_report()
        json_file = output_dir / f"mcp_demo_report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(json_report, f, indent=2)
        print(f"✓ JSON report saved: {json_file}")
        
        # Save summary
        summary = self._generate_summary()
        summary_file = output_dir / f"mcp_demo_summary_{timestamp}.txt"
        with open(summary_file, "w") as f:
            f.write(summary)
        print(f"✓ Summary saved: {summary_file}")
    
    def _calculate_duration(self) -> str:
        """Calculate test duration.
        
        Returns:
            Duration string
        """
        duration = datetime.now() - self.start_time
        return f"{duration.total_seconds():.2f}s"
    
    def _generate_summary(self) -> str:
        """Generate test summary.
        
        Returns:
            Summary string
        """
        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "success")
        
        return f"""Day 09 MCP Integration Test Summary
=======================================
Total Tests: {total}
Passed: {success}
Failed: {total - success}
Success Rate: {(success/total*100):.1f}%
Duration: {self._calculate_duration()}
"""


async def run_demo_with_reports():
    """Run MCP demo and generate reports."""
    print("=" * 80)
    print("Day 09 MCP Integration Test Suite")
    print("=" * 80)
    print()
    
    report = ReportGenerator()
    client = MCPClient()
    
    # Test calculators
    print("Testing Calculator Tools...")
    add_input = {"a": 15, "b": 27}
    add_result = await client.call_tool("add", add_input)
    status = "success" if isinstance(add_result, (int, float)) and add_result == 42 else "failed"
    report.add_result(
        "Calculator Tools",
        "add",
        status,
        {"result": add_result}
    )
    report.add_raw_data("add", add_input, add_result)
    
    multiply_input = {"a": 7, "b": 8}
    multiply_result = await client.call_tool("multiply", multiply_input)
    multiply_status = "success" if isinstance(multiply_result, (int, float)) and multiply_result == 56 else "failed"
    report.add_result(
        "Calculator Tools",
        "multiply",
        multiply_status,
        {"result": multiply_result}
    )
    report.add_raw_data("multiply", multiply_input, multiply_result)
    
    # Test model listing
    print("Testing Model SDK Tools...")
    models_input = {}
    models = await client.call_tool("list_models", models_input)
    local_count = len(models.get("local_models", []))
    api_count = len(models.get("api_models", []))
    
    report.add_result(
        "Model SDK Tools",
        "list_models",
        "success",
        {"local_models": local_count, "api_models": api_count}
    )
    report.add_raw_data("list_models", models_input, models)
    
    # Test token counting
    print("Testing Token Analysis...")
    token_input = {"text": "Hello world"}
    token_result = await client.call_tool("count_tokens", token_input)
    token_count = token_result.get("count", 0) if isinstance(token_result, dict) else 0
    
    report.add_result(
        "Token Analysis",
        "count_tokens",
        "success" if token_count >= 0 else "failed",
        {"count": token_count}
    )
    report.add_raw_data("count_tokens", token_input, token_result)
    
    # Test code generation with multiple models
    print("Testing Code Generation with Multiple Models...")
    models_to_test = ["mistral", "starcoder", "qwen"]
    
    for model_name in models_to_test:
        print(f"   Testing with model: {model_name}")
        try:
            gen_input = {
                "description": "Create a Python function to calculate factorial of n",
                "model": model_name
            }
            gen_result = await client.call_tool("generate_code", gen_input)
            
            success = gen_result.get("success", False) if isinstance(gen_result, dict) else False
            error_msg = gen_result.get("error", "Success") if isinstance(gen_result, dict) else str(gen_result)
            code_snippet = ""
            
            if success and isinstance(gen_result, dict):
                code_snippet = gen_result.get("code", "")[:100]
            
            report.add_result(
                "Agent Tools",
                f"generate_code_{model_name}",
                "success" if success else "failed",
                {
                    "model": model_name,
                    "success": success,
                    "error": error_msg,
                    "code_preview": code_snippet
                }
            )
            report.add_raw_data(f"generate_code_{model_name}", gen_input, gen_result)
        except Exception as e:
            print(f"   Error with {model_name}: {e}")
            report.add_result(
                "Agent Tools",
                f"generate_code_{model_name}",
                "failed",
                {"model": model_name, "error": str(e)}
            )
    
    # Test code review
    print("Testing Code Review...")
    try:
        review_input = {"code": "def hello(): pass", "model": "mistral"}
        review_result = await client.call_tool("review_code", review_input)
        success = review_result.get("success", False) if isinstance(review_result, dict) else False
        report.add_result(
            "Agent Tools",
            "review_code",
            "success" if success else "failed",
            {"success": success, "error": review_result.get("error", "") if isinstance(review_result, dict) and not success else ""}
        )
        report.add_raw_data("review_code", review_input, review_result)
    except Exception as e:
        report.add_result(
            "Agent Tools",
            "review_code",
            "failed",
            {"error": str(e)}
        )
    
    # Generate and display report
    print("\n" + "=" * 80)
    print("Test Complete - Generating Reports")
    print("=" * 80)
    print()
    
    text_report = report.generate_text_report()
    print(text_report)
    
    # Save reports
    report.save_reports()
    
    return 0


async def main():
    """Main entry point."""
    try:
        return await run_demo_with_reports()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

