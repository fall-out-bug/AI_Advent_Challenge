"""Homework review repository for storing review logs and reports in MongoDB.

Following Clean Architecture principles and the Zen of Python.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class HomeworkReviewRepository:
    """Async repository for homework review sessions.

    Purpose:
        Encapsulate CRUD operations for homework review sessions,
        including logs, reports, and metadata.

    Args:
        db: MongoDB database instance

    Example:
        repository = HomeworkReviewRepository(db)
        session_id = await repository.save_review_session(
            session_id="abc-123",
            repo_name="student_hw1",
            logs=all_logs,
            report=report_dict
        )
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository.

        Args:
            db: MongoDB database instance
        """
        self._db = db
        self._indexes_created = False

    async def _ensure_indexes(self) -> None:
        """Create required indexes for efficient queries."""
        if self._indexes_created:
            return

        collection = self._db.homework_reviews

        # Unique index on session_id
        await collection.create_index([("session_id", 1)], unique=True)

        # Index on repo_name and created_at for queries
        await collection.create_index([("repo_name", 1), ("created_at", -1)])

        # Index on assignment_type
        await collection.create_index([("assignment_type", 1)])

        # TTL index on created_at (optional: 30 days)
        # Uncomment if you want automatic cleanup:
        # await collection.create_index(
        #     [("created_at", 1)], expireAfterSeconds=2592000
        # )

        self._indexes_created = True

    async def save_review_session(
        self,
        session_id: str,
        repo_name: str,
        assignment_type: str,
        logs: Dict[str, Any],
        report: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save complete review session to MongoDB.

        Purpose:
            Saves all logs (work, review, model responses) and report
            (markdown + JSON) to MongoDB.

        Args:
            session_id: Unique session ID
            repo_name: Repository/project name
            assignment_type: Assignment type (HW1, HW2, HW3, auto)
            logs: Dict with all logs from ReviewLogger.get_all_logs()
            report: Dict with markdown and json report
            metadata: Optional additional metadata

        Returns:
            Document ID as string

        Raises:
            ValueError: If required fields are missing

        Example:
            session_id = await repository.save_review_session(
                session_id="abc-123",
                repo_name="student_hw1",
                assignment_type="HW1",
                logs=review_logger.get_all_logs(),
                report={"markdown": "...", "json": {...}},
                metadata={"execution_time": 120.5}
            )
        """
        await self._ensure_indexes()

        # Validate required fields
        if (
            not session_id
            or not repo_name
            or not assignment_type
            or not logs
            or not report
        ):
            missing = []
            if not session_id:
                missing.append("session_id")
            if not repo_name:
                missing.append("repo_name")
            if not assignment_type:
                missing.append("assignment_type")
            if not logs:
                missing.append("logs")
            if not report:
                missing.append("report")
            raise ValueError(f"Missing required fields: {missing}")

        doc: Dict[str, Any] = {
            "session_id": session_id,
            "repo_name": repo_name,
            "assignment_type": assignment_type,
            "created_at": datetime.utcnow(),
            "logs": logs,
            "report": report,
            "metadata": metadata or {},
        }

        # Insert or update if session_id already exists
        result = await self._db.homework_reviews.update_one(
            {"session_id": session_id},
            {"$set": doc},
            upsert=True,
        )

        return str(result.upserted_id) if result.upserted_id else session_id

    async def get_review_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get review session by session_id.

        Purpose:
            Retrieves complete review session including all logs and report.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Review session document or None if not found

        Example:
            session = await repository.get_review_session("abc-123")
            if session:
                markdown = session["report"]["markdown"]
        """
        await self._ensure_indexes()

        doc = await self._db.homework_reviews.find_one({"session_id": session_id})

        if doc:
            doc["id"] = str(doc.pop("_id"))
            return doc

        return None

    async def save_logs(
        self,
        session_id: str,
        logs: Dict[str, Any],
    ) -> bool:
        """Save logs for existing session.

        Purpose:
            Updates logs for an existing review session.

        Args:
            session_id: Session ID
            logs: Logs dict from ReviewLogger.get_all_logs()

        Returns:
            True if updated, False if session not found

        Example:
            updated = await repository.save_logs(
                "abc-123",
                review_logger.get_all_logs()
            )
        """
        await self._ensure_indexes()

        result = await self._db.homework_reviews.update_one(
            {"session_id": session_id},
            {"$set": {"logs": logs, "updated_at": datetime.utcnow()}},
        )

        return result.modified_count > 0

    async def save_markdown_report(
        self,
        session_id: str,
        markdown: str,
        json_report: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save markdown report for existing session.

        Purpose:
            Updates report for an existing review session.

        Args:
            session_id: Session ID
            markdown: Markdown report string
            json_report: Optional JSON report

        Returns:
            True if updated, False if session not found

        Example:
            updated = await repository.save_markdown_report(
                "abc-123",
                markdown_report,
                json_report=report.to_dict()
            )
        """
        await self._ensure_indexes()

        report_update: Dict[str, Any] = {"report.markdown": markdown}
        if json_report:
            report_update["report.json"] = json_report

        report_update["updated_at"] = datetime.utcnow()

        result = await self._db.homework_reviews.update_one(
            {"session_id": session_id},
            {"$set": report_update},
        )

        return result.modified_count > 0

    async def list_reviews(
        self,
        repo_name: Optional[str] = None,
        assignment_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """List review sessions with optional filters.

        Purpose:
            Query review sessions by repo_name or assignment_type.

        Args:
            repo_name: Optional filter by repository name
            assignment_type: Optional filter by assignment type
            limit: Maximum number of results

        Returns:
            List of review session documents

        Example:
            reviews = await repository.list_reviews(
                repo_name="student_hw1",
                limit=10
            )
        """
        await self._ensure_indexes()

        query: Dict[str, Any] = {}
        if repo_name:
            query["repo_name"] = repo_name
        if assignment_type:
            query["assignment_type"] = assignment_type

        cursor = (
            self._db.homework_reviews.find(query).sort("created_at", -1).limit(limit)
        )
        docs = await cursor.to_list(length=limit)

        for doc in docs:
            doc["id"] = str(doc.pop("_id"))

        return docs
