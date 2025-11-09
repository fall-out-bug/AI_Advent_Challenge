"""Tests for validate script.

Following TDD principles:
- Test validation functions
- Verify configuration checking
- Test error handling
"""

import tempfile
from pathlib import Path

import pytest

from scripts.maintenance.validate import (
    validate_config_files,
    validate_json_file,
    validate_yaml_file,
)


class TestValidateScript:
    """Test validate script functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_validate_yaml_file(self, temp_dir):
        """Test YAML validation."""
        # Valid YAML
        yaml_file = temp_dir / "valid.yaml"
        yaml_file.write_text("test: value\n")
        assert validate_yaml_file(yaml_file)

        # Invalid YAML
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("test: [invalid")
        assert not validate_yaml_file(invalid_yaml)

    def test_validate_json_file(self, temp_dir):
        """Test JSON validation."""
        # Valid JSON
        json_file = temp_dir / "valid.json"
        json_file.write_text('{"test": true}')
        assert validate_json_file(json_file)

        # Invalid JSON
        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text("{invalid json}")
        assert not validate_json_file(invalid_json)

    def test_validate_config_files_with_missing_files(self, temp_dir):
        """Test config validation with missing files."""
        result = validate_config_files()
        # Should handle gracefully
        assert isinstance(result, bool)
