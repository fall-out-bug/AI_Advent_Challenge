#!/usr/bin/env python
"""Data export script.

Features:
- Export all experiments to CSV
- Export metrics history
- Export configuration snapshot
- Generate summary report

Usage:
    python -m scripts.maintenance.export_data --output exports/
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.infrastructure.config.settings import Settings
from src.infrastructure.debug.debug_utils import DebugUtils
from src.infrastructure.monitoring.exporter import MetricsExporter
from src.infrastructure.monitoring.metrics import get_metrics


def export_experiments(settings: Settings, output_dir: Path) -> None:
    """Export all experiments to CSV.

    Args:
        settings: Application settings
        output_dir: Output directory
    """
    storage_path = settings.get_experiment_storage_path()

    if not storage_path.exists():
        print("⚠️  No experiments to export")
        return

    with storage_path.open() as f:
        experiments = json.load(f)

    if not experiments:
        print("⚠️  No experiments found")
        return

    # Convert to CSV
    csv_path = output_dir / "experiments.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "status", "timestamp"])
        writer.writeheader()

        for exp in experiments.get("experiments", []):
            writer.writerow({
                "id": exp.get("id", ""),
                "name": exp.get("name", ""),
                "status": exp.get("status", ""),
                "timestamp": exp.get("timestamp", "")
            })

    print(f"✅ Exported {len(experiments.get('experiments', []))} experiments to {csv_path}")


def export_agents(settings: Settings, output_dir: Path) -> None:
    """Export all agents to CSV.

    Args:
        settings: Application settings
        output_dir: Output directory
    """
    storage_path = settings.get_agent_storage_path()

    if not storage_path.exists():
        print("⚠️  No agents to export")
        return

    with storage_path.open() as f:
        agents = json.load(f)

    if not agents:
        print("⚠️  No agents found")
        return

    csv_path = output_dir / "agents.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "status", "tasks_count"])
        writer.writeheader()

        for agent in agents.get("agents", []):
            writer.writerow({
                "name": agent.get("name", ""),
                "status": agent.get("status", ""),
                "tasks_count": agent.get("tasks_count", 0)
            })

    print(f"✅ Exported agents to {csv_path}")


def export_metrics(output_dir: Path) -> None:
    """Export metrics to multiple formats.

    Args:
        output_dir: Output directory
    """
    metrics = get_metrics()
    exporter = MetricsExporter(metrics)

    # Export to JSON
    json_path = output_dir / "metrics.json"
    exporter.export_to_json(str(json_path), include_history=True)
    print(f"✅ Exported metrics to {json_path}")

    # Export to CSV
    csv_path = output_dir / "metrics.csv"
    exporter.export_to_csv(str(csv_path))
    print(f"✅ Exported metrics to {csv_path}")

    # Export to Markdown
    md_path = output_dir / "metrics_report.md"
    exporter.export_to_markdown(str(md_path), include_history=True)
    print(f"✅ Exported metrics report to {md_path}")


def generate_summary(output_dir: Path) -> None:
    """Generate summary report.

    Args:
        output_dir: Output directory
    """
    settings = Settings.from_env()
    debug = DebugUtils(settings)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "configuration": debug.dump_config(),
        "metrics": get_metrics().get_metrics(),
        "statistics": {
            "experiments": _count_items(settings.get_experiment_storage_path()),
            "agents": _count_items(settings.get_agent_storage_path())
        }
    }

    summary_path = output_dir / "summary.json"
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Generated summary report: {summary_path}")


def _count_items(storage_path: Path) -> int:
    """Count items in storage file.

    Args:
        storage_path: Path to storage file

    Returns:
        Number of items
    """
    if not storage_path.exists():
        return 0

    try:
        with storage_path.open() as f:
            data = json.load(f)
            return len(data.get("items", []))
    except Exception:
        return 0


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Export data")
    parser.add_argument(
        "--output",
        type=str,
        default="exports",
        help="Output directory"
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("📤 Data Export Script")
    print(f"   Output directory: {output_dir}\n")

    export_experiments(settings, output_dir)
    export_agents(settings, output_dir)
    export_metrics(output_dir)
    generate_summary(output_dir)

    print("\n✅ Export complete")


if __name__ == "__main__":
    main()
