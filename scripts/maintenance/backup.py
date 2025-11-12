#!/usr/bin/env python
"""Backup script for data and configuration.

Features:
- Backup JSON storage
- Backup configuration files
- Create timestamped backups
- Restore functionality

Usage:
    python -m scripts.maintenance.backup
    python -m scripts.maintenance.backup --restore backup_20240101.tar.gz
"""

import argparse
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.infrastructure.config.settings import Settings


def create_backup(settings: Settings, output_dir: Path) -> Path:
    """Create backup of data and configuration.

    Args:
        settings: Application settings
        output_dir: Directory for backups

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.tar.gz"
    backup_path = output_dir / backup_name

    output_dir.mkdir(parents=True, exist_ok=True)

    files_to_backup = [
        settings.get_agent_storage_path(),
        settings.get_experiment_storage_path(),
        Path("config/models.yaml"),
        Path("config/agents.yaml"),
    ]

    with tarfile.open(backup_path, "w:gz") as tar:
        for file_path in files_to_backup:
            if file_path.exists():
                tar.add(file_path, arcname=file_path.name)
                print(f"📦 Added {file_path}")

    print(f"\n✅ Backup created: {backup_path}")
    print(f"   Size: {backup_path.stat().st_size / 1024:.2f} KB")

    return backup_path


def restore_backup(backup_path: Path, restore_dir: Path) -> None:
    """Restore from backup.

    Args:
        backup_path: Path to backup file
        restore_dir: Directory to restore to
    """
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return

    print(f"📥 Restoring from {backup_path}")

    restore_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall(restore_dir)

    print(f"✅ Files extracted to {restore_dir}")


def list_backups(backup_dir: Path) -> None:
    """List available backups.

    Args:
        backup_dir: Directory with backups
    """
    if not backup_dir.exists():
        print("❌ No backups found")
        return

    backups = sorted(backup_dir.glob("backup_*.tar.gz"), reverse=True)

    if not backups:
        print("❌ No backups found")
        return

    print(f"\n📋 Available backups ({len(backups)}):\n")
    for backup in backups[:10]:
        size = backup.stat().st_size / 1024
        print(f"   {backup.name} ({size:.2f} KB)")
    print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Backup and restore data")
    parser.add_argument("--restore", type=str, help="Path to backup to restore")
    parser.add_argument("--list", action="store_true", help="List backups")
    args = parser.parse_args()

    settings = Settings.from_env()
    backup_dir = Path("backups")

    if args.list:
        list_backups(backup_dir)
    elif args.restore:
        restore_backup(Path(args.restore), Path("restored"))
    else:
        create_backup(settings, backup_dir)


if __name__ == "__main__":
    main()
