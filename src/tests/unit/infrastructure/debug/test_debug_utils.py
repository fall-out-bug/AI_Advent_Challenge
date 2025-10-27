"""Tests for debug utilities.

Following TDD principles:
- Tests first approach
- Comprehensive coverage
- Clear test scenarios
"""

import json
from pathlib import Path

import pytest

from src.infrastructure.config.settings import Settings
from src.infrastructure.debug.debug_utils import DebugUtils


class TestDebugUtils:
    """Test debug utilities."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create test settings."""
        return Settings(storage_path=tmp_path)

    @pytest.fixture
    def debug_utils(self, settings):
        """Create debug utils."""
        return DebugUtils(settings)

    def test_dump_config(self, debug_utils):
        """Test configuration dump."""
        config = debug_utils.dump_config()

        assert "storage_path" in config
        assert "agent_storage" in config
        assert "experiment_storage" in config
        assert "model_default_name" in config

    def test_count_tokens(self, debug_utils):
        """Test token counting."""
        text = "This is a test string with many words"
        result = debug_utils.count_tokens(text)

        assert "estimated_tokens" in result
        assert "character_count" in result
        assert "word_count" in result
        assert result["character_count"] == len(text)
        assert result["word_count"] == 8

    def test_count_tokens_empty(self, debug_utils):
        """Test token counting with empty text."""
        result = debug_utils.count_tokens("")

        assert result["estimated_tokens"] == 0
        assert result["word_count"] == 0

    def test_replay_request_valid(self, debug_utils):
        """Test replay request with valid data."""
        request_data = {"prompt": "Test prompt", "model": "test-model"}

        result = debug_utils.replay_request(request_data)

        assert "original_request" in result
        assert "replay_metadata" in result
        assert result["replay_metadata"]["validation_status"] == "valid"

    def test_check_dependencies(self, debug_utils):
        """Test dependency checking."""
        dependencies = debug_utils.check_dependencies()

        assert "httpx" in dependencies
        assert "fastapi" in dependencies
        assert isinstance(dependencies["httpx"], dict)
        assert "installed" in dependencies["httpx"]

    def test_export_config_snapshot(self, debug_utils, tmp_path):
        """Test config snapshot export."""
        filepath = tmp_path / "snapshot.json"
        debug_utils.export_config_snapshot(str(filepath))

        assert filepath.exists()

        with filepath.open() as f:
            data = json.load(f)

        assert "configuration" in data
        assert "dependencies" in data
        assert "timestamp" in data
