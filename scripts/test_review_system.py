"""Script to test review system end-to-end.

Purpose:
    Comprehensive test of review system:
    1. Check MongoDB connection
    2. Test archive extraction
    3. Test diff analysis
    4. Test use cases
    5. Test full pipeline with ModularReviewService-backed reviewer
"""

import asyncio
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# Add src and shared to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

# Try to import UnifiedModelClient
try:
    from shared_package.clients.unified_client import UnifiedModelClient
except ImportError:
    try:
        from shared.clients.unified_client import UnifiedModelClient
    except ImportError:
        shared_package_path = _root / "shared" / "shared_package"
        if shared_package_path.exists():
            sys.path.insert(0, str(shared_package_path.parent))
            from shared_package.clients.unified_client import UnifiedModelClient
        else:
            UnifiedModelClient = None

from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.application.use_cases.review_submission_use_case import (
    ReviewSubmissionUseCase,
)
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.clients.external_api_client import ExternalAPIClient
from src.infrastructure.clients.external_api_mock import (
    ExternalAPIClientMock,
)
from src.infrastructure.logs.log_normalizer import LogNormalizer
from src.infrastructure.logs.log_parser_impl import LogParserImpl
from src.infrastructure.logs.llm_log_analyzer import LLMLogAnalyzer
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.repositories.long_tasks_repository import (
    LongTasksRepository,
)


def create_test_zip(zip_path: str, files: dict[str, str]) -> None:
    """Create test ZIP archive.

    Args:
        zip_path: Path to create ZIP
        files: Dictionary mapping file paths to content
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)


async def test_mongodb_connection() -> bool:
    """Test MongoDB connection.

    Returns:
        True if connection successful
    """
    try:
        db = await get_db()
        # Use client to ping, not db.admin
        from src.infrastructure.database.mongo import get_client
        client = await get_client()
        await client.admin.command("ping")
        print("✅ MongoDB connection: OK")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection: FAILED - {e}")
        return False


async def test_archive_extraction() -> bool:
    """Test archive extraction.

    Returns:
        True if extraction successful
    """
    try:
        settings = get_settings()
        service = ZipArchiveService(settings)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "test.zip")
            create_test_zip(
                zip_path,
                {
                    "main.py": "def hello():\n    print('world')",
                    "utils.py": "def helper():\n    pass",
                },
            )

            archive = service.extract_submission(zip_path, "test_submission")
            assert len(archive.code_files) == 2
            assert "main.py" in archive.code_files
            print("✅ Archive extraction: OK")
            return True
    except Exception as e:
        print(f"❌ Archive extraction: FAILED - {e}")
        return False


def test_diff_analysis() -> bool:
    """Test diff analysis.

    Returns:
        True if analysis successful
    """
    try:
        analyzer = DiffAnalyzer()
        old_code = "def old():\n    pass"
        new_code = "def old():\n    pass\ndef new():\n    pass"

        diff = analyzer.analyze(old_code, new_code)
        assert diff.lines_added > 0
        assert "new" in diff.functions_added
        print("✅ Diff analysis: OK")
        return True
    except Exception as e:
        print(f"❌ Diff analysis: FAILED - {e}")
        return False


async def test_use_cases() -> bool:
    """Test use cases with real MongoDB.

    Returns:
        True if use cases work
    """
    try:
        db = await get_db()
        tasks_repo = LongTasksRepository(db)
        review_repo = HomeworkReviewRepository(db)

        # Test enqueue
        enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
        task = await enqueue_use_case.execute(
            student_id="999",
            assignment_id="HW_TEST",
            new_submission_path="/test/path.zip",
            new_commit="commit_hw_test",
        )
        assert task.task_id is not None
        assert task.task_type.value == "code_review"
        print("✅ Enqueue use case: OK")

        # Test get by id
        retrieved = await tasks_repo.get_by_id(task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == task.task_id
        print("✅ Repository get_by_id: OK")

        # Cleanup
        await db.long_tasks.delete_one({"task_id": task.task_id})
        print("✅ Use cases: OK")
        return True
    except Exception as e:
        print(f"❌ Use cases: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline() -> bool:
    """Test full review pipeline with modular multipass reviewer.

    Purpose:
        Tests complete review pipeline with real UnifiedModelClient.
        Requires LLM_URL to be configured in settings.

    Returns:
        True if pipeline works
    """
    if UnifiedModelClient is None:
        print("⚠️  UnifiedModelClient not available, skipping full pipeline test")
        return False

    try:
        settings = get_settings()
        llm_url = settings.llm_url or os.getenv("LLM_URL")
        if not llm_url:
            print("⚠️  LLM_URL not configured, skipping full pipeline test")
            print("   Set LLM_URL environment variable to test with real LLM")
            return False

        db = await get_db()
        tasks_repo = LongTasksRepository(db)
        review_repo = HomeworkReviewRepository(db)

        # Create test archives
        with tempfile.TemporaryDirectory() as tmpdir:
            old_zip = os.path.join(tmpdir, "old.zip")
            new_zip = os.path.join(tmpdir, "new.zip")
            create_test_zip(old_zip, {"main.py": "def old(): pass"})
            create_test_zip(
                new_zip,
                {
                    "main.py": "def old():\n    pass\ndef new(): pass",
                    "test.py": "def test(): pass",
                },
            )

            # Setup
            archive_service = ZipArchiveService(settings)
            diff_analyzer = DiffAnalyzer()
            log_parser = LogParserImpl()
            log_normalizer = LogNormalizer()

            # Set LLM_URL in environment for UnifiedModelClient
            if not os.getenv("LLM_URL"):
                os.environ["LLM_URL"] = llm_url

            unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)
            log_analyzer = LLMLogAnalyzer(
                unified_client=unified_client,
                timeout=settings.review_llm_timeout,
            )

            # Use real external API client if configured, otherwise mock
            if settings.external_api_enabled and settings.external_api_url:
                try:
                    publisher = ExternalAPIClient(settings)
                    print("✅ Using real External API client")
                except ValueError:
                    publisher = ExternalAPIClientMock(settings)
                    print("⚠️  External API not fully configured, using mock")
            else:
                publisher = ExternalAPIClientMock(settings)
                print("⚠️  External API disabled, using mock")

            review_use_case = ReviewSubmissionUseCase(
                archive_reader=archive_service,
                diff_analyzer=diff_analyzer,
                unified_client=unified_client,
                review_repository=review_repo,
                tasks_repository=tasks_repo,
                publisher=publisher,
                log_parser=log_parser,
                log_normalizer=log_normalizer,
                log_analyzer=log_analyzer,
                settings=settings,
            )

            # Enqueue task
            enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
            task = await enqueue_use_case.execute(
                student_id="888",
                assignment_id="HW_PIPELINE",
                new_submission_path=new_zip,
                previous_submission_path=old_zip,
                new_commit="commit_pipeline",
            )

            # Process task
            session_id = await review_use_case.execute(task)

            # Verify
            completed = await tasks_repo.get_by_id(task.task_id)
            assert completed.status.value == "succeeded"
            assert completed.result_text == session_id

            session = await review_repo.get_review_session(session_id)
            assert session is not None
            assert "report" in session

            # Cleanup
            await db.long_tasks.delete_one({"task_id": task.task_id})
            await db.homework_reviews.delete_one({"session_id": session_id})

            print("✅ Full pipeline: OK")
            return True
    except Exception as e:
        print(f"❌ Full pipeline: FAILED - {e}")
        import traceback

        traceback.print_exc()
        return False


async def main() -> None:
    """Run all tests."""
    print("=" * 60)
    print("Review System Health Check")
    print("=" * 60)
    print()

    results = []

    # 1. MongoDB
    results.append(("MongoDB", await test_mongodb_connection()))
    print()

    # 2. Archive extraction
    results.append(("Archive Extraction", await test_archive_extraction()))
    print()

    # 3. Diff analysis
    results.append(("Diff Analysis", test_diff_analysis()))
    print()

    # 4. Use cases (requires MongoDB)
    if results[0][1]:  # If MongoDB is OK
        results.append(("Use Cases", await test_use_cases()))
        print()

        # 5. Full pipeline (requires MongoDB + LLM)
        results.append(("Full Pipeline", await test_full_pipeline()))
        print()
    else:
        print("⚠️  Skipping use cases and pipeline tests (MongoDB unavailable)")
        print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print()
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
