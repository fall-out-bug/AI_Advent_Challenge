"""Formatting utilities for backoffice CLI output."""

from __future__ import annotations

import enum
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, List

from rich.console import Console
from rich.table import Table


class OutputFormat(str, enum.Enum):
    """Supported output formats."""

    TABLE = "table"
    JSON = "json"


def format_output(data: Any, format_type: OutputFormat | str) -> str:
    """Format payload according to the chosen output format.

    Args:
        data: Arbitrary payload to display in CLI.
        format_type: Desired output format (`table` or `json`).

    Returns:
        Rendered string representation suitable for stdout.
    """
    resolved_format = (
        format_type if isinstance(format_type, OutputFormat) else OutputFormat(format_type)
    )

    if resolved_format is OutputFormat.JSON:
        return _render_json(data)

    return _render_table(data)


def _render_json(data: Any) -> str:
    """Render payload as pretty-printed JSON."""
    return json.dumps(data, default=_stringify, ensure_ascii=False, indent=2)


def _render_table(data: Any) -> str:
    """Render payload as a Rich table."""
    rows = _normalise_rows(data)
    if not rows:
        return ""

    columns = _collect_columns(rows)
    table = Table(show_header=True, header_style="bold white")
    for column in columns:
        table.add_column(str(column))

    for row in rows:
        table.add_row(*(_stringify(row.get(column, "")) for column in columns))

    console = Console(width=120, record=True)
    console.print(table)
    return console.export_text(clear=True).rstrip()


def _normalise_rows(data: Any) -> list[dict[str, Any]]:
    """Normalise arbitrary payload into a list of dictionaries."""
    if _is_sequence_of_rows(data):
        return [_coerce_row(item) for item in data]

    if isinstance(data, Mapping) or is_dataclass(data):
        return [_coerce_row(data)]

    if data is None:
        return []

    return [{"value": data}]


def _is_sequence_of_rows(data: Any) -> bool:
    """Check if payload behaves as a sequence of potential rows."""
    return isinstance(data, Sequence) and not isinstance(data, (bytes, str))


def _coerce_row(item: Any) -> dict[str, Any]:
    """Coerce item into a dictionary row."""
    if isinstance(item, Mapping):
        return dict(item)

    if is_dataclass(item):
        return asdict(item)

    return {"value": item}


def _collect_columns(rows: Iterable[Mapping[str, Any]]) -> List[str]:
    """Collect ordered set of column names from rows."""
    seen: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.append(str(key))
    return seen or ["value"]


def _stringify(value: Any) -> str:
    """Convert value to string for display."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=False)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, str)):
        return ", ".join(_stringify(item) for item in value)
    return str(value)

