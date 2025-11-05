#!/usr/bin/env python3
"""Script to test multi-pass code review on real homework archives.

Usage:
    python scripts/test_homework_review.py <archive_path> [--model mistral] [--token-budget 8000]
"""

import asyncio
import argparse
import sys
import zipfile
import tempfile
from pathlib import Path
from typing import Optional

# Add root to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.agents.multi_pass_reviewer import MultiPassReviewerAgent


def load_all_files_as_string(directory: Path, extensions: Optional[list] = None) -> str:
    """Load all files from directory as single string.

    Args:
        directory: Path to directory with files
        extensions: List of file extensions to include (None = all)

    Returns:
        Concatenated file contents
    """
    if extensions is None:
        extensions = [".py", ".yml", ".yaml", ".sh", ".txt", ".md", "Dockerfile"]

    content_parts = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            if any(
                file_path.suffix in ext or ext in str(file_path.name)
                for ext in extensions
            ):
                try:
                    rel_path = file_path.relative_to(directory)
                    content_parts.append(f"\n# File: {rel_path}\n")
                    content_parts.append(
                        file_path.read_text(encoding="utf-8", errors="ignore")
                    )
                    content_parts.append("\n\n")
                except Exception as e:
                    content_parts.append(f"# Error reading {file_path}: {e}\n\n")

    return "".join(content_parts)


def extract_archive(archive_path: str) -> Path:
    """Extract ZIP archive to temporary directory.

    Args:
        archive_path: Path to ZIP archive

    Returns:
        Path to temporary directory with extracted files
    """
    temp_dir = tempfile.mkdtemp(prefix="homework_review_")

    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    return Path(temp_dir)


async def test_homework_review(
    archive_path: str, model_name: str = "mistral", token_budget: int = 8000
):
    """Test multi-pass review on homework archive.

    Args:
        archive_path: Path to ZIP archive
        model_name: Model name to use (default: mistral)
        token_budget: Token budget for review
    """
    print(f"📦 Extracting archive: {archive_path}")
    temp_dir = extract_archive(archive_path)

    try:
        # Find root project directory
        root_dir = temp_dir
        # Check if there's a single subdirectory (common in student archives)
        subdirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        if len(subdirs) == 1:
            root_dir = subdirs[0]

        print(f"📁 Loading files from: {root_dir}")
        code = load_all_files_as_string(root_dir)

        print(f"📝 Loaded {len(code)} characters of code")
        print(f"🤖 Using model: {model_name}")
        print(f"💰 Token budget: {token_budget}")

        # Initialize client and agent
        client = UnifiedModelClient(timeout=300.0)
        agent = MultiPassReviewerAgent(client, token_budget=token_budget)

        # Determine repo name from archive
        repo_name = Path(archive_path).stem

        print("\n🚀 Starting multi-pass review...")
        print("=" * 60)

        report = await agent.process_multi_pass(code, repo_name=repo_name)

        print("=" * 60)
        print("\n✅ Review complete!")
        print(f"\n📊 Results:")
        print(f"  - Session ID: {report.session_id}")
        print(f"  - Detected Components: {', '.join(report.detected_components)}")
        print(f"  - Total Findings: {report.total_findings}")
        print(f"  - Execution Time: {report.execution_time_seconds:.2f}s")
        print(f"  - Pass 1: {'✅' if report.pass_1 else '❌'}")
        print(f"  - Pass 2: {len(report.pass_2_results)} components")
        print(f"  - Pass 3: {'✅' if report.pass_3 else '❌'}")

        # Save report
        output_file = Path(archive_path).parent / f"{repo_name}_review.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        print(f"\n💾 Report saved to: {output_file}")

        return report

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test multi-pass code review on homework archive"
    )
    parser.add_argument(
        "archive_path", type=str, help="Path to ZIP archive with homework"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistral",
        help="Model name to use (default: mistral)",
    )
    parser.add_argument(
        "--token-budget",
        type=int,
        default=8000,
        help="Token budget for review (default: 8000)",
    )

    args = parser.parse_args()

    if not Path(args.archive_path).exists():
        print(f"❌ Error: Archive not found: {args.archive_path}")
        sys.exit(1)

    try:
        await test_homework_review(
            args.archive_path, model_name=args.model, token_budget=args.token_budget
        )
    except Exception as e:
        print(f"\n❌ Error during review: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
