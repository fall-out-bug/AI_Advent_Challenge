"""HTTP client for HW Checker MCP API.

Provides async interface to HW Checker REST API endpoints.
Following Python Zen: Explicit is better than implicit.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class HWCheckerClient:
    """Client for HW Checker MCP API.

    Handles HTTP requests to HW Checker server for checking homework status,
    queue status, and retrying submissions.

    Attributes:
        base_url: Base URL for HW Checker API
        timeout: Request timeout in seconds
        client: HTTP client instance
    """

    def __init__(
        self,
        base_url: str = "http://hw_checker-mcp-server-1:8005",
        timeout: float = 30.0,
    ):
        """Initialize HW Checker client.

        Args:
            base_url: Base URL for HW Checker API (default: http://hw_checker-mcp-server-1:8005)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def get_checks_by_date(
        self,
        start_date: str,
        end_date: str,
        assignment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get checks for date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            assignment: Optional assignment filter (e.g., "HW2")
            limit: Maximum number of results (default: 100)
            offset: Offset for pagination (default: 0)

        Returns:
            Response dictionary with checks and metadata

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        }
        if assignment:
            params["assignment"] = assignment

        try:
            response = await self.client.get(
                f"{self.base_url}/api/checks_by_date", params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting checks by date: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error getting checks by date: {e}")
            raise

    async def get_all_checks_status(
        self,
        assignment: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get all checks status (full status of all homework checks).

        Args:
            assignment: Optional assignment filter (e.g., "HW2")
            limit: Maximum number of results (default: 100)

        Returns:
            Response dictionary with checks and total count

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        params = {"limit": limit}
        if assignment:
            params["assignment"] = assignment

        try:
            response = await self.client.get(
                f"{self.base_url}/api/all_checks_status", params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting all checks status: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error getting all checks status: {e}")
            raise

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status with job counts.

        Returns:
            Response dictionary with queue statistics and jobs

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/queue_status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting queue status: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error getting queue status: {e}")
            raise

    async def retry_check(
        self,
        job_id: Optional[str] = None,
        archive_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        assignment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retry a homework check.

        Args:
            job_id: Optional job ID to retry
            archive_name: Optional archive name to retry
            commit_hash: Optional commit hash to retry
            assignment: Optional assignment filter

        Returns:
            Response dictionary with retry result

        Raises:
            ValueError: If no identifier provided
            httpx.HTTPError: If HTTP request fails
        """
        if not any([job_id, archive_name, commit_hash]):
            raise ValueError("At least one identifier (job_id, archive_name, commit_hash) must be provided")

        payload: Dict[str, Any] = {}
        if job_id:
            payload["job_id"] = job_id
        if archive_name:
            payload["archive_name"] = archive_name
        if commit_hash:
            payload["commit_hash"] = commit_hash
        if assignment:
            payload["assignment"] = assignment

        try:
            response = await self.client.post(
                f"{self.base_url}/api/retry_check",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrying check: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error retrying check: {e}")
            raise

    async def health_check(self) -> Dict[str, str]:
        """Check if HW Checker server is healthy.

        Returns:
            Response dictionary with status

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking health: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error checking health: {e}")
            raise

    async def get_recent_commits(
        self,
        days: int = 1,
        assignment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get recent commits with submissions from git.

        Args:
            days: Number of days to look back (default: 1)
            assignment: Optional assignment filter (e.g., "HW2")

        Returns:
            Response dictionary with commits list and total count

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        params = {"days": days}
        if assignment:
            params["assignment"] = assignment

        try:
            response = await self.client.get(
                f"{self.base_url}/api/recent_commits", params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting recent commits: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error getting recent commits: {e}")
            raise

    async def download_archive(
        self,
        commit_hash: str,
        assignment: Optional[str] = None,
    ) -> bytes:
        """Download archive by commit hash.

        Args:
            commit_hash: Full git commit hash
            assignment: Optional assignment filter (e.g., "HW2")

        Returns:
            Archive file content as bytes

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        params = {}
        if assignment:
            params["assignment"] = assignment

        try:
            response = await self.client.get(
                f"{self.base_url}/api/archive/{commit_hash}/download",
                params=params,
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading archive: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error downloading archive: {e}")
            raise

