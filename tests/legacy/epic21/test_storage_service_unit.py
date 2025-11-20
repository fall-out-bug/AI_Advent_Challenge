"""Unit tests for StorageService with security focus.

Tests the new secure storage abstraction with path validation and access control.

Epic 21 · Stage 21_01c · Storage Abstraction
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.domain.interfaces.storage_service import StorageError, StorageService
from src.infrastructure.services.storage_service_impl import StorageServiceImpl


@pytest.mark.epic21
@pytest.mark.stage_21_01
@pytest.mark.storage
@pytest.mark.unit
class TestStorageServiceUnit:
    """Unit tests for StorageService implementation."""

    @pytest.fixture
    def storage_service(self) -> StorageService:
        """Create StorageService with test configuration."""
        import tempfile

        system_temp = Path(tempfile.gettempdir())
        return StorageServiceImpl(
            allowed_base_dirs=[system_temp, Path("/tmp"), Path("/app/archive")],
            max_temp_file_size=1024 * 1024,  # 1MB for tests
        )

    def test_create_temp_file_basic(self, storage_service):
        """Unit: create_temp_file creates file with correct parameters."""
        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.return_value.__enter__ = lambda self: self
            mock_tempfile.return_value.__exit__ = lambda self, *args: None
            mock_tempfile.return_value.name = "/tmp/test_temp_file.zip"
            mock_tempfile.return_value.write = lambda data: None
            mock_tempfile.return_value.flush = lambda: None

            temp_file = storage_service.create_temp_file(
                suffix=".zip", prefix="test_", content=b"test content"
            )

            # Verify tempfile creation parameters
            call_kwargs = mock_tempfile.call_args[1]
            assert call_kwargs["delete"] == False
            assert call_kwargs["suffix"] == ".zip"
            assert call_kwargs["prefix"] == "test_"
            assert call_kwargs["mode"] == "wb+"

    def test_create_temp_file_with_content(self, storage_service):
        """Unit: create_temp_file writes content correctly."""
        content_written = []

        def mock_write(data):
            content_written.append(data)

        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.return_value.__enter__ = lambda self: self
            mock_tempfile.return_value.__exit__ = lambda self, *args: None
            mock_tempfile.return_value.name = "/tmp/test_temp_file.txt"
            mock_tempfile.return_value.write = mock_write
            mock_tempfile.return_value.flush = lambda: None

            test_content = b"Hello, World!"
            temp_file = storage_service.create_temp_file(content=test_content)

            assert content_written == [test_content]

    def test_create_temp_file_content_size_limit(self, storage_service):
        """Unit: create_temp_file enforces size limits."""
        large_content = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte

        with pytest.raises(StorageError) as exc_info:
            storage_service.create_temp_file(content=large_content)

        assert "Content size" in str(exc_info.value)
        assert "exceeds maximum" in str(exc_info.value)

    def test_create_temp_file_path_validation(self, storage_service):
        """Unit: create_temp_file validates created path."""
        with (
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch.object(storage_service, "validate_path_safe", return_value=False),
        ):

            mock_tempfile.return_value.__enter__ = lambda self: self
            mock_tempfile.return_value.__exit__ = lambda self, *args: None
            mock_tempfile.return_value.name = "/tmp/test_temp_file.zip"
            mock_tempfile.return_value.write = lambda data: None
            mock_tempfile.return_value.flush = lambda: None

            with pytest.raises(StorageError) as exc_info:
                storage_service.create_temp_file()

            assert "unsafe" in str(exc_info.value)

    def test_create_temp_text_file_basic(self, storage_service):
        """Unit: create_temp_text_file creates text file correctly."""
        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.return_value.__enter__ = lambda self: self
            mock_tempfile.return_value.__exit__ = lambda self, *args: None
            mock_tempfile.return_value.name = "/tmp/test_temp_file.md"
            mock_tempfile.return_value.write = lambda data: None
            mock_tempfile.return_value.flush = lambda: None

            temp_file = storage_service.create_temp_text_file(
                suffix=".md", prefix="report_", content="Test content", encoding="utf-8"
            )

            call_kwargs = mock_tempfile.call_args[1]
            assert call_kwargs["delete"] == False
            assert call_kwargs["suffix"] == ".md"
            assert call_kwargs["prefix"] == "report_"
            assert call_kwargs["mode"] == "w+"
            assert call_kwargs["encoding"] == "utf-8"

    def test_validate_path_safe_within_allowed_dirs(self, storage_service):
        """Unit: validate_path_safe allows paths within allowed directories."""
        # Test allowed paths
        allowed_paths = [
            Path("/tmp/safe_file.txt"),
            Path("/app/archive/safe_file.zip"),
        ]

        for path in allowed_paths:
            assert storage_service.validate_path_safe(path)

    def test_validate_path_safe_blocks_path_traversal(self, storage_service):
        """Unit: validate_path_safe blocks path traversal attempts."""
        dangerous_paths = [
            Path("/tmp/../../../etc/passwd"),
            Path("/app/archive/../secret.txt"),
            Path("/tmp/.hidden/file"),
            Path("/absolute/path"),
            Path("C:\\windows\\system32"),
        ]

        for path in dangerous_paths:
            assert not storage_service.validate_path_safe(path)

    def test_validate_path_safe_blocks_unsafe_suffix(self, storage_service):
        """Unit: create_temp_file blocks unsafe suffixes."""
        unsafe_suffixes = [
            "../etc/passwd",
            "../../../root",
            "/absolute/path",
        ]

        for suffix in unsafe_suffixes:
            with pytest.raises(StorageError) as exc_info:
                storage_service.create_temp_file(suffix=suffix)

            assert "Invalid file suffix" in str(exc_info.value)

    def test_cleanup_temp_file_basic(self, storage_service):
        """Unit: cleanup_temp_file removes file correctly."""
        test_path = Path("/tmp/test_cleanup_file.txt")

        with (
            patch.object(test_path, "unlink") as mock_unlink,
            patch.object(storage_service, "validate_path_safe", return_value=True),
            patch.object(storage_service, "_is_temp_file_pattern", return_value=True),
        ):

            storage_service.cleanup_temp_file(test_path)

            mock_unlink.assert_called_once_with(missing_ok=True)

    def test_cleanup_temp_file_validates_path(self, storage_service):
        """Unit: cleanup_temp_file validates path safety."""
        unsafe_path = Path("/etc/passwd")

        with patch.object(storage_service, "validate_path_safe", return_value=False):
            with pytest.raises(StorageError) as exc_info:
                storage_service.cleanup_temp_file(unsafe_path)

            assert "unsafe path" in str(exc_info.value)

    def test_ensure_directory_exists_basic(self, storage_service):
        """Unit: ensure_directory_exists creates directory."""
        test_dir = Path("/tmp/test_dir")

        with (
            patch.object(test_dir, "mkdir") as mock_mkdir,
            patch.object(storage_service, "validate_path_safe", return_value=True),
            patch.object(storage_service, "validate_file_access", return_value=True),
        ):

            storage_service.ensure_directory_exists(test_dir)

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_secure_temp_dir_prefers_shared(self, storage_service):
        """Unit: get_secure_temp_dir prefers shared directory."""
        with patch("pathlib.Path.exists", return_value=True):
            secure_dir = storage_service.get_secure_temp_dir()
            assert str(secure_dir) == "/app/archive"

    def test_get_secure_temp_dir_falls_back_to_system(self, storage_service):
        """Unit: get_secure_temp_dir falls back to system temp."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("tempfile.gettempdir", return_value="/system/tmp"),
        ):

            secure_dir = storage_service.get_secure_temp_dir()
            assert str(secure_dir) == "/system/tmp"

    def test_validate_file_access_read_operation(self, storage_service):
        """Unit: validate_file_access checks read permissions."""
        test_path = Path("/tmp/test_file.txt")

        with (
            patch.object(test_path, "stat") as mock_stat,
            patch.object(test_path, "exists", return_value=True),
        ):

            # Mock stat to return read permission
            mock_stat.return_value.st_mode = 0o644  # rw-r--r--

            assert storage_service.validate_file_access(test_path, "read")

    def test_validate_file_access_write_operation(self, storage_service):
        """Unit: validate_file_access checks write permissions."""
        test_path = Path("/tmp/test_file.txt")

        with (
            patch.object(test_path, "stat") as mock_stat,
            patch.object(test_path, "exists", return_value=True),
        ):

            # Mock stat to return write permission
            mock_stat.return_value.st_mode = 0o644  # rw-r--r--

            assert storage_service.validate_file_access(test_path, "write")

    def test_validate_file_access_nonexistent_file_parent(self, storage_service):
        """Unit: validate_file_access checks parent directory for nonexistent files."""
        test_path = Path("/tmp/nonexistent_file.txt")
        parent_path = test_path.parent

        with (
            patch.object(test_path, "exists", return_value=False),
            patch.object(parent_path, "stat") as mock_stat,
        ):

            mock_stat.return_value.st_mode = 0o755  # rwxr-xr-x

            assert storage_service.validate_file_access(test_path, "write")

    def test_validate_file_access_unknown_operation(self, storage_service):
        """Unit: validate_file_access returns False for unknown operations."""
        test_path = Path("/tmp/test_file.txt")

        assert not storage_service.validate_file_access(test_path, "unknown")

    def test_is_temp_file_pattern_recognizes_temp_files(self, storage_service):
        """Unit: _is_temp_file_pattern recognizes temporary file patterns."""
        temp_paths = [
            Path("/tmp/temp_file.txt"),
            Path("/tmp/homework_review_archive.zip"),
            Path("/tmp/tmp_data.dat"),
        ]

        for path in temp_paths:
            assert storage_service._is_temp_file_pattern(path)

    def test_is_temp_file_pattern_rejects_non_temp_files(self, storage_service):
        """Unit: _is_temp_file_pattern rejects non-temporary files."""
        non_temp_paths = [
            Path("/tmp/config.json"),
            Path("/tmp/user_data.db"),
            Path("/tmp/important_file.txt"),
        ]

        for path in non_temp_paths:
            assert not storage_service._is_temp_file_pattern(path)

    def test_contains_path_traversal_detects_traversal(self, storage_service):
        """Unit: _contains_path_traversal detects path traversal attempts."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\windows\\system32",
            "/absolute/path",
            "C:\\drive\\letter",
        ]

        for attempt in traversal_attempts:
            assert storage_service._contains_path_traversal(attempt)

    def test_contains_path_traversal_allows_safe_paths(self, storage_service):
        """Unit: _contains_path_traversal allows safe relative paths."""
        safe_paths = [
            "safe_file.txt",
            "subdir/file.zip",
            "path/to/file.md",
        ]

        for path in safe_paths:
            assert not storage_service._contains_path_traversal(path)
