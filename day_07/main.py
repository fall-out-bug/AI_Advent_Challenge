#!/usr/bin/env python3
"""Main entry point for the StarCoder Multi-Agent System."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from communication.message_schema import OrchestratorRequest
from orchestrator import MultiAgentOrchestrator, process_simple_task


async def main():
    """Main function for running the multi-agent system."""
    parser = argparse.ArgumentParser(
        description="StarCoder Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a simple task
  python main.py --task "Create a function to calculate fibonacci numbers"
  
  # Run with custom requirements
  python main.py --task "Create a REST API client" --requirements "Use httpx" "Add retry logic"
  
  # Run multiple tasks
  python main.py --task "Create a sorting function" --task "Create a search function"
  
  # Run with custom orchestrator settings
  python main.py --task "Create a data processor" --generator-url http://localhost:9001 --reviewer-url http://localhost:9002
        """,
    )

    parser.add_argument(
        "--task", action="append", required=True, help="Task description(s) to process"
    )

    parser.add_argument(
        "--language", default="python", help="Programming language (default: python)"
    )

    parser.add_argument(
        "--requirements",
        action="append",
        default=[],
        help="Additional requirements for the task",
    )

    parser.add_argument(
        "--generator-url",
        default="http://localhost:9001",
        help="URL of the generator agent (default: http://localhost:9001)",
    )

    parser.add_argument(
        "--reviewer-url",
        default="http://localhost:9002",
        help="URL of the reviewer agent (default: http://localhost:9002)",
    )

    parser.add_argument(
        "--results-dir",
        default="results",
        help="Directory to save results (default: results)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple task processing (single task only)",
    )

    args = parser.parse_args()

    if args.verbose:
        print("🌟 StarCoder Multi-Agent System")
        print("=" * 50)
        print(f"Tasks: {len(args.task)}")
        print(f"Language: {args.language}")
        print(f"Requirements: {args.requirements}")
        print(f"Generator URL: {args.generator_url}")
        print(f"Reviewer URL: {args.reviewer_url}")
        print(f"Results directory: {args.results_dir}")
        print()

    # Process tasks
    if args.simple and len(args.task) == 1:
        # Use simple processing for single task
        if args.verbose:
            print(f"🔄 Processing simple task: {args.task[0]}")

        try:
            result = await process_simple_task(
                task_description=args.task[0],
                language=args.language,
                requirements=args.requirements,
            )

            if result.success:
                print("✅ Task completed successfully!")
                print(f"⏱️  Workflow time: {result.workflow_time:.2f}s")
                print(
                    f"📊 Code quality score: {result.review_result.code_quality_score}/10"
                )

                if args.verbose:
                    print("\n📝 Generated Code:")
                    print("-" * 30)
                    print(result.generation_result.generated_code)

                    print("\n🧪 Generated Tests:")
                    print("-" * 30)
                    print(result.generation_result.tests)

                    print("\n🔍 Review Issues:")
                    print("-" * 30)
                    for issue in result.review_result.issues:
                        print(f"• {issue}")

                    print("\n💡 Recommendations:")
                    print("-" * 30)
                    for rec in result.review_result.recommendations:
                        print(f"• {rec}")
            else:
                print(f"❌ Task failed: {result.error_message}")
                return 1

        except Exception as e:
            print(f"❌ Error processing task: {str(e)}")
            return 1

    else:
        # Use orchestrator for multiple tasks or advanced processing
        orchestrator = MultiAgentOrchestrator(
            generator_url=args.generator_url,
            reviewer_url=args.reviewer_url,
            results_dir=args.results_dir,
        )

        results = []

        for i, task in enumerate(args.task, 1):
            if args.verbose:
                print(f"🔄 Processing task {i}/{len(args.task)}: {task}")

            request = OrchestratorRequest(
                task_description=task,
                language=args.language,
                requirements=args.requirements,
            )

            try:
                result = await orchestrator.process_task(request)
                results.append(result)

                if result.success:
                    print(
                        f"✅ Task {i} completed - Quality: {result.review_result.code_quality_score}/10"
                    )
                else:
                    print(f"❌ Task {i} failed: {result.error_message}")

            except Exception as e:
                print(f"❌ Task {i} error: {str(e)}")
                results.append(None)

        # Summary
        successful = sum(1 for r in results if r and r.success)
        total = len(results)

        if args.verbose:
            avg_quality = (
                sum(
                    r.review_result.code_quality_score
                    for r in results
                    if r and r.success
                )
                / successful
                if successful > 0
                else 0
            )

            print(f"\n📊 Summary:")
            print(f"• Tasks completed: {successful}/{total}")
            print(f"• Average quality score: {avg_quality:.1f}/10")
            print(f"• Results saved in: {orchestrator.results_dir}")

            # Show detailed results for each task
            for i, result in enumerate(results, 1):
                if result and result.success:
                    print(f"\n📋 Task {i} Details:")
                    print(f"• Quality: {result.review_result.code_quality_score}/10")
                    print(f"• Issues: {len(result.review_result.issues)}")
                    print(
                        f"• Recommendations: {len(result.review_result.recommendations)}"
                    )
                    print(f"• Workflow time: {result.workflow_time:.2f}s")

        if successful == 0:
            print("❌ No tasks completed successfully")
            return 1
        elif successful < total:
            print(f"⚠️  {successful}/{total} tasks completed successfully")
            return 1
        else:
            print("🎉 All tasks completed successfully!")
            return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
