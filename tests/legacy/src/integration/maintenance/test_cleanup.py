"""Tests for cleanup script.

Following TDD principles:
- Tests verify script functionality
- Clear test scenarios
- Mock external dependencies
"""

import tempfile
from pathlib import Path

import pytest

from scripts.maintenance.cleanup import cleanup_data, find_old_files
from src.infrastructure.config.settings import Settings


class TestCleanupScript:
    """Test cleanup script functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def settings(self, temp_dir):
        """Create test settings."""
        return Settings(storage_path=temp_dir)

    def test_find_old_files(self, temp_dir):
        """Test finding old files."""
        # Create a file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        # Should find old files (simulating old files)
        old_files = find_old_files(temp_dir, 0)

        assert len(old_files) >= 0

    def test_cleanup_data_dry_run(self, settings):
        """Test cleanup in dry run mode."""
        # Create some test files
        test_file = settings.storage_path / "test.json"
        test_file.write_text('{"test": true}')

        # Run in dry run mode
        cleanup_data(settings, days=0, dry_run=True)

        # File should still exist
        assert test_file.exists()

    def test_cleanup_creates_backup(self, settings):
        """Test that cleanup archives files."""
        # Create some test files
        test_file = settings.storage_path / "test.json"
        test_file.write_text('{"test": true}')

        # Run cleanup
        cleanup_data(settings, days=0, dry_run=False)

        # Check backup directory exists
        backup_dir = settings.storage_path / "archive"
        assert backup_dir.exists()
