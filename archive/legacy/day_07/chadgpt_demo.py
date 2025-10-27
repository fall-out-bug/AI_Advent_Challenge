#!/usr/bin/env python3
"""
ChadGPT Multi-Agent System Demo.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import asyncio
import os
import time
from typing import Dict, List, Optional

import requests


class ChadGPTDemo:
    """ChadGPT Multi-Agent System Demo with Generator and Reviewer Agents."""

    def __init__(self):
        """Initialize the demo."""
        self.api_key_available = bool(os.getenv("CHADGPT_API_KEY"))
        self.api_key = os.getenv("CHADGPT_API_KEY")
        self.results: List[Dict] = []

    def _slow_print(self, text: str, delay: float = 0.05) -> None:
        """Print text slowly, line by line."""
        lines = text.split("\n")
        for line in lines:
            print(line)
            time.sleep(delay)

    async def run_demo(self) -> None:
        """Run the complete demo."""
        self._print_header()

        if not self.api_key_available:
            self._print_api_key_error()
            return

        tasks = self._get_demo_tasks()

        for i, task in enumerate(tasks, 1):
            print(f"\n🚀 Task {i}: {task['name']}")
            print("=" * 50)
            await self._process_task(task)
            if i < len(tasks):  # Don't pause after last task
                time.sleep(2.0)  # Pause between tasks

        self._print_summary()

    def _print_header(self) -> None:
        """Print demo header."""
        print("🌟 ChadGPT Multi-Agent System Demo")
        print("=" * 50)
        print("🧠 Featuring Generator & Reviewer Agents")
        print("=" * 50)
        print(
            f"🔑 ChadGPT API: {'✅ Available' if self.api_key_available else '❌ Not set'}"
        )

    def _print_api_key_error(self) -> None:
        """Print API key error message."""
        print("⚠️  This demo requires CHADGPT_API_KEY environment variable.")
        print("   Set it with: export CHADGPT_API_KEY='your-key'")

    def _get_demo_tasks(self) -> List[Dict]:
        """Get demo tasks."""
        return [
            {
                "name": "Simple Function",
                "description": "Create a function to calculate the factorial of a number",
                "complexity": "simple",
            },
            {
                "name": "Data Structure",
                "description": "Implement a simple stack data structure with push, pop, and peek operations",
                "complexity": "medium",
            },
            {
                "name": "Web API",
                "description": "Create a simple REST API endpoint for user registration",
                "complexity": "complex",
            },
        ]

    async def _process_task(self, task: Dict) -> None:
        """Process a single task."""
        print(f"📝 Description: {task['description']}")
        print(f"🎯 Complexity: {task['complexity']}")

        try:
            # Generate code with Generator Agent
            await self._generate_code(task)

        except Exception as e:
            print(f"❌ Task failed: {e}")
            self._record_failed_task(task)

    async def _generate_code(self, task: Dict) -> None:
        """Generate code for the task using Generator Agent."""
        print(f"\n⚡ Generator Agent: Creating code...")

        gen_prompt = f"Create a Python function for: {task['description']}"

        # Use correct ChadGPT API
        request_json = {"message": gen_prompt, "api_key": self.api_key}

        try:
            response = requests.post(
                url="https://ask.chadgpt.ru/api/public/gpt-4o-mini", json=request_json
            )

            if response.status_code == 200:
                resp_json = response.json()

                if resp_json["is_success"]:
                    gen_response = resp_json["response"]
                    used_words = resp_json["used_words_count"]

                    print(f"✅ Code generated successfully!")
                    print(f"📊 Tokens used: {used_words}")
                    time.sleep(0.5)  # Pause before showing code

                    # Show generated code
                    print(f"\n📝 Generated Code:")
                    print("-" * 40)
                    self._slow_print(gen_response, 0.03)
                    time.sleep(1.0)  # Pause before review

                    # Review code with Reviewer Agent
                    await self._review_code(task, gen_response)

                else:
                    print(f"❌ Code generation failed: {resp_json['error_message']}")
                    self._record_failed_task(task)
            else:
                print(f"❌ HTTP error: {response.status_code}")
                self._record_failed_task(task)

        except Exception as e:
            print(f"❌ Code generation failed: {e}")
            self._record_failed_task(task)

    async def _review_code(self, task: Dict, code: str) -> None:
        """Review the generated code using Reviewer Agent."""
        print(f"\n🔍 Reviewer Agent: Analyzing code...")

        # Limit code length for review to avoid API issues
        code_for_review = code[:2000] + "..." if len(code) > 2000 else code

        review_prompt = f"Review this Python code for quality, best practices, and potential improvements:\n\n{code_for_review}\n\nPlease provide a brief review with quality score (1-10)."

        # Use correct ChadGPT API
        request_json = {"message": review_prompt, "api_key": self.api_key}

        try:
            response = requests.post(
                url="https://ask.chadgpt.ru/api/public/gpt-4o-mini", json=request_json
            )

            if response.status_code == 200:
                resp_json = response.json()

                if resp_json["is_success"]:
                    review_response = resp_json["response"]
                    used_words = resp_json["used_words_count"]

                    print(f"✅ Code review completed!")
                    print(f"📊 Tokens used: {used_words}")
                    time.sleep(0.5)  # Pause before showing review

                    # Show review
                    print(f"\n📝 Code Review:")
                    print("-" * 40)
                    self._slow_print(review_response, 0.03)

                    # Parse quality score from review
                    quality_score = self._extract_quality_score(review_response)

                    # Parse issues and recommendations
                    issues_count, recommendations_count = self._parse_review_details(
                        review_response
                    )

                    self._record_successful_task(
                        task, quality_score, issues_count, recommendations_count
                    )

                else:
                    print(f"❌ Code review failed: {resp_json['error_message']}")
                    self._record_failed_task(task)
            else:
                print(f"❌ HTTP error: {response.status_code}")
                self._record_failed_task(task)

        except Exception as e:
            print(f"❌ Code review failed: {e}")
            self._record_failed_task(task)

    def _parse_review_details(self, review_text: str) -> tuple[int, int]:
        """Parse issues and recommendations count from review text."""
        try:
            issues_count = 0
            recommendations_count = 0

            lines = review_text.split("\n")
            for line in lines:
                if "issues:" in line.lower():
                    # Count bullet points or numbered items
                    issues_count = len(
                        [
                            l
                            for l in lines
                            if l.strip().startswith(("-", "•", "*", "1.", "2.", "3."))
                        ]
                    )
                elif "recommendations:" in line.lower():
                    recommendations_count = len(
                        [
                            l
                            for l in lines
                            if l.strip().startswith(("-", "•", "*", "1.", "2.", "3."))
                        ]
                    )

            return max(issues_count, 0), max(recommendations_count, 0)
        except:
            return 0, 0

    def _extract_quality_score(self, review_text: str) -> int:
        """Extract quality score from review text."""
        try:
            lines = review_text.split("\n")
            for line in lines:
                if "quality score" in line.lower() or "score:" in line.lower():
                    # Look for patterns like "Quality Score: 8/10" or "Score: 8"
                    import re

                    score_match = re.search(r"(\d+)/?10?", line)
                    if score_match:
                        return int(score_match.group(1))
            return 5  # Default score if not found
        except:
            return 5

    def _record_successful_task(
        self,
        task: Dict,
        quality_score: int,
        issues_count: int = 0,
        recommendations_count: int = 0,
    ) -> None:
        """Record successful task result."""
        self.results.append(
            {
                "task": task["name"],
                "complexity": task["complexity"],
                "success": True,
                "quality_score": quality_score,
                "issues_count": issues_count,
                "recommendations_count": recommendations_count,
            }
        )

    def _record_failed_task(self, task: Dict) -> None:
        """Record failed task result."""
        self.results.append(
            {
                "task": task["name"],
                "complexity": task["complexity"],
                "success": False,
                "quality_score": 0,
                "issues_count": 0,
                "recommendations_count": 0,
            }
        )

    def _print_summary(self) -> None:
        """Print demo summary."""
        print(f"\n🎉 Demo Summary")
        print("=" * 50)

        successful_tasks = [r for r in self.results if r["success"]]
        failed_tasks = [r for r in self.results if not r["success"]]

        print(f"📊 Tasks completed: {len(successful_tasks)}/{len(self.results)}")
        print(f"❌ Failed tasks: {len(failed_tasks)}")

        if successful_tasks:
            avg_quality = sum(r["quality_score"] for r in successful_tasks) / len(
                successful_tasks
            )
            avg_issues = sum(r["issues_count"] for r in successful_tasks) / len(
                successful_tasks
            )
            avg_recommendations = sum(
                r["recommendations_count"] for r in successful_tasks
            ) / len(successful_tasks)

            print(f"\n📈 Performance Metrics:")
            print(f"   Average quality score: {avg_quality:.1f}/10")
            print(f"   Average issues found: {avg_issues:.1f}")
            print(f"   Average recommendations: {avg_recommendations:.1f}")

            # Complexity analysis
            complexity_stats = {}
            for r in successful_tasks:
                complexity = r["complexity"]
                if complexity not in complexity_stats:
                    complexity_stats[complexity] = []
                complexity_stats[complexity].append(r)

            print(f"\n📊 Complexity Analysis:")
            for complexity, tasks in complexity_stats.items():
                avg_quality = sum(t["quality_score"] for t in tasks) / len(tasks)
                print(
                    f"   {complexity.capitalize()}: {len(tasks)} tasks, avg quality {avg_quality:.1f}/10"
                )

        if failed_tasks:
            print(f"\n❌ Failed Tasks:")
            for task in failed_tasks:
                print(f"   • {task['task']} ({task['complexity']})")

        print(f"\n💡 Key Features Demonstrated:")
        print(f"   • Generator Agent: Code generation with ChadGPT")
        print(f"   • Reviewer Agent: Comprehensive code review")
        print(f"   • Multi-agent workflow orchestration")
        print(f"   • Performance analysis and quality scoring")
        print(f"   • Full output display without truncation")

        print(f"\n🔧 Setup Requirements:")
        print(f"   • Set CHADGPT_API_KEY environment variable")
        print(f"   • Install required dependencies")
        print(f"   • Ensure ChadGPT API is accessible")


async def main():
    """Main function."""
    demo = ChadGPTDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
