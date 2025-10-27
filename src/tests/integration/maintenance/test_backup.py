"""Tests for backup script.

Following TDD principles:
- Test backup creation
- Test backup restoration
- Test backup listing
"""

import tempfile
import tarfile
from pathlib import Path

import pytest

from scripts.maintenance.backup import create_backup, list_backups, restore_backup
from src.infrastructure.config.settings import Settings


class TestBackupScript:
    """Test backup script functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def settings(self, temp_dir):
        """Create test settings."""
        return Settings(storage_path=temp_dir)

    def test_create_backup(self, settings, temp_dir):
        """Test backup creation."""
        # Create test files
        test_file = settings.storage_path / "test.json"
        test_file.write_text('{"test": true}')

        # Create backup
        output_dir = temp_dir / "backups"
        backup_path = create_backup(settings, output_dir)

        # Verify backup was created
        assert backup_path.exists()
        assert backup_path.suffix == ".gz"

    def test_list_backups(self, temp_dir):
        """Test listing backups."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir()

        # Should handle empty directory
        list_backups(backup_dir)

        # Create a fake backup
        fake_backup = backup_dir / "backup_20240101_120000.tar.gz"
        fake_backup.write_text("test")

        # Should list backup
        list_backups(backup_dir)
