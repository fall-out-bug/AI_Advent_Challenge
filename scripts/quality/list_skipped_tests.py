#!/usr/bin/env python3
"""Collect and report pytest skip markers for reviewer quality tracking."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import pytest


@dataclass
class SkipRecord:
    """Structured representation of a skipped test."""

    nodeid: str
    marker: str
    active: str
    reason: str
    condition: str
    file: str


class SkipCollector:
    """Pytest plugin that captures skip-related markers during collection."""

    def __init__(self) -> None:
        self._records: list[SkipRecord] = []
        self._seen: set[tuple[str, str, str]] = set()

    def pytest_collection_modifyitems(  # type: ignore[override]
        self,
        session: pytest.Session,
        config: pytest.Config,
        items: list[pytest.Item],
    ) -> None:
        for item in items:
            for record in self._extract_records(item):
                key = (record.nodeid, record.marker, record.reason)
                if key not in self._seen:
                    self._seen.add(key)
                    self._records.append(record)

    def records(self) -> list[SkipRecord]:
        """Return collected skip records."""
        return self._records

    @staticmethod
    def _extract_records(item: pytest.Item) -> Iterable[SkipRecord]:
        file_path = Path(item.location[0]).as_posix()
        nodeid = item.nodeid

        for marker in item.iter_markers(name="skip"):
            yield SkipRecord(
                nodeid=nodeid,
                marker="skip",
                active="yes",
                reason=_extract_reason(marker),
                condition="",
                file=file_path,
            )

        for marker in item.iter_markers(name="skipif"):
            condition_value = _extract_condition(marker)
            active = _resolve_skipif_state(condition_value)
            yield SkipRecord(
                nodeid=nodeid,
                marker="skipif",
                active=active,
                reason=_extract_reason(marker),
                condition=_to_string(condition_value),
                file=file_path,
            )


def _extract_reason(marker: pytest.Mark) -> str:
    reason = marker.kwargs.get("reason")
    if reason is not None:
        return _to_string(reason)
    for value in reversed(marker.args):
        if isinstance(value, str):
            return value
    return ""


def _extract_condition(marker: pytest.Mark) -> Any:
    if "condition" in marker.kwargs:
        return marker.kwargs["condition"]
    if marker.args:
        # Skipif stores condition as the first positional argument by default.
        return marker.args[0]
    return None


def _resolve_skipif_state(condition: Any) -> str:
    if isinstance(condition, bool):
        return "yes" if condition else "no"
    return "unknown"


def _to_string(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:  # pragma: no cover - defensive fallback
        return repr(value)


def _escape_markdown(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", "<br>")
        .strip()
    )


def format_markdown(records: list[SkipRecord]) -> str:
    header = (
        "| NodeID | Marker | Active | Reason | Condition | File |\n"
        "|--------|--------|--------|--------|-----------|------|"
    )
    rows = [
        "| {node} | `{marker}` | {active} | {reason} | {condition} | `{file}` |".format(
            node=_escape_markdown(record.nodeid),
            marker=record.marker,
            active=record.active,
            reason=_escape_markdown(record.reason),
            condition=_escape_markdown(record.condition),
            file=_escape_markdown(record.file),
        )
        for record in sorted(records, key=lambda r: r.nodeid)
    ]
    content = [header, *rows] if rows else [header, "| _No skipped tests found_ |"]
    return "\n".join(content)


def format_csv(records: list[SkipRecord], output: Path | None) -> None:
    fieldnames = ["nodeid", "marker", "active", "reason", "condition", "file"]
    target = sys.stdout if output is None else output.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(target, fieldnames=fieldnames)
    writer.writeheader()
    for record in sorted(records, key=lambda r: r.nodeid):
        writer.writerow(asdict(record))
    if output is not None:
        target.close()


def format_json(records: list[SkipRecord]) -> str:
    data = [asdict(record) for record in sorted(records, key=lambda r: r.nodeid)]
    return json.dumps(data, ensure_ascii=False, indent=2)


def run_pytest(paths: list[str], extra_args: list[str]) -> list[SkipRecord]:
    collector = SkipCollector()
    args = ["--collect-only", "--disable-warnings", "--maxfail=1", *extra_args, *paths]
    exit_code = pytest.main(args, plugins=[collector])
    if exit_code != 0:
        raise RuntimeError(f"pytest collection failed with exit code {exit_code}")
    return collector.records()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate inventory of skipped pytest tests."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["tests"],
        help="Test paths or files to collect (default: tests)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output file path. Defaults to stdout.",
    )
    parser.add_argument(
        "-a",
        "--pytest-args",
        nargs="*",
        default=[],
        help="Additional arguments forwarded to pytest.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        records = run_pytest(args.paths, args.pytest_args)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        output_text = format_markdown(records)
        if args.output:
            args.output.write_text(output_text, encoding="utf-8")
        else:
            print(output_text)
    elif args.format == "json":
        output_text = format_json(records)
        if args.output:
            args.output.write_text(output_text, encoding="utf-8")
        else:
            print(output_text)
    else:
        format_csv(records, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

