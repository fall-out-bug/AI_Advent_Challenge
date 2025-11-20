"""Example: Submit code review using Python requests library.

This example demonstrates how to integrate with the Code Review API.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class ReviewAPIClient:
    """Client for Code Review API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip("/")
        self.reviews_endpoint = f"{self.base_url}/api/v1/reviews"

    def submit_review(
        self,
        student_id: str,
        assignment_id: str,
        new_zip_path: str,
        old_zip_path: Optional[str] = None,
        logs_zip_path: Optional[str] = None,
        new_commit: str,
        old_commit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit code review task.

        Args:
            student_id: Student identifier
            assignment_id: Assignment identifier
            new_zip_path: Path to new submission ZIP archive
            old_zip_path: Optional path to previous submission ZIP
            logs_zip_path: Optional path to logs ZIP archive
            new_commit: Commit hash for new submission
            old_commit: Optional commit hash for previous submission

        Returns:
            Response dictionary with task_id and status

        Raises:
            requests.HTTPError: On API error
        """
        files = {
            "new_zip": open(new_zip_path, "rb"),
        }

        data = {
            "student_id": student_id,
            "assignment_id": assignment_id,
        }

        new_commit_value = new_commit.strip()
        if not new_commit_value:
            raise ValueError("new_commit cannot be empty")
        data["new_commit"] = new_commit_value
        if old_commit:
            data["old_commit"] = old_commit

        if old_zip_path:
            files["old_zip"] = open(old_zip_path, "rb")
        if logs_zip_path:
            files["logs_zip"] = open(logs_zip_path, "rb")

        try:
            response = requests.post(
                self.reviews_endpoint,
                files=files,
                data=data,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        finally:
            # Close all file handles
            for file_obj in files.values():
                file_obj.close()

    def get_review_status(self, task_id: str) -> Dict[str, Any]:
        """Get review task status.

        Args:
            task_id: Task identifier

        Returns:
            Response dictionary with task status and results

        Raises:
            requests.HTTPError: On API error
        """
        response = requests.get(
            f"{self.reviews_endpoint}/{task_id}",
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 5,
        max_wait: int = 300,
    ) -> Dict[str, Any]:
        """Wait for review task to complete.

        Args:
            task_id: Task identifier
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            Final task status

        Raises:
            TimeoutError: If task doesn't complete within max_wait
        """
        start_time = time.time()

        while True:
            status = self.get_review_status(task_id)

            if status["status"] in ["completed", "failed"]:
                return status

            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {max_wait}s"
                )

            time.sleep(poll_interval)


def main():
    """Example usage."""
    client = ReviewAPIClient(base_url="http://localhost:8000")

    # Submit review
    print("Submitting review...")
    result = client.submit_review(
        student_id="student_123",
        assignment_id="HW2",
        new_zip_path="./new_submission.zip",
        old_zip_path="./old_submission.zip",
        logs_zip_path="./logs.zip",
        new_commit="abc123def456",
        old_commit="xyz789uvw012",
    )

    task_id = result["task_id"]
    print(f"Task created: {task_id}")
    print(f"Status: {result['status']}")

    # Wait for completion
    print("Waiting for review to complete...")
    final_status = client.wait_for_completion(task_id)

    print(f"Final status: {final_status['status']}")
    if final_status["status"] == "completed":
        print(f"Session ID: {final_status['result'].get('session_id')}")
        print(f"Overall score: {final_status['result'].get('overall_score')}")
    elif final_status["status"] == "failed":
        print(f"Error: {final_status.get('error')}")


if __name__ == "__main__":
    main()
