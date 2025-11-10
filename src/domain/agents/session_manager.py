"""Session manager for multi-pass code review.

Following Clean Architecture principles and the Zen of Python.
"""

import json
import logging
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage session state between review passes.

    Purpose:
        Creates unique sessions, persists findings between passes,
        and provides context summarization for subsequent passes.

    Args:
        session_id: Optional existing session ID to load

    Example:
        # Create new session
        session = SessionManager.create()

        # Save findings
        session.save_findings("pass_1", findings_dict)

        # Load context for next pass
        context = session.get_context_summary_for_next_pass()

        # Persist to disk
        session.persist()
    """

    SESSIONS_DIR = Path("/tmp/sessions")
    SESSION_TTL_HOURS = 24

    def __init__(self, session_id: Optional[str] = None):
        """Initialize session manager.

        Args:
            session_id: Optional existing session ID to load
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.session_dir = self.SESSIONS_DIR / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._findings_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

        if session_id:
            self._load_existing_session()

    @staticmethod
    def create() -> "SessionManager":
        """Create new session manager with unique ID.

        Returns:
            New SessionManager instance

        Example:
            session = SessionManager.create()
        """
        return SessionManager()

    def save_findings(self, pass_name: str, findings: Dict[str, Any]) -> None:
        """Save findings for a specific pass.

        Purpose:
            Saves findings to both memory cache and disk.
            Findings are stored as JSON files per pass.

        Args:
            pass_name: Name of the pass (e.g., "pass_1", "pass_2_docker")
            findings: Dictionary with findings data

        Example:
            session.save_findings("pass_1", {
                "findings": [...],
                "recommendations": [...],
                "metadata": {...}
            })
        """
        self._findings_cache[pass_name] = findings

        findings_file = self.session_dir / f"findings_{pass_name}.json"
        with open(findings_file, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2, default=str)

        self.logger.debug(f"Saved findings for {pass_name} to {findings_file}")

    def load_findings(self, pass_name: str) -> Dict[str, Any]:
        """Load findings for a specific pass.

        Purpose:
            Loads findings from cache or disk.
            Returns empty dict if not found.

        Args:
            pass_name: Name of the pass to load

        Returns:
            Dictionary with findings data or empty dict

        Example:
            findings = session.load_findings("pass_1")
        """
        # Check cache first
        if pass_name in self._findings_cache:
            return self._findings_cache[pass_name]

        # Load from disk
        findings_file = self.session_dir / f"findings_{pass_name}.json"
        if findings_file.exists():
            with open(findings_file, "r", encoding="utf-8") as f:
                findings = json.load(f)
                self._findings_cache[pass_name] = findings
                return findings

        return {}

    def load_all_findings(self) -> Dict[str, Any]:
        """Load all findings from all passes.

        Purpose:
            Aggregates findings from all completed passes.
            Useful for synthesis pass.

        Returns:
            Dictionary mapping pass_name to findings

        Example:
            all_findings = session.load_all_findings()
            # Returns: {"pass_1": {...}, "pass_2_docker": {...}, ...}
        """
        all_findings = {}

        # Load from all JSON files in session directory
        for findings_file in self.session_dir.glob("findings_*.json"):
            pass_name = findings_file.stem.replace("findings_", "")
            findings = self.load_findings(pass_name)
            if findings:
                all_findings[pass_name] = findings

        return all_findings

    def get_context_summary_for_next_pass(self) -> str:
        """Generate summarized context for next pass.

        Purpose:
            Creates human-readable summary of previous findings
            to use as context in subsequent passes.

        Returns:
            Formatted summary string

        Example:
            context = session.get_context_summary_for_next_pass()
            # Use in prompt: prompt.format(context_from_pass_1=context)
        """
        all_findings = self.load_all_findings()

        if not all_findings:
            return "No previous findings available."

        summary_parts = []
        summary_parts.append("## Context from Previous Passes\n\n")

        for pass_name, findings in sorted(all_findings.items()):
            summary_parts.append(f"### {pass_name.upper()}\n")

            # Summary if available
            if findings.get("summary"):
                summary_parts.append(f"Summary: {findings['summary']}\n\n")

            # Findings count by severity
            findings_list = findings.get("findings", {})
            if isinstance(findings_list, dict):
                critical = len(findings_list.get("critical", []))
                major = len(findings_list.get("major", []))
                minor = len(findings_list.get("minor", []))
                summary_parts.append(
                    f"Findings: {critical} critical, {major} major, {minor} minor\n\n"
                )

            # Key recommendations
            recommendations = findings.get("recommendations", [])
            if recommendations:
                summary_parts.append("Key Recommendations:\n")
                for rec in recommendations[:3]:  # Top 3
                    summary_parts.append(f"- {rec}\n")
                summary_parts.append("\n")

        return "".join(summary_parts)

    def persist(self) -> None:
        """Persist session metadata to disk.

        Purpose:
            Saves session metadata including timestamps,
            component types detected, etc.
        """
        metadata = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "findings_keys": list(self._findings_cache.keys()),
        }

        metadata_file = self.session_dir / "session_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)

        self.logger.debug(f"Persisted session metadata to {metadata_file}")

    def _load_existing_session(self) -> None:
        """Load existing session from disk."""
        if not self.session_dir.exists():
            self.logger.warning(
                f"Session directory not found: {self.session_dir}. Creating new session."
            )
            return

        # Load metadata if exists
        metadata_file = self.session_dir / "session_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                self.logger.debug(f"Loaded session metadata: {metadata}")

        # Preload findings cache
        for findings_file in self.session_dir.glob("findings_*.json"):
            pass_name = findings_file.stem.replace("findings_", "")
            self.load_findings(pass_name)

    def cleanup(self) -> None:
        """Delete session directory and all files.

        Purpose:
            Removes all session data from disk.
            Useful for cleanup after report generation.
        """
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
            self.logger.debug(f"Cleaned up session directory: {self.session_dir}")

    @classmethod
    def cleanup_old_sessions(cls, hours: Optional[int] = None) -> int:
        """Cleanup sessions older than specified hours.

        Purpose:
            Removes old session directories to prevent disk space issues.

        Args:
            hours: Age threshold in hours (default: SESSION_TTL_HOURS)

        Returns:
            Number of sessions cleaned up

        Example:
            cleaned = SessionManager.cleanup_old_sessions(24)
        """
        hours = hours or cls.SESSION_TTL_HOURS
        threshold = datetime.now() - timedelta(hours=hours)
        cleaned = 0

        if not cls.SESSIONS_DIR.exists():
            return 0

        for session_dir in cls.SESSIONS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            metadata_file = session_dir / "session_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    created_at = datetime.fromisoformat(
                        metadata.get("created_at", datetime.now().isoformat())
                    )

                    if created_at < threshold:
                        shutil.rmtree(session_dir)
                        cleaned += 1
                        logger.debug(f"Cleaned up old session: {session_dir}")

        logger.info(f"Cleaned up {cleaned} old sessions (older than {hours} hours)")
        return cleaned
