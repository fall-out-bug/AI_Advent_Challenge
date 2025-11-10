"""End-to-end tests for review pipeline with real ZIP archives."""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

# Add shared to path for UnifiedModelClient
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.application.use_cases.review_submission_use_case import (
    ReviewSubmissionUseCase,
)
from src.domain.services.diff_analyzer import DiffAnalyzer
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.clients.external_api_client import ExternalAPIClient
from src.infrastructure.clients.external_api_mock import ExternalAPIClientMock
from src.infrastructure.config.settings import get_settings
from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.repositories.long_tasks_repository import (
    LongTasksRepository,
)

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


@pytest.fixture
def temp_zip_dir():
    """Create temporary directory for test ZIP files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def create_test_zip(
    zip_path: str, files: dict[str, str], test_logs: str | None = None
) -> None:
    """Create test ZIP archive with files.

    Args:
        zip_path: Path to create ZIP
        files: Dictionary mapping file paths to content
        test_logs: Optional test logs content
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_path, content in files.items():
            zf.writestr(file_path, content)
        if test_logs:
            zf.writestr("test_logs.txt", test_logs)


@pytest.fixture
def old_submission_zip(temp_zip_dir):
    """Create old submission ZIP for testing."""
    zip_path = os.path.join(temp_zip_dir, "old_submission.zip")
    create_test_zip(
        zip_path,
        {
            "main.py": "def hello():\n    print('old version')\n    return 1",
            "utils.py": "def helper():\n    pass",
        },
        test_logs="Tests passed: 5/5",
    )
    return zip_path


@pytest.fixture
def new_submission_zip(temp_zip_dir):
    """Create new submission ZIP for testing."""
    zip_path = os.path.join(temp_zip_dir, "new_submission.zip")
    create_test_zip(
        zip_path,
        {
            "main.py": "def hello():\n    print('new version')\n    return 2\ndef new_func():\n    pass",
            "utils.py": "def helper():\n    pass\ndef new_helper():\n    return True",
            "tests.py": "def test_new():\n    assert True",
        },
        test_logs="Tests passed: 8/8\nCoverage: 90%",
    )
    return zip_path


@pytest.mark.asyncio
async def test_full_review_pipeline_with_real_zips(
    real_mongodb, old_submission_zip, new_submission_zip
):
    """Test complete review pipeline with real ZIP archives.

    Purpose:
        E2E test that verifies the entire review process using modular reviewer:
        1. Extract archives
        2. Analyze diff
        3. Run multi-pass review
        4. Save results

    Note:
        - Tests call use cases directly (not through worker) - this is correct
          for E2E testing as we test business logic, not worker infrastructure
        - Uses real UnifiedModelClient (requires LLM_URL environment variable)
        - Worker would call the same use cases in production

    Prerequisites:
        - MongoDB running (test will be skipped if unavailable)
        - LLM_URL environment variable set (e.g., http://localhost:8000)
        - External API (optional): set EXTERNAL_API_URL and EXTERNAL_API_KEY for real API testing
    """
    if UnifiedModelClient is None:
        pytest.skip("UnifiedModelClient not available")

    # Setup
    settings = get_settings()
    tasks_repo = LongTasksRepository(real_mongodb)
    review_repo = HomeworkReviewRepository(real_mongodb)
    archive_service = ZipArchiveService(settings)
    diff_analyzer = DiffAnalyzer()

    # Use real UnifiedModelClient (requires LLM_URL environment variable)
    llm_url = settings.llm_url or os.getenv("LLM_URL")
    if not llm_url:
        pytest.skip("LLM_URL not configured, skipping E2E test with real LLM")

    # Set LLM_URL in environment for UnifiedModelClient
    if not os.getenv("LLM_URL"):
        os.environ["LLM_URL"] = llm_url

    unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)

    # Use real external API client if configured, otherwise mock
    if settings.external_api_enabled and settings.external_api_url:
        try:
            publisher = ExternalAPIClient(settings)
        except ValueError:
            publisher = ExternalAPIClientMock(settings)
    else:
        publisher = ExternalAPIClientMock(settings)

    review_use_case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=diff_analyzer,
        unified_client=unified_client,
        review_repository=review_repo,
        tasks_repository=tasks_repo,
        publisher=publisher,
    )

    # Create task
    enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
    task = await enqueue_use_case.execute(
        student_id="123",  # Must be numeric for user_id
        assignment_id="HW2",
        new_submission_path=new_submission_zip,
        previous_submission_path=old_submission_zip,
        new_commit="commit_hw2",
    )

    assert task.task_type.value == "code_review"
    assert task.status.value == "queued"
    assert task.task_id is not None

    # Process task
    session_id = await review_use_case.execute(task)

    assert session_id is not None

    # Verify task is completed
    completed_task = await tasks_repo.get_by_id(task.task_id)
    assert completed_task is not None
    assert completed_task.status.value == "succeeded"
    assert completed_task.result_text == session_id

    # Verify review session exists
    session = await review_repo.get_review_session(session_id)
    assert session is not None
    assert "report" in session
    assert "markdown" in session["report"]
    assert "json" in session["report"]


@pytest.mark.asyncio
async def test_review_pipeline_first_submission(real_mongodb, new_submission_zip):
    """Test review pipeline for first submission (no previous).

    Prerequisites:
        - MongoDB running (test will be skipped if unavailable)
        - LLM_URL environment variable set
    """
    if UnifiedModelClient is None:
        pytest.skip("UnifiedModelClient not available")

    settings = get_settings()
    tasks_repo = LongTasksRepository(real_mongodb)
    review_repo = HomeworkReviewRepository(real_mongodb)
    archive_service = ZipArchiveService(settings)
    diff_analyzer = DiffAnalyzer()

    llm_url = settings.llm_url or os.getenv("LLM_URL")
    if not llm_url:
        pytest.skip("LLM_URL not configured")

    if not os.getenv("LLM_URL"):
        os.environ["LLM_URL"] = llm_url

    unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)

    if settings.external_api_enabled and settings.external_api_url:
        try:
            publisher = ExternalAPIClient(settings)
        except ValueError:
            publisher = ExternalAPIClientMock(settings)
    else:
        publisher = ExternalAPIClientMock(settings)

    review_use_case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=diff_analyzer,
        unified_client=unified_client,
        review_repository=review_repo,
        tasks_repository=tasks_repo,
        publisher=publisher,
    )

    enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
    task = await enqueue_use_case.execute(
        student_id="456",
        assignment_id="HW1",
        new_submission_path=new_submission_zip,
        new_commit="commit_hw1",
    )

    session_id = await review_use_case.execute(task)

    completed_task = await tasks_repo.get_by_id(task.task_id)
    assert completed_task.status.value == "succeeded"
    assert completed_task.metadata.get("previous_submission_path") is None


@pytest.mark.asyncio
async def test_review_pipeline_handles_invalid_zip(real_mongodb):
    """Test review pipeline handles invalid ZIP gracefully.

    Prerequisites:
        - MongoDB running (test will be skipped if unavailable)
        - LLM_URL environment variable set
    """
    if UnifiedModelClient is None:
        pytest.skip("UnifiedModelClient not available")

    settings = get_settings()
    tasks_repo = LongTasksRepository(real_mongodb)
    review_repo = HomeworkReviewRepository(real_mongodb)
    archive_service = ZipArchiveService(settings)
    diff_analyzer = DiffAnalyzer()

    llm_url = settings.llm_url or os.getenv("LLM_URL")
    if not llm_url:
        pytest.skip("LLM_URL not configured")

    if not os.getenv("LLM_URL"):
        os.environ["LLM_URL"] = llm_url

    unified_client = UnifiedModelClient(timeout=settings.review_llm_timeout)

    if settings.external_api_enabled and settings.external_api_url:
        try:
            publisher = ExternalAPIClient(settings)
        except ValueError:
            publisher = ExternalAPIClientMock(settings)
    else:
        publisher = ExternalAPIClientMock(settings)

    review_use_case = ReviewSubmissionUseCase(
        archive_reader=archive_service,
        diff_analyzer=diff_analyzer,
        unified_client=unified_client,
        review_repository=review_repo,
        tasks_repository=tasks_repo,
        publisher=publisher,
    )

    enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
    task = await enqueue_use_case.execute(
        student_id="789",
        assignment_id="HW2",
        new_submission_path="/nonexistent/archive.zip",
        new_commit="commit_invalid",
    )

    # Should fail gracefully
    with pytest.raises(Exception):
        await review_use_case.execute(task)

    failed_task = await tasks_repo.get_by_id(task.task_id)
    assert failed_task.status.value == "failed"
    assert failed_task.error is not None
