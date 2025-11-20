"""Tests for SessionManager.

Following TDD principles and the Zen of Python.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.domain.agents.session_manager import SessionManager


class TestSessionManager:
    """Test suite for SessionManager."""

    def test_create_session(self):
        """Test session creation."""
        session = SessionManager.create()
        assert session.session_id is not None
        assert session.session_dir.exists()

    def test_save_and_load_findings(self):
        """Test saving and loading findings."""
        session = SessionManager.create()
        findings = {
            "findings": {"critical": ["Issue 1"], "major": []},
            "recommendations": ["Fix issue 1"],
        }

        session.save_findings("pass_1", findings)
        loaded = session.load_findings("pass_1")

        assert loaded == findings
        assert loaded["findings"]["critical"] == ["Issue 1"]

    def test_load_all_findings(self):
        """Test loading all findings."""
        session = SessionManager.create()

        session.save_findings("pass_1", {"findings": {}})
        session.save_findings("pass_2_docker", {"findings": {}})

        all_findings = session.load_all_findings()
        assert "pass_1" in all_findings
        assert "pass_2_docker" in all_findings

    def test_context_summary_generation(self):
        """Test context summary generation."""
        session = SessionManager.create()

        session.save_findings(
            "pass_1",
            {
                "findings": {
                    "critical": ["Issue 1"],
                    "major": ["Issue 2"],
                    "minor": [],
                },
                "recommendations": ["Rec 1"],
                "summary": "Test summary",
            },
        )

        context = session.get_context_summary_for_next_pass()
        assert "PASS_1" in context or "pass_1" in context.lower()
        assert "critical" in context.lower()
        assert "Test summary" in context

    def test_persist_session(self):
        """Test session persistence."""
        session = SessionManager.create()
        session.save_findings("pass_1", {"test": "data"})
        session.persist()

        metadata_file = session.session_dir / "session_metadata.json"
        assert metadata_file.exists()

    def test_load_existing_session(self):
        """Test loading existing session."""
        session = SessionManager.create()
        session_id = session.session_id
        session.save_findings("pass_1", {"test": "data"})
        session.persist()

        # Load in new instance
        session_2 = SessionManager(session_id=session_id)
        loaded = session_2.load_findings("pass_1")
        assert loaded == {"test": "data"}

    def test_cleanup_session(self):
        """Test session cleanup."""
        session = SessionManager.create()
        session_dir = session.session_dir
        session.save_findings("pass_1", {"test": "data"})

        session.cleanup()
        assert not session_dir.exists()
