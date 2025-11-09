#!/usr/bin/env python3
"""Smoke-test script for the modular homework review service."""

import argparse
import asyncio
import sys
import zipfile
from pathlib import Path

_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from multipass_reviewer.application.config import ReviewConfig

from shared_package.clients.unified_client import UnifiedModelClient

from src.application.services.modular_review_service import ModularReviewService
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging.review_logger import ReviewLogger


async def test_homework_review(
    archive_path: str, model_name: str = "mistral", token_budget: int = 8000
):
    """Test modular review on homework archive."""

    archive_path_obj = Path(archive_path)
    if not archive_path_obj.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    print(f"📦 Archive: {archive_path}")
    with zipfile.ZipFile(archive_path, "r") as zip_ref:
        files = [name for name in zip_ref.namelist() if not name.endswith("/")]
        print(f"🗂  Files inside archive: {len(files)}")

    settings = get_settings()
    archive_service = ZipArchiveService(settings)
    diff_analyzer = DiffAnalyzer()
    review_config = ReviewConfig(token_budget=token_budget)
    review_logger = ReviewLogger(enabled=True)

    unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)
    service = ModularReviewService(
        archive_service=archive_service,
        diff_analyzer=diff_analyzer,
        llm_client=unified_client,
        review_config=review_config,
        review_logger=review_logger,
        settings=settings,
    )

    repo_name = archive_path_obj.stem
    student_id = f"smoke::{repo_name}"

    print(f"🤖 Model alias: {model_name}")
    print(f"💰 Token budget: {token_budget}")
    print("\n🚀 Starting modular review...\n" + "=" * 60)

    try:
        report = await service.review_submission(
            new_archive_path=str(archive_path_obj),
            previous_archive_path=None,
            assignment_id=repo_name,
            student_id=student_id,
        )
    finally:
        await unified_client.close()

    print("=" * 60)
    print("\n✅ Review complete!")
    print("\n📊 Results:")
    print(f"  - Session ID: {report.session_id}")
    print(f"  - Detected Components: {', '.join(report.detected_components)}")
    print(f"  - Total Findings: {report.total_findings}")
    print(f"  - Execution Time: {report.execution_time_seconds:.2f}s")
    print(f"  - Pass 1: {'✅' if report.pass_1 else '❌'}")
    print(f"  - Pass 2 components: {list(report.pass_2_results.keys())}")
    print(f"  - Pass 3: {'✅' if report.pass_3 else '❌'}")

    output_file = archive_path_obj.parent / f"{repo_name}_review.md"
    output_file.write_text(report.to_markdown(), encoding="utf-8")
    print(f"\n💾 Report saved to: {output_file}")

    return report


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
