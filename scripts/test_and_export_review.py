"""Script to test review with archives and export reports."""

import json
import sys
import time
from pathlib import Path

import requests

# API base URL
API_BASE = "http://localhost:8004/api/v1/reviews"


def create_review_task(
    student_id: str,
    assignment_id: str,
    new_submission_path: str,
    previous_submission_path: str | None = None,
) -> dict:
    """Create review task.

    Args:
        student_id: Student ID (must be numeric)
        assignment_id: Assignment ID
        new_submission_path: Path to new submission archive
        previous_submission_path: Optional path to previous submission

    Returns:
        Task data
    """
    payload = {
        "student_id": student_id,
        "assignment_id": assignment_id,
        "new_submission_path": new_submission_path,
    }
    if previous_submission_path:
        payload["previous_submission_path"] = previous_submission_path

    print(f"Creating review task: student={student_id}, assignment={assignment_id}")
    response = requests.post(API_BASE, json=payload)
    response.raise_for_status()
    return response.json()


def wait_for_task(task_id: str, max_wait: int = 300) -> dict:
    """Wait for task to complete.

    Args:
        task_id: Task ID
        max_wait: Maximum wait time in seconds

    Returns:
        Final task status data
    """
    print(f"\nWaiting for task {task_id} to complete...")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE}/{task_id}")
        response.raise_for_status()
        data = response.json()
        status = data["status"]
        elapsed = int(time.time() - start_time)

        print(f"[{elapsed}s] Status: {status}")

        if status == "succeeded":
            print("✅ Task completed successfully!")
            return data
        elif status == "failed":
            print(f"❌ Task failed: {data.get('error', 'Unknown error')}")
            return data

        time.sleep(3)

    print(f"⏱️  Timeout after {max_wait} seconds")
    response = requests.get(f"{API_BASE}/{task_id}")
    response.raise_for_status()
    return response.json()


def export_report(task_data: dict, output_dir: Path) -> None:
    """Export review report to files.

    Args:
        task_data: Task data with result
        output_dir: Output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    task_id = task_data["task_id"]
    result = task_data.get("result", {})

    if not result:
        print(f"⚠️  No result for task {task_id}")
        return

    session_id = result.get("session_id", "unknown")
    report = result.get("report", {})

    # Export markdown report
    markdown = report.get("markdown", "")
    if markdown:
        md_file = output_dir / f"{task_id}_report.md"
        md_file.write_text(markdown, encoding="utf-8")
        print(f"📄 Markdown report: {md_file}")

    # Export JSON report
    json_data = report.get("json", {})
    if json_data:
        json_file = output_dir / f"{task_id}_report.json"
        json_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"📄 JSON report: {json_file}")

    # Export full task data
    full_file = output_dir / f"{task_id}_full.json"
    full_file.write_text(
        json.dumps(task_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"📄 Full task data: {full_file}")

    print(f"\n✅ Reports exported for task {task_id} (session: {session_id})")


def main() -> None:
    """Run test and export reports."""
    print("=" * 60)
    print("Review Test with Archives")
    print("=" * 60)

    # Test 1: With both archives (diff analysis)
    print("\n" + "=" * 60)
    print("Test 1: New + Old Archive (with diff analysis)")
    print("=" * 60)

    task1 = create_review_task(
        student_id="2001",
        assignment_id="TEST_HW_DIFF",
        new_submission_path="review_archives/new_submission.zip",
        previous_submission_path="review_archives/old_submission.zip",
    )

    task1_id = task1["task_id"]
    final1 = wait_for_task(task1_id, max_wait=300)

    # Test 2: Only new archive
    print("\n" + "=" * 60)
    print("Test 2: New Archive Only")
    print("=" * 60)

    task2 = create_review_task(
        student_id="2002",
        assignment_id="TEST_HW_NEW_ONLY",
        new_submission_path="review_archives/new_submission.zip",
    )

    task2_id = task2["task_id"]
    final2 = wait_for_task(task2_id, max_wait=300)

    # Export reports
    print("\n" + "=" * 60)
    print("Exporting Reports")
    print("=" * 60)

    output_dir = Path("review_reports")
    export_report(final1, output_dir)
    export_report(final2, output_dir)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Test 1 (with diff): {final1['status']}")
    print(f"Test 2 (new only): {final2['status']}")
    print(f"\nReports saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

