"""Tests for export data script.

Following TDD principles:
- Test data export
- Verify file creation
- Check export formats
"""

import tempfile
from pathlib import Path

import pytest

from scripts.maintenance.export_data import export_metrics, generate_summary


class TestExportDataScript:
    """Test export data script functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_export_metrics(self, temp_dir):
        """Test metrics export."""
        export_metrics(temp_dir)

        # Check files were created
        assert (temp_dir / "metrics.json").exists()
        assert (temp_dir / "metrics.csv").exists()

    def test_generate_summary(self, temp_dir):
        """Test summary generation."""
        generate_summary(temp_dir)

        # Check summary was created
        assert (temp_dir / "summary.json").exists()
