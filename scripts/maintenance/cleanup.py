#!/usr/bin/env python
"""Cleanup script for removing old data.

Features:
- Remove old experiment data (configurable age)
- Clean up temporary files
- Archive old logs
- Dry-run mode for safety

Usage:
    python -m scripts.maintenance.cleanup --days 30
    python -m scripts.maintenance.cleanup --dry-run
"""

import argparse
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.infrastructure.config.settings import Settings


def find_old_files(directory: Path, days: int) -> List[Path]:
    """Find files older than specified days.

    Args:
        directory: Directory to search
        days: Number of days

    Returns:
        List of old file paths
    """
    if not directory.exists():
        return []

    cutoff_time = time.time() - (days * 24 * 60 * 60)
    old_files = []

    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            old_files.append(file_path)

    return old_files


def cleanup_data(settings: Settings, days: int, dry_run: bool) -> None:
    """Clean up old experiment data.

    Args:
        settings: Application settings
        days: Files older than this will be removed
        dry_run: If True, only show what would be deleted
    """
    print(f"🧹 Cleanup Script - {'DRY RUN' if dry_run else 'LIVE MODE'}")
    print(f"   Removing files older than {days} days")

    storage_path = settings.storage_path
    if not storage_path.exists():
        print("❌ Storage path does not exist")
        return

    # Find old files
    old_files = find_old_files(storage_path, days)

    if not old_files:
        print("✅ No old files to clean up")
        return

    print(f"\n📋 Found {len(old_files)} old files:")

    for file_path in old_files[:10]:  # Show first 10
        age_days = (time.time() - file_path.stat().st_mtime) / (24 * 60 * 60)
        print(f"   - {file_path.name} ({age_days:.1f} days old)")

    if len(old_files) > 10:
        print(f"   ... and {len(old_files) - 10} more files")

    if not dry_run:
        # Create backup directory
        backup_dir = storage_path / "archive"
        backup_dir.mkdir(exist_ok=True)

        # Move files to archive
        moved = 0
        for file_path in old_files:
            try:
                rel_path = file_path.relative_to(storage_path)
                archive_path = backup_dir / rel_path
                archive_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.move(str(file_path), str(archive_path))
                moved += 1
            except Exception as e:
                print(f"⚠️  Failed to move {file_path}: {e}")

        print(f"\n✅ Archived {moved} files to {backup_dir}")
    else:
        print("\n🔍 Dry run - no files were moved")


def cleanup_tmp_files(tmp_dir: Path, dry_run: bool) -> None:
    """Clean up temporary files.

    Args:
        tmp_dir: Temporary directory
        dry_run: If True, only show what would be deleted
    """
    if not tmp_dir.exists():
        return

    temp_files = list(tmp_dir.rglob("*.tmp"))
    temp_files += list(tmp_dir.rglob("*.log"))

    if temp_files:
        print(f"\n📋 Found {len(temp_files)} temporary files")
        if not dry_run:
            for file_path in temp_files:
                try:
                    file_path.unlink()
                except Exception:
                    pass
            print(f"✅ Removed {len(temp_files)} temporary files")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Clean up old data")
    parser.add_argument(
        "--days", type=int, default=30, help="Remove files older than N days"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    args = parser.parse_args()

    settings = Settings.from_env()
    cleanup_data(settings, args.days, args.dry_run)

    # Clean up tmp files
    tmp_dir = Path("tmp")
    cleanup_tmp_files(tmp_dir, args.dry_run)


if __name__ == "__main__":
    main()


